"""3D magnetostatic model of the Ledex solenoid and a washer stack (NGSolve; throwaway venv, Mac).

The calibrated 2D FEMM model (ledex_washer.lua, results/calibration/best_params.json) is axisymmetric,
so it cannot represent a washer stack that runs ACROSS the solenoid axis. This script rebuilds the
same device in 3D (same geometry, same fitted parameters, same 1010 B-H curve) and computes the pull
on the target for either orientation:

    axial   stack along the solenoid axis (what the 2D model does; used to check 3D against FEMM)
    across  stack perpendicular to the axis, centred on it, the tip facing the washer rims

Setup (one time):  python3 -m venv /tmp/ngenv && /tmp/ngenv/bin/pip install ngsolve numpy scipy
Run:               /tmp/ngenv/bin/python fea3d.py check         # axial stack vs FEMM
                   /tmp/ngenv/bin/python fea3d.py across        # perpendicular stacks, writes results/fea3d.csv

Method: A-formulation (H(curl), order 2, no gradients), quarter model (the field is tangent to the two
mirror planes and to the outer box, so A x n = 0 on all of them), Picard iteration on the element-wise
reluctivity of the steel, force from the Maxwell stress tensor integrated as a volume integral over a
smooth shell around the target (F_i = -int T_ij d_j(phi) dV), multiplied by 4 for the quarter.
Forces in g-force (1 g = 9.81 mN), z positive toward the solenoid body.
"""
import json
import math
import os
import sys
import time

import numpy as np
from ngsolve import *
from netgen.occ import *

HERE = os.path.dirname(os.path.abspath(__file__))
MU0 = 4e-7 * math.pi * 1e3           # T mm / A (lengths in mm, H in A/mm, B in T)
TURNS = 1491

# published geometry (mm), as in ledex_washer.lua
PROTRUDE, PMASS, RP, RO, LEN, LBOSS, RBOSS, RTIP = 23.81, 20.1, 3.91, 9.78, 39.37, 9.52, 6.6, 1.0
SLOTR, SLOTD, BOB = 2.43, 9.5, 0.5
# 1010 steel B-H table (FEMM library)
BH_B = [0, 0.211862, 0.265665, 0.332377, 0.414377, 0.513811, 0.631899, 0.767784, 0.917018,
        1.070353, 1.214255, 1.334637, 1.422981, 1.480634, 1.517214, 1.544515, 1.571296, 1.602049,
        1.638404, 1.68049, 1.727311, 1.776659, 1.825401, 1.870557, 1.910809, 1.947222, 1.982328,
        2.018252, 2.055398, 2.092545, 2.128095, 2.161612, 2.194644, 2.230339, 2.272386, 2.324282,
        2.389356, 2.471238]
BH_H = [0, 79.577472, 100.182101, 126.121793, 158.77793, 199.889571, 251.646061, 316.80362,
        398.832128, 502.099901, 632.106325, 795.774715, 1001.821011, 1261.217929, 1587.779301,
        1998.89571, 2516.460605, 3168.036204, 3988.321282, 5020.999013, 6321.06325, 7957.747155,
        10018.210114, 12612.179293, 15877.79301, 19988.957103, 25164.606052, 31680.362037,
        39883.212823, 50209.990127, 63210.632497, 79577.471546, 100182.101136, 126121.792926,
        158777.930096, 199889.57103, 251646.060522, 316803.62037]
BH_B, BH_H = np.array(BH_B), np.array(BH_H)


def fitted():
    with open(os.path.join(HERE, "results", "calibration", "best_params.json")) as f:
        return json.load(f)["params"]


def nu_table(bscale):
    """Reluctivity H/B (A/(T mm) -> use H in A/mm) on the B grid of the (scaled) curve."""
    b = BH_B * bscale
    h = BH_H * 1e-3                    # A/mm
    nu = np.empty_like(b)
    nu[1:] = h[1:] / b[1:]
    nu[0] = nu[1]
    return b, h, nu


def reluctivity(b, tab):
    """Secant reluctivity (A/(T mm)) at flux density b (T), linear in H(B) between table points."""
    bt, ht, _ = tab
    h = np.interp(b, bt, ht)
    over = b > bt[-1]                  # beyond the table: slope of vacuum
    h = np.where(over, ht[-1] + (b - bt[-1]) / MU0, h)
    return h / np.maximum(b, 1e-9)


def prof(pts, ang=90):
    """Solid of revolution (quarter by default: x >= 0, y >= 0) from an (r, z) polygon."""
    v = [Pnt(r, 0, z) for r, z in pts]
    w = Wire([Segment(v[i], v[(i + 1) % len(v)]) for i in range(len(v))])
    return Face(w).Revolve(Axis(Pnt(0, 0, 0), Z), ang)


class Model:
    def __init__(self, p, kind, n_washers, gap, amps, rbox=62.0, zlo=-62.0, zhi=80.0, wri=1.6, wro=4.5,
                 maxh_tip=0.45, maxh_air=9.0, order=2, maxh_pl=0.7):
        self.p, self.kind, self.n, self.gap, self.amps = p, kind, n_washers, gap, amps
        self.order = order
        seat, clr, tpl, wall, conea = p["SEAT"], p["CLR"], p["TPL"], p["WALL"], p["CONEA"]
        rb, rki = RP + clr, RO - wall
        rci, rco = rb + BOB, rki - 0.1
        conel = (RP - RTIP) / math.tan(math.radians(conea))
        vcone = math.pi / 3 * conel * (RP * RP + RP * RTIP + RTIP * RTIP)
        vslot = 2.5 * 2 * math.sqrt(RP * RP - 1.5625) * 9.5
        vhole = math.pi * 1.25 ** 2 * (2 * RP - 2.5)
        lcyl = (PMASS / 7.85e-3 - vcone + vslot + vhole) / (math.pi * RP * RP)
        zt = -PROTRUDE
        zcone = zt + lcyl
        zapex = zcone + conel
        zs, za = zcone + seat, zapex + seat
        ht = 0.8 * n_washers
        # the same profiles as ledex_washer.lua, revolved over 90 degrees
        steel1 = prof([(0, za), (RTIP, za), (RP, zs), (rb, zs), (rb, LEN - tpl), (rki, LEN - tpl), (rki, tpl),
                       (RO, tpl), (RO, LEN), (0, LEN)])
        steel2 = prof([(rb, -LBOSS), (RBOSS, -LBOSS), (RBOSS, 0), (RO, 0), (RO, tpl), (rki, tpl), (rb, tpl)])
        coil = prof([(rci, tpl + 0.1), (rco, tpl + 0.1), (rco, LEN - tpl - 0.1), (rci, LEN - tpl - 0.1)])
        plunger = prof([(0, zt + SLOTD), (SLOTR, zt + SLOTD), (SLOTR, zt), (RP, zt), (RP, zcone),
                        (RTIP, zapex), (0, zapex)])
        steel1.mat("steel"); steel2.mat("steel"); coil.mat("coil"); plunger.mat("plunger")
        solids = [steel1, steel2, coil, plunger]
        if n_washers:
            if kind == "axial":
                w2 = zt - gap
                target = prof([(wri, w2 - ht), (wro, w2 - ht), (wro, w2), (wri, w2)])
                self.tgeo = ("axial", w2 - ht / 2, ht / 2, wro)
            else:   # across: axis along y, centred on the solenoid axis, rim facing the tip
                zc = zt - gap - wro
                c = Cylinder(Pnt(0, 0, zc), Y, r=wro, h=ht / 2) - Cylinder(Pnt(0, -1, zc), Y, r=wri, h=ht / 2 + 2)
                c = c.Rotate(Axis(Pnt(0, 0, zc), Y), 45)         # keep the cylinder seam off the mirror plane
                target = c * Box(Pnt(0, 0, zc - wro - 1), Pnt(wro + 1, ht / 2 + 1, zc + wro + 1))
                self.tgeo = ("across", zc, ht / 2, wro)
            target.mat("target")
            solids.append(target)
        domain = prof([(0, zlo), (rbox, zlo), (rbox, zhi), (0, zhi)])
        air = domain
        for s_ in solids:
            air = air - s_
        air.mat("air")
        # mesh sizes: fine near the tip and the target, coarse far away
        plunger.maxh = maxh_pl
        steel1.maxh = steel2.maxh = 2.0
        coil.maxh = 3.0
        if n_washers:
            target.maxh = maxh_tip
        pieces = solids + [air]
        for q in pieces:      # mirror planes (x = 0, y = 0) and the far boundary: B tangent, A x n = 0
            for f in q.faces:
                c = f.center
                on_plane = abs(c[0]) < 1e-6 or abs(c[1]) < 1e-6
                far = math.hypot(c[0], c[1]) > rbox - 0.5 and abs(c[2] - 0.5 * (zlo + zhi)) < 0.5 * (zhi - zlo)
                end = abs(c[2] - zlo) < 1e-6 or abs(c[2] - zhi) < 1e-6
                f.name = "outer" if (on_plane or far or end) else "inner"
        self.mesh = Mesh(OCCGeometry(Glue(pieces)).GenerateMesh(maxh=maxh_air, grading=0.25))
        self.rb, self.tpl, self.zt = rb, tpl, zt

    def solve(self, tol=1e-3, maxit=40, verbose=True):
        mesh = self.mesh
        p = self.p
        # all boundary faces of the quarter are tangent to B (mirror planes, far box): A x n = 0
        fes = HCurl(mesh, order=self.order, dirichlet="outer", nograds=True)
        u, v = fes.TnT()
        l2 = L2(mesh, order=0)
        nu_gf = GridFunction(l2)
        nu0 = 1.0 / MU0
        mats = [el.mat for el in mesh.Elements(VOL)]
        is_sol = np.array([m in ("steel", "plunger") for m in mats])
        is_tgt = np.array([m == "target" for m in mats])
        tab_s, tab_t = nu_table(p["BSCALE"]), nu_table(1.0)
        arr = np.full(len(mats), nu0)
        arr[is_sol | is_tgt] = reluctivity(0.05, tab_s)       # start from a low-field guess
        nu_gf.vec.FV().NumPy()[:] = arr
        # coil current density: turns * I / cross-section, azimuthal
        rci, rco = self.rb + BOB, RO - self.p["WALL"] - 0.1
        area = (rco - rci) * (LEN - 2 * self.tpl - 0.2)
        jmag = TURNS * self.amps / area                        # A/mm^2
        rr = sqrt(x * x + y * y) + 1e-12
        J = CoefficientFunction((-y / rr, x / rr, 0)) * jmag
        jcf = mesh.MaterialCF({"coil": J}, default=CoefficientFunction((0, 0, 0)))
        a = BilinearForm(fes)
        a += nu_gf * curl(u) * curl(v) * dx
        a += 1e-6 * nu0 * u * v * dx          # fixes the gradient kernel left at order 2
        f = LinearForm(fes)
        f += jcf * v * dx("coil")
        gfu = GridFunction(fes)
        bnorm = sqrt(curl(gfu) * curl(gfu))
        vol = Integrate(CoefficientFunction(1), mesh, VOL, element_wise=True).NumPy()
        prev = None
        for it in range(maxit):
            a.Assemble()
            f.Assemble()
            gfu.vec.data = a.mat.Inverse(fes.FreeDofs(), inverse="sparsecholesky") * f.vec
            bavg = Integrate(bnorm, mesh, VOL, element_wise=True).NumPy() / vol
            new = arr.copy()
            new[is_sol] = reluctivity(bavg[is_sol], tab_s)
            new[is_tgt] = reluctivity(bavg[is_tgt], tab_t)
            rel = 0.3
            arr = np.exp(rel * np.log(new) + (1 - rel) * np.log(arr))
            arr[~(is_sol | is_tgt)] = nu0
            nu_gf.vec.FV().NumPy()[:] = arr
            fz = self.force(gfu)
            if verbose:
                print("  it {:2d}  Fz = {:.4f} g  (max B steel {:.2f} T)".format(it, fz, bavg[is_sol].max()), flush=True)
            if prev is not None and abs(fz - prev) < tol * abs(fz):
                break
            prev = fz
        self.gfu = gfu
        return fz

    def force(self, gfu):
        """Pull on the target toward the solenoid (g-force), Maxwell stress over a smooth shell."""
        if not self.n:
            return 0.0
        mesh = self.mesh
        kind, zc, h, ro = self.tgeo
        d1, d2 = 0.15 * self.gap, 0.75 * self.gap
        if kind == "axial":
            rho = sqrt(x * x + y * y)
            ax = IfPos(rho - ro, rho - ro, 0)
            az = IfPos(sqrt((z - zc) * (z - zc) + 1e-12) - h, sqrt((z - zc) * (z - zc) + 1e-12) - h, 0)
        else:
            rho = sqrt(x * x + (z - zc) * (z - zc))
            ax = IfPos(rho - ro, rho - ro, 0)
            az = IfPos(y - h, y - h, 0)
        dist = sqrt(ax * ax + az * az)
        t = IfPos(dist - d1, IfPos(d2 - dist, (dist - d1) / (d2 - d1), 1), 0)
        phi_cf = 1 - t * t * (3 - 2 * t)
        h1 = H1(mesh, order=2)
        phi = GridFunction(h1)
        phi.Set(phi_cf)
        B = curl(gfu)
        g = grad(phi)
        bz = B[2]
        bg = B * g
        tz = (bz * bg - 0.5 * (B * B) * g[2]) / MU0           # T_zj d_j(phi); B^2/mu0 in 1e-3 N/mm^2
        fz = -Integrate(tz, mesh, VOL, order=6)               # x 1e-3 gives N
        return float(fz) * 1e-3 * 4 / 9.81e-3                  # quarter model x4, N -> g-force


def run(kind, n, gap, amps, p=None, **kw):
    p = p or fitted()
    t0 = time.time()
    m = Model(p, kind, n, gap, amps, **kw)
    ne = len(list(m.mesh.Elements(VOL)))
    fz = m.solve()
    print("{} n={} gap={} I={}: {:.4f} g  ({} tets, {:.0f} s)".format(kind, n, gap, amps, fz, ne, time.time() - t0), flush=True)
    return fz


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "across":
        out = os.path.join(HERE, "results", "fea3d.csv")
        done = set()
        if os.path.exists(out):
            done = set(tuple(l.split(",")[:4]) for l in open(out).read().splitlines()[1:])
        else:
            open(out, "w").write("kind,n_washers,gap_mm,current_A,force_g\n")
        for kind in ("across", "axial"):
            for n in (1, 5, 10, 20):
                for gap in (1.0, 2.0, 3.0):
                    for I in (0.074, 0.31, 0.58):
                        key = (kind, str(n), "%g" % gap, "%g" % I)
                        if key in done:
                            continue
                        f = run(kind, n, gap, I)
                        open(out, "a").write("%s,%d,%g,%g,%.4f\n" % (kind, n, gap, I, f))
    if mode == "check":
        run("axial", 5, 2.0, 0.31)
