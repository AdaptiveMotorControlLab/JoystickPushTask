"""Interactive rig explorer and true-section figures of the joystick, constrainer, Ledex holder and both magnet options.

    python rig_explorer.py   # figures/rig/rig_explorer.html (three.js + Plotly from CDNs; open in a browser),
                             # figures/rig/side_view.png (section at Y = 0), figures/rig/assembly_3d.png

The explorer embeds the measured CAD (joystick holder, component, constrainer, shaft, cube), the adjustable Ledex
holder (mechanical/ledex-holder-adjustable), the link parts and the force tables, and recomputes in the
browser: lever tilt about the pivot, washer gap and offset or plunger stroke, the magnet resistance at the cube,
the centring spring, plunger friction, feasibility and a live design map. The browser model is a port of
rig_forces.py / plunger_link.py; `main()` checks it against them with node (if installed) before writing.
"""
import base64
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import plunger_link as pl
import rig_forces as rf
import rig_geometry as rg
from plot_results import COMMAND_V, HERE, save

OUT_FIG = rf.OUT_FIG
HOLDER_DIR = os.path.join(rg.CAD, "ledex-holder-adjustable")
REF_DIR = os.path.join(rg.CAD, "ledex-195224-model")
LX = rg.LEDEX
NUT_R = 12.7                     # M14 thin nut, 22 mm across flats (corner radius; assumed, the nut is not drawn)
PIN_LEN = 10.0
CHEEK_Y = 2.3                    # side view cuts the plunger through one cheek of its tip slot (slot is +-1.25)
PIVOT_RANGE = (rg.PIVOT_DEPTHS[0], rg.PIVOT_DEPTHS[-1])

# name, source, frame, colour, opacity
MESHES = [
    ("joystick holder", "holder", "static", "#9e9e9e", 1.0),
    ("joystick component", "component", "static", "#454545", 1.0),
    ("1D constrainer (window revision)", "constrainer", "static", "#4f8fd6", 0.35),
    ("shaft", "shaft", "moving", "#e0b050", 1.0),
    ("cube handle", "cube", "moving", "#e07b39", 1.0),
    ("Ledex body (datasheet model)", "ledex_body", "ledex", "#5a5a5a", 0.55),
    ("plunger (datasheet model)", "ledex_plunger", "plunger", "#c8c8c8", 1.0),
    ("Ledex carriage", "ledex_holder_carriage", "ledex", "#f39c12", 1.0),
    ("Ledex upright", "ledex_holder_upright", "upright", "#27ae60", 1.0),
    ("Ledex base", "ledex_holder_base", "base", "#c0392b", 1.0),
    ("link collar", "link_collar", "collar", "#8e44ad", 1.0),
    ("link bar", "link_bar", "link", "#d4a017", 1.0),
]


def mesh(src):
    if src in rg.PARTS:
        return rg.part_mesh(src)
    if src.startswith("ledex_") and not src.startswith("ledex_holder"):
        return rg.read_stl(os.path.join(REF_DIR, src + ".stl"))
    return rg.read_stl(os.path.join(HOLDER_DIR, src + ".stl"))


def enc_i16(t):
    q = np.round(t.reshape(-1, 3) * 100).astype("<i2")
    return base64.b64encode(q.tobytes()).decode()


def enc_f32(a):
    return base64.b64encode(np.asarray(a, "<f4").tobytes()).decode()


# ---------------------------------------------------------------- data for the browser
def browser_data(wf, tab):
    G = dict(SHAFT_BASE=rg.SHAFT_BASE, HANDLE_Z=rg.HANDLE_Z, FACE=rg.FACE, ATTACH_R=rg.ATTACH_R, LINK=rg.LINK,
             PIN_FROM_TIP=rg.PIN_FROM_TIP, PIN_D=rg.PIN_D, PIN_LEN=PIN_LEN, protrude=LX["protrude"], plunger_r=LX["plunger_r"], case_r=LX["case_r"],
             case_len=LX["case_len"], boss_r=LX["boss_r"], boss_len=LX["boss_len"], NUT_T=rg.NUT_T, NUT_R=NUT_R,
             PLATE_T=rg.PLATE_T, WASHER_RO=rg.WASHER_RO, WASHER_RI=rg.WASHER_RI, WASHER_T=rg.WASHER_T,
             N_WASHERS=rg.N_WASHERS, WASHER_SEAT=rg.WASHER_SEAT, TOWER_Z=rf.TOWER_Z, SLOT_HOME_X=rg.SLOT_HOME_X,
             SLOT_FAR_X=rg.SLOT_FAR_X, SLOT_Z=rg.SLOT_Z, ARCH_HALF_W=rg.ARCH_HALF_W, ARCH_BOTTOM=rg.ARCH_BOTTOM,
             WINDOW_TOP=rg.WINDOW_TOP, CON_OUTER=rg.CON_OUTER, CLEARANCE=rg.CLEARANCE,
             LINK_Z_MIN=rg.LINK_Z_MIN, LINK_Z_MAX=rg.LINK_Z_MAX, H_MIN=rf.H_RANGE[0], H_MAX=rf.H_RANGE[1],
             CONTACT_MIN=rf.CONTACT_MIN, S_MIN=rf.STROKE_RANGE[0], S_MAX=rf.STROKE_RANGE[1], S_RET=round(59.7 - LX["protrude"] - 15.0, 2), MAX_PUSH=20.0,
             COMP_TOP=rg.COMP_TOP, PIVOT=rg.PIVOT_DEPTH, PIVOT_MIN=PIVOT_RANGE[0], PIVOT_MAX=PIVOT_RANGE[1], g=pl.G,
             PLUNGER_G=pl.PLUNGER_G, PIN_FRICTION_GF=pl.PIN_FRICTION_GF)
    a, v = np.array(sorted(COMMAND_V.items())).T
    gaps = np.round(np.arange(0.05, 25.0001, 0.05), 3)
    offs = np.round(np.arange(0.0, 30.0001, 0.25), 3)
    lf = np.log(wf(gaps[:, None], offs[None, :], 0.31))
    cur = sorted(tab)
    strokes = tab[cur[0]][0]
    assert all(np.allclose(tab[c][0], strokes) for c in cur)
    plf = np.array([np.log(tab[c][1]) for c in cur])
    rec = {k: dict(H=round(r["H"], 3), face=round(r["face"], 3)) for k, r in rf.REC.items()}
    mu = pl.MU[1]
    return dict(G=G, cmd=dict(volts=list(v), amps=list(a)),
                washer=dict(gaps=list(gaps), offs=list(offs), lf=enc_f32(lf.ravel()),
                            cur=list(wf.cur), rat=list(wf.rat)),
                plunger=dict(strokes=list(strokes), cur=cur, lf=enc_f32(plf.ravel())),
                rec=rec, spring=dict(k=0.2, mu=mu))


# ---------------------------------------------------------------- browser physics (also run by node in the check)
PHYS_JS = r"""
function makePhys(D, dec){
  const G = D.G, W = D.washer, P = D.plunger;
  const wlf = dec(W.lf), plf = dec(P.lf);
  const nG = W.gaps.length, nY = W.offs.length, nS = P.strokes.length;
  const lerp = (x, xs, ys) => {           // xs ascending, clamped
    if (x <= xs[0]) return ys[0];
    const n = xs.length - 1;
    if (x >= xs[n]) return ys[n];
    let lo = 0, hi = n;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] <= x) lo = m; else hi = m; }
    const w = (x - xs[lo]) / (xs[hi] - xs[lo]);
    return ys[lo] + w * (ys[hi] - ys[lo]);
  };
  function rotate(px, pz, dp, th){ const h = pz + dp;
    return [px * Math.cos(th) + h * Math.sin(th), -dp - px * Math.sin(th) + h * Math.cos(th)]; }
  function pushForTilt(th, dp){ return rotate(-G.FACE, G.HANDLE_Z, dp, th)[0] - rotate(-G.FACE, G.HANDLE_Z, dp, 0)[0]; }
  function tiltForPush(u, dp){ let lo = -10 * Math.PI / 180, hi = 35 * Math.PI / 180;
    for (let i = 0; i < 60; i++){ const m = 0.5 * (lo + hi); if (pushForTilt(m, dp) < u) lo = m; else hi = m; }
    return 0.5 * (lo + hi); }
  const stopPush = dp => pushForTilt(Math.asin(G.SLOT_HOME_X / (G.SLOT_Z + dp)), dp);
  const maxPush = dp => G.MAX_PUSH;                 // 20 mm at the cube (set in the viewer, not by the slot)
  const current = volts => volts <= 0 ? 0 : lerp(volts, D.cmd.volts, D.cmd.amps);
  function washerRatio(a){ const la = Math.log(Math.max(a, 1e-4)), c = W.cur, r = W.rat;
    if (la < c[0]) return Math.exp(r[0] + (r[1] - r[0]) / (c[1] - c[0]) * (la - c[0]));
    return Math.exp(lerp(la, c, r)); }
  function washerPull(gap, yoff, a){          // gf along the plunger axis
    if (a <= 0) return 0;
    const g = Math.min(Math.max(gap, W.gaps[0]), W.gaps[nG - 1]), y = Math.min(Math.abs(yoff), W.offs[nY - 1]);
    const fi = (g - W.gaps[0]) / (W.gaps[1] - W.gaps[0]), fj = y / (W.offs[1] - W.offs[0]);
    const i = Math.min(Math.floor(fi), nG - 2), j = Math.min(Math.floor(fj), nY - 2), u = fi - i, v = fj - j;
    const L = (ii, jj) => wlf[ii * nY + jj];
    const l = (1 - u) * (1 - v) * L(i, j) + u * (1 - v) * L(i + 1, j) + (1 - u) * v * L(i, j + 1) + u * v * L(i + 1, j + 1);
    return Math.exp(l) * washerRatio(a); }
  function plungerPull(a, s){                // N
    if (a <= 0) return 0;
    const c = P.cur, ls = Math.log(Math.max(s, P.strokes[0]));
    const lsx = P.strokes.map(Math.log);
    let i = 0; while (i < c.length - 2 && c[i + 1] < a) i++;
    const row = k => { const r = Array.from(plf.subarray(k * nS, (k + 1) * nS));
      return ls <= lsx[nS - 1] ? lerp(ls, lsx, r)      // beyond the table: extend the end slope in log-log
        : r[nS - 1] + (r[nS - 1] - r[nS - 2]) / (lsx[nS - 1] - lsx[nS - 2]) * (ls - lsx[nS - 1]); };
    const w = (Math.log(a) - Math.log(c[i])) / (Math.log(c[i + 1]) - Math.log(c[i]));
    return Math.exp(row(i) + w * (row(i + 1) - row(i))); }
  function washers(u, H, face, a, dp){
    const th = tiltForPush(u, dp), [xt, zt] = rotate(0, G.TOWER_Z, dp, th);
    const tip = face + G.protrude, gap = xt - G.WASHER_RO - tip, yoff = zt + G.SHAFT_BASE - H;
    const cz = rotate(-G.FACE, G.HANDLE_Z, dp, th)[1];
    const pull = washerPull(gap, yoff, a);
    return {th, gap, yoff, tip, pull, F: pull * (zt + dp) / (cz + dp), ratio: (zt + dp) / (cz + dp), fric: 0}; }
  function link(u, H, face, a, dp, mu){
    const za = H - G.SHAFT_BASE, pin0 = -G.ATTACH_R - G.LINK, tip0 = pin0 + G.PIN_FROM_TIP;
    const s0 = tip0 - G.protrude - face, th = tiltForPush(u, dp);
    const [sx, sz] = rotate(-G.ATTACH_R, za, dp, th);
    const px = sx - Math.sqrt(G.LINK * G.LINK - (sz - za) * (sz - za));
    const stroke = s0 + px - pin0, tx = (px - sx) / G.LINK, tz = (za - sz) / G.LINK;
    const torque = (sx * tz - (sz + dp) * tx) / Math.abs(tx), cz = rotate(-G.FACE, G.HANDLE_Z, dp, th)[1];
    const ratio = torque / (cz + dp), pullN = plungerPull(a, Math.max(stroke, 0.5));
    const fricN = (mu === undefined ? 0 : mu) * G.PLUNGER_G * 1e-3 * G.g + G.PIN_FRICTION_GF * 1e-3 * G.g;
    return {th, za, s0, stroke, sx, sz, px, tip: px + G.PIN_FROM_TIP, ratio, pull: pullN / G.g * 1e3,
            F: pullN * ratio / G.g * 1e3, fric: fricN * ratio / G.g * 1e3,
            linkDeg: Math.asin((sz - za) / G.LINK) * 180 / Math.PI}; }
  function state(opt, u, H, face, a, dp, mu){ return opt === 'washers' ? washers(u, H, face, a, dp) : link(u, H, face, a, dp, mu); }
  function checks(opt, H, face, dp){
    const r = G.plunger_r + G.CLEARANCE;
    const out = [
      ['plunger through the window', r <= G.ARCH_HALF_W && H - r >= G.ARCH_BOTTOM && H + r <= G.WINDOW_TOP,
       `axis Z ${H.toFixed(1)} in ${(G.ARCH_BOTTOM + r).toFixed(1)}-${(G.WINDOW_TOP - r).toFixed(1)}`],
      ['nut clear of the constrainer', face + G.PLATE_T + G.NUT_T <= -G.CON_OUTER - G.CLEARANCE,
       `nut front X ${(face + G.PLATE_T + G.NUT_T).toFixed(1)} (wall ${(-G.CON_OUTER).toFixed(0)})`],
      ['holder height range', H >= G.H_MIN && H <= G.H_MAX, `${G.H_MIN}-${G.H_MAX} mm`]];
    const us = stopPush(dp);
    if (opt === 'washers'){
      const g = washers(us, H, face, 0.31, dp).gap;
      out.push(['no contact at the home stop', g >= G.CONTACT_MIN, `gap at the stop ${g.toFixed(2)} mm (min ${G.CONTACT_MIN.toFixed(1)})`]);
    } else {
      const za = H - G.SHAFT_BASE, lo = link(us, H, face, 0, dp).stroke, hi = link(G.MAX_PUSH, H, face, 0, dp).stroke;
      out.push(['collar on the straight shaft, plunger under the window top', za >= G.LINK_Z_MIN - 1e-9 && za <= G.LINK_Z_MAX + 1e-9,
                `link z ${za.toFixed(1)} in ${G.LINK_Z_MIN.toFixed(1)}-${G.LINK_Z_MAX.toFixed(1)}`]);
      out.push(['plunger stays in its bearing (stroke limit)', lo >= 0 && hi <= G.S_RET,
                `${lo.toFixed(2)}-${hi.toFixed(2)} mm of 0-${G.S_RET.toFixed(1)} (0 = seated)` + (hi > G.S_MAX ? ` (pull extrapolated beyond ${G.S_MAX})` : '') + (lo < G.S_MIN ? ` (below ${G.S_MIN} the pull is held at its ${G.S_MIN} mm value; seated it is higher)` : '')]);
    }
    return out; }
  const spring = (u, p0, k) => k * u;
  return {rotate, tiltForPush, pushForTilt, stopPush, maxPush, current, washerPull, plungerPull, washers, link, state,
          checks, spring};
}
if (typeof module !== 'undefined') module.exports = {makePhys};
"""


def js_check(data, wf, tab):
    """Compare the browser model with rig_forces at a spread of settings (needs node)."""
    node = shutil.which("node")
    if node is None:
        print("node not found: browser model not checked")
        return True
    cases = []
    for opt in ("washers", "link"):
        r = rf.REC[opt]
        for u in (rg.stop_push(rg.PIVOT_DEPTH), 0.0, 5.0, 15.0):
            for dH, dF in ((0, 0), (-1.5, -1.0), (-3.0, -2.5)):
                for a in (0.074, 0.18, 0.31, 0.58):
                    for dp in rg.PIVOT_DEPTHS:
                        H, face = r["H"] + dH, r["face"] + dF
                        if opt == "washers":
                            F = float(np.ravel(rf.washer_handle(wf, u, H, face, a, dp)[0])[0])
                        else:
                            F = float(rf.link_handle(tab, u, H, face, a, dp)[0][0])
                        cases.append([opt, u, H, face, a, dp, F])
    script = PHYS_JS + r"""
const D = JSON.parse(require('fs').readFileSync(process.argv[2]));
const dec = s => new Float32Array(new Uint8Array(Buffer.from(s, 'base64')).buffer);
const P = makePhys(D, dec);
let worst = 0;
for (const [opt, u, H, face, a, dp, F] of D.cases){
  const f = P.state(opt, u, H, face, a, dp).F, e = Math.abs(f / F - 1);
  if (e > worst) worst = e;
}
console.log(JSON.stringify({worst, n: D.cases.length, stop: P.stopPush(D.G.PIVOT), max: P.maxPush(D.G.PIVOT)}));
"""
    with tempfile.TemporaryDirectory() as tmp:
        js, dj = os.path.join(tmp, "check.js"), os.path.join(tmp, "data.json")
        open(js, "w").write(script)
        json.dump(dict(data, cases=cases), open(dj, "w"))
        out = json.loads(subprocess.run([node, js, dj], capture_output=True, text=True, check=True).stdout)
    ok = out["worst"] < 0.03 and abs(out["stop"] - rg.stop_push(rg.PIVOT_DEPTH)) < 1e-3 \
        and abs(out["max"] - 20.0) < 1e-3
    print("browser model vs rig_forces: worst %.2f %% over %d cases, stop %.3f, max push %.2f -> %s"
          % (100 * out["worst"], out["n"], out["stop"], out["max"], "OK" if ok else "MISMATCH"))
    return ok


HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>JoystickPushTask rig explorer</title>
<style>
body{margin:0;font-family:system-ui,sans-serif;font-size:13px;background:#f4f4f4;display:grid;
     grid-template-columns:340px 1fr 460px;height:100vh;overflow:hidden}
#ui{overflow-y:auto;padding:10px 14px;background:#fff;border-right:1px solid #ccc}
#view{position:relative}
#plots{overflow-y:auto;background:#fff;border-left:1px solid #ccc}
.row{display:grid;grid-template-columns:126px 1fr 64px;column-gap:10px;align-items:center;margin:3px 0}
.num{width:100%;box-sizing:border-box;text-align:right;font:inherit;font-variant-numeric:tabular-nums;border:1px solid #ccc;border-radius:3px;padding:1px 3px;background:#fafafa}
.row input[type=range]{width:100%}
h3{margin:12px 0 4px;font-size:13px;border-bottom:1px solid #ddd}
.ok{color:#1a7f37}.bad{color:#c62828;font-weight:600}
.sw{display:inline-block;width:10px;height:10px;margin-right:5px;border:1px solid #666}
small{color:#555}
table{border-collapse:collapse;width:100%}td{padding:1px 4px;vertical-align:top}td:last-child{text-align:right}
#hint{position:absolute;bottom:8px;left:10px;color:#555;font-size:12px;background:rgba(255,255,255,.8);padding:3px 6px}
button{font-size:12px}
.btns{display:flex;gap:10px;margin:12px 0 4px}
@media (max-width:1400px){body{grid-template-columns:320px 1fr;grid-template-rows:62vh 38vh}#ui{grid-row:1 / span 2}#plots{grid-column:2;grid-row:2;display:flex;overflow-x:auto}#plots>div{flex:0 0 440px;height:100%!important}}
</style>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js",
"three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div id="ui">
<b>JoystickPushTask rig explorer</b>
<h3>Magnet option</h3>
<label><input type="radio" name="opt" value="link" checked> plunger linked to the shaft</label><br>
<label><input type="radio" name="opt" value="washers"> washer target on the shaft</label><div class="btns"><button id="rec" title="reset every slider to its default">set default</button><button id="unitBtn" title="switch every force between gram-force (gf) and newton (N)">force unit: gf</button></div>
<h3>Magnet</h3>
<div class="row"><span id="face_lbl">stroke length (mm)</span><input id="face" type="range" min="0" max="70" step="0.01"><input id="face_v" class="num" type="number" step="any"></div>
<div class="row"><span title="height distance to pivot">magnet height (mm)</span><input id="H" type="range" min="15" max="65" step="0.01"><input id="H_v" class="num" type="number" step="any"></div>
<div class="row"><span>AO0 command (V)</span><input id="volts" type="range" min="0" max="10" step="0.1" value="10"><input id="volts_v" class="num" type="number" step="any"></div>
<label><input type="checkbox" id="imax"> Imax raised (0.58 A, ignores the command)</label>
<input id="Y" type="hidden" value="0">
<h3>Joystick</h3>
<div class="row"><span>push at the cube (mm)</span><input id="push" type="range" step="0.01" value="0"><input id="push_v" class="num" type="number" step="any"></div>
<div class="row"><span title="height from the bottom face of the TS-1D1S00A component">pivot depth (mm)</span><input id="dp" type="range" step="0.1"><input id="dp_v" class="num" type="number" step="any"></div>
<h3>Return spring and friction</h3>
<div class="row"><span id="k_lbl">spring stiffness (gf/mm)</span><input id="k" type="range" min="0" max="2" step="0.01"><input id="k_v" class="num" type="number" step="any"></div>
<div class="row"><span title="Friction coefficient of the plunger sliding in the Ledex bearing (dry nylon on steel: 0.15 slippery, 0.3 typical, 0.4 sticky). Higher = more drag on the handle.">plunger friction (no unit)</span><input id="mu" type="range" min="0.1" max="0.5" step="0.01"><input id="mu_v" class="num" type="number" step="any"></div>
<h3>View</h3>
<label><input type="checkbox" id="cut"> section at Y = 0 (hide the -Y half)</label><br>
<div id="parts"></div>
<h3>Readout</h3><div id="read"></div>
<p><small>Forces: washers from the 3D model (offset sweep, +-40 %), plunger from FEMM anchored to the datasheet
(+-15-20 %); current held constant. Spring as felt at the cube: k per mm from neutral.
See simulations/ledex_femm/README.md.</small></p>
</div>
<div id="view"><div id="hint">drag: orbit, scroll: zoom, right-drag: pan</div></div>
<div id="plots"><div id="pf" style="height:400px"></div><div id="pm" style="height:360px"></div><div id="pc" style="height:340px"></div></div>
<script>__PHYS__</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const D = __DATA__;
function bytes(s){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u.buffer;}
const P = makePhys(D, s => new Float32Array(bytes(s))), G = D.G;
const $ = id => document.getElementById(id);

// ---------------- scene (Z up, world mm: X push away from the mouse, origin under the joystick axis)
THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const view = $('view'), scene = new THREE.Scene(); scene.background = new THREE.Color(0xf4f4f4);
const cam = new THREE.PerspectiveCamera(32, 1, 1, 3000);
const ren = new THREE.WebGLRenderer({antialias: true}); ren.setPixelRatio(devicePixelRatio); view.appendChild(ren.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x777777, 1.7));
const dl = new THREE.DirectionalLight(0xffffff, 1.5); dl.position.set(-150, -200, 250); scene.add(dl);
const grid = new THREE.GridHelper(300, 12, 0x999999, 0xcccccc); grid.rotation.x = Math.PI / 2; scene.add(grid);
const cut = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
const mats = [];
function mat(color, opacity){ const m = new THREE.MeshStandardMaterial({color, transparent: opacity < 1, opacity,
  side: THREE.DoubleSide, flatShading: true, depthWrite: opacity >= 1, metalness: 0.1, roughness: 0.7}); mats.push(m); return m; }
const pivotG = new THREE.Group(), rotG = new THREE.Group(); pivotG.add(rotG); scene.add(pivotG);
const ledG = new THREE.Group(), uprG = new THREE.Group(), baseG = new THREE.Group(), linkG = new THREE.Group();
const collarG = new THREE.Group(), plungerG = new THREE.Group(); rotG.add(collarG); ledG.add(plungerG);
scene.add(ledG, uprG, baseG, linkG);
const frames = {static: scene, moving: rotG, ledex: ledG, plunger: plungerG, upright: uprG, base: baseG, collar: collarG,
                link: linkG};
const toggles = [];
function addToggle(name, color, objs){ const id = 't' + toggles.length; toggles.push(objs);
  $('parts').insertAdjacentHTML('beforeend', `<label><input type="checkbox" id="${id}" checked> <span class="sw" style="background:${color}"></span>${name}</label><br>`);
  $(id).onchange = e => { for (const o of objs) o.userData.on = e.target.checked; update(); }; }
for (const p of D.meshes){
  const pos = new Int16Array(bytes(p.tris)), f = new Float32Array(pos.length);
  for (let i = 0; i < pos.length; i++) f[i] = pos[i] / 100;
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(f, 3)); g.computeVertexNormals();
  const m = new THREE.Mesh(g, mat(p.color, p.opacity)); m.userData.on = true; m.userData.opt = p.opt;
  frames[p.frame].add(m); addToggle(p.name, p.color, [m]);
}
// nut (assumed size) in the Ledex frame (X from the body face, Z from the axis); pins along Y
function cylX(r, x0, x1, color, opacity, seg){ const g = new THREE.CylinderGeometry(r, r, x1 - x0, seg || 48);
  g.rotateZ(-Math.PI / 2); g.translate((x0 + x1) / 2, 0, 0); const m = new THREE.Mesh(g, mat(color, opacity)); m.userData.on = true; return m; }
function pinY(x, len){ const g = new THREE.CylinderGeometry(G.PIN_D / 2, G.PIN_D / 2, len, 24); g.translate(x, 0, 0);
  const m = new THREE.Mesh(g, mat('#303030', 1)); m.userData.on = true; m.userData.opt = 'link'; return m; }
const nutM = cylX(G.NUT_R, G.PLATE_T, G.PLATE_T + G.NUT_T, '#a0a0a0', 1, 6); ledG.add(nutM);
addToggle('M14 nut (assumed size)', '#a0a0a0', [nutM]);
const tipPin = pinY(G.protrude - G.PIN_FROM_TIP, G.PIN_LEN), collarPin = pinY(-G.ATTACH_R, 9);
plungerG.add(tipPin); collarG.add(collarPin); addToggle('link pins', '#303030', [tipPin, collarPin]);
// washer tower on the shaft
const towerG = new THREE.Group(); rotG.add(towerG); const wm = mat('#b9b9b9', 1);
for (let i = 0; i < G.N_WASHERS; i++){
  const pts = [[G.WASHER_RI, 0.02], [G.WASHER_RO, 0.02], [G.WASHER_RO, G.WASHER_T - 0.02], [G.WASHER_RI, G.WASHER_T - 0.02], [G.WASHER_RI, 0.02]]
    .map(([r, z]) => new THREE.Vector2(r, z));
  const g = new THREE.LatheGeometry(pts, 40); g.rotateX(Math.PI / 2);
  g.translate(0, 0, G.SHAFT_BASE + G.WASHER_SEAT + i * G.WASHER_T); towerG.add(new THREE.Mesh(g, wm));
}
towerG.userData.on = true; addToggle('washer tower', '#b9b9b9', [towerG]);
const pivotM = new THREE.Mesh(new THREE.SphereGeometry(1.4, 20, 12), mat('#ff00ff', 1)); pivotM.userData.on = true; scene.add(pivotM);
addToggle('pivot', '#ff00ff', [pivotM]);

const ctl = new OrbitControls(cam, ren.domElement); ctl.target.set(-30, 0, 50); cam.position.set(-280, -360, 230); ctl.update();
function resize(){ const w = view.clientWidth, h = view.clientHeight; cam.aspect = w / h; cam.updateProjectionMatrix(); ren.setSize(w, h); }
addEventListener('resize', resize); resize();
(function loop(){ requestAnimationFrame(loop); ren.render(scene, cam); })();

// ---------------- controls
const ctrl = {face: 2, H: 2, push: 2, volts: 1, dp: 2, k: 2, mu: 2};
function opt(){ return document.querySelector('input[name=opt]:checked').value; }
const tip0 = -G.ATTACH_R - G.LINK + G.PIN_FROM_TIP;
const faceToUi = (o, face) => o === 'link' ? tip0 - G.protrude - face : -G.WASHER_RO - G.protrude - face;
const uiToFace = (o, v) => o === 'link' ? tip0 - G.protrude - v : -G.WASHER_RO - G.protrude - v;
const hToUi = (H, dp) => H - G.SHAFT_BASE + dp;
const uiToH = (v, dp) => v + G.SHAFT_BASE - dp;
const dpToUi = dp => G.COMP_TOP - dp;
const uiToDp = v => G.COMP_TOP - v;
function setLabels(o){
  $('face_lbl').textContent = o === 'link' ? 'stroke length (mm)' : 'distance to target (mm)';
  $('face_lbl').title = o === 'link' ? 'plunger stroke from seated at neutral (0 = fully seated)'
                                     : 'gap from plunger tip to washer tower at neutral';
}
function setRec(){
  const o = opt(), r = D.rec[o], dp = uiToDp(+$('dp').value);
  setLabels(o);
  $('face').value = faceToUi(o, r.face);
  $('H').value = hToUi(r.H, dp);
  lastDp = +$('dp').value;
}
let lastDp = null;      // the pivot moves the scale of the magnet height, never the magnet itself
$('dp').min = dpToUi(G.PIVOT_MAX).toFixed(2); $('dp').max = dpToUi(G.PIVOT_MIN).toFixed(2); $('dp').value = dpToUi(G.PIVOT).toFixed(2);
$('k').value = D.spring.k; $('mu').value = D.spring.mu;
let Hw = D.rec.link.H;     // magnet axis height above the breadboard (world), the true state
setRec();
function amps(){ return $('imax').checked ? 0.58 : P.current(+$('volts').value); }
let pending = false;
function update(){ if (!pending){ pending = true; setTimeout(() => { pending = false; draw(); }, 0); } }
for (const id of Object.keys(ctrl)) $(id).oninput = update;
for (const id of Object.keys(ctrl)){ const n = $(id + '_v');           // numbers can be typed too
  n.oninput = () => { n.dataset.typing = '1'; };
  n.onchange = () => { delete n.dataset.typing; const v = parseFloat(n.value); if (!isNaN(v)) $(id).value = id === 'k' ? v / kScale() : v; update(); };
  n.onblur = () => { delete n.dataset.typing; update(); }; }
for (const el of document.querySelectorAll('input[name=opt]')) el.onchange = () => { setRec(); update(); };
function setDefaults(){          // every slider back to its default
  $('dp').value = dpToUi(G.PIVOT).toFixed(2);
  setRec();
  $('push').value = 0; $('volts').value = 10; $('imax').checked = false;
  $('k').value = D.spring.k; $('mu').value = D.spring.mu;
  for (const id of Object.keys(ctrl)) delete $(id + '_v').dataset.typing;
  update();
}
$('imax').onchange = update; $('cut').onchange = update; $('rec').onclick = setDefaults;

const fmt = (v, d) => (+v).toFixed(d);
let fu = 'gf';                                              // force unit shown: gf or N
const fk = () => fu === 'gf' ? 1 : G.g / 1000;               // gf -> shown unit
const kScale = () => fu === 'gf' ? 1 : G.g;                  // gf/mm -> N/m
const fF = (v, d) => fmt(v * fk(), fu === 'gf' ? d : d + 2) + ' ' + fu;
function setUnitLabels(){
  $('unitBtn').textContent = 'force unit: ' + fu;
  $('k_lbl').textContent = 'spring stiffness (' + (fu === 'gf' ? 'gf/mm' : 'N/m') + ')';
  $('k_lbl').title = 'Return spring: extra force at the cube for each mm of push. Zero force at home. ' +
    (fu === 'gf' ? '1 gf/mm = 9.81 N/m.' : '9.81 N/m = 1 gf/mm.');
}
$('unitBtn').onclick = () => { fu = fu === 'gf' ? 'N' : 'gf'; setUnitLabels(); update(); };
setUnitLabels();
function feasibleRange(el, ok){
  if (!el.dataset.min){ el.dataset.min = el.min; el.dataset.max = el.max; }     // full design range
  const lo0 = +el.dataset.min, hi0 = +el.dataset.max, step = 0.01; let lo = null, hi = null;
  for (let v = lo0; v <= hi0 + 1e-9; v += step) if (ok(v)){ if (lo === null) lo = v; hi = v; }
  return lo === null ? null : [lo, hi]; }
const clampTo = (el, r) => {      // the slider spans exactly the feasible range
  if (!r) return;
  const v = Math.min(Math.max(+el.value, r[0]), r[1]);
  el.min = r[0].toFixed(2); el.max = r[1].toFixed(2); el.value = v; };
function limitInputs(o, dp){      // sliders cannot leave the feasible layout
  setLabels(o);
  const hOnly = c => /window|height|collar/.test(c[0]);
  clampTo($('H'), feasibleRange($('H'), v => P.checks(o, uiToH(v, dp), D.rec[o].face, dp).filter(hOnly).every(c => c[1])));
  const H = uiToH(+$('H').value, dp);
  clampTo($('face'), feasibleRange($('face'), v => P.checks(o, H, uiToFace(o, v), dp).every(c => c[1])));
}
function draw(){
  const o = opt();
  const dpUi = Math.min(Math.max(+$('dp').value, +$('dp').min), +$('dp').max);
  $('dp').value = dpUi;
  const dp = uiToDp(dpUi);
  const hel = $('H');
  if (lastDp !== null && dpUi !== lastDp) hel.value = hToUi(Hw, dp);      // pivot moved: same magnet, new reading
  lastDp = dpUi;
  hel.dataset.min = hToUi(30, dp).toFixed(2); hel.dataset.max = hToUi(90, dp).toFixed(2);
  limitInputs(o, dp);
  Hw = uiToH(+hel.value, dp);
  const face = uiToFace(o, +$('face').value), H = Hw, Y = +$('Y').value;
  const us = P.stopPush(dp), um = P.maxPush(dp);
  $('push').min = us.toFixed(2); $('push').max = um.toFixed(2);
  const u = Math.min(Math.max(+$('push').value, us), um), a = amps(), mu = +$('mu').value, p0 = 0, k = +$('k').value;
  for (const id of Object.keys(ctrl)){ const n = $(id + '_v'), el = $(id);
    const sc = id === 'k' ? kScale() : 1;
    n.min = +el.min * sc; n.max = +el.max * sc;
    if (!n.dataset.typing) n.value = fmt((id === 'push' ? u : el.value) * sc, ctrl[id]); }
  ren.clippingPlanes = $('cut').checked ? [cut] : [];
  // geometry
  const s = P.state(o, u, H, face, a, dp, mu), Zp = G.SHAFT_BASE - dp;
  pivotG.position.set(0, 0, Zp); rotG.position.set(0, 0, -Zp); pivotG.rotation.y = s.th; pivotM.position.set(0, 0, Zp);
  ledG.position.set(face, Y, H); uprG.position.set(face, Y, 0); baseG.position.set(face, 0, 0);
  plungerG.position.x = (o === 'link' ? s.tip : face + G.protrude) - face - G.protrude;
  collarG.position.set(0, 0, G.SHAFT_BASE + (o === 'link' ? s.za : 0));
  if (o === 'link'){ linkG.position.set(s.sx, 0, G.SHAFT_BASE + s.sz);
    linkG.rotation.set(0, Math.atan2(-(s.za - s.sz), s.px - s.sx), 0); }
  const show = (obj, on) => { obj.visible = obj.userData.on && on; };
  for (const g of toggles) for (const m of g) show(m, m === towerG ? o === 'washers' : (m.userData.opt ? m.userData.opt === o : true));
  for (const c of collarG.children) show(c, o === 'link'); for (const c of linkG.children) show(c, o === 'link');
  // readout
  const sp = P.spring(u, p0, k), fr = o === 'link' ? s.fric : 0;
  const s0 = P.state(o, 0, H, face, a, dp, mu);
  const pulled = s0.F > p0 + (o === 'link' ? s0.fric : 0);
  const rows = [['coil current', fmt(a, 3) + ' A'], ['joystick tilt', fmt(s.th * 180 / Math.PI, 2) + '&deg;']];
  if (o === 'washers') rows.push(['gap (tip to washers)', fmt(s.gap, 2) + ' mm'], ['tower centre above the axis', fmt(s.yoff, 2) + ' mm'],
                                 ['pull on the tower', fF(s.pull, 3)], ['handle / tower force ratio (no unit)', fmt(s.ratio, 3)]);
  else rows.push(['plunger stroke', fmt(s.stroke, 2) + ' mm (home ' + fmt(s.s0, 2) + ')'], ['link angle', fmt(s.linkDeg, 2) + '&deg;'],
                 ['plunger pull', fF(s.pull, 1)], ['handle / plunger force ratio (no unit)', fmt(s.ratio, 3)]);
  rows.push(['<b>magnet force at the cube</b>', '<b>' + fF(s.F, s.F < 1 ? 3 : 1) + '</b>'], ['spring force at the cube', fF(sp, 2)],
            ['plunger friction at the cube', fF(fr, 2)], ['<b>push needed to hold here</b>', '<b>' + fF(s.F + sp + fr, 2) + '</b>']);
  $('read').innerHTML = '<table>' + rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('') + '</table>';
  plots(o, H, face, a, dp, mu, p0, k, u, us, um);
}

// ---------------- plots
const other = o => o === 'link' ? 'washers' : 'link';
const name = o => o === 'link' ? 'plunger link' : 'washer target';
function plots(o, H, face, a, dp, mu, p0, k, u, us, um){
  const us_ = [], F = [], Fo = [], S = [], T = [], K = fk();
  const r = D.rec[other(o)];
  for (let i = 0; i <= 120; i++){ const x = us + (um - us) * i / 120; us_.push(x);
    const s = P.state(o, x, H, face, a, dp, mu); F.push(Math.max(s.F, 1e-3) * K);
    Fo.push(Math.max(P.state(other(o), x, r.H, r.face, a, dp, mu).F, 1e-3) * K);
    const sp = P.spring(x, p0, k); S.push(sp * K); T.push((s.F + sp + (o === 'link' ? s.fric : 0)) * K); }
  const lay = (t, x, y, extra) => Object.assign({title: {text: t, font: {size: 12}}, margin: {l: 55, r: 10, t: 34, b: 42},
    xaxis: {title: x}, yaxis: {title: y}, legend: {font: {size: 10}, orientation: 'h', x: 0, y: -0.22, yanchor: 'top'},
    showlegend: true}, extra || {});
  Plotly.react('pf', [
    {x: us_, y: F, name: 'magnet, ' + name(o), line: {color: '#c62828'}},
    {x: us_, y: Fo, name: 'magnet, ' + name(other(o)) + ' (recommended layout)', line: {color: '#999', dash: 'dash'}},
    {x: us_, y: S, name: 'spring', line: {color: '#1565c0'}},
    {x: us_, y: T, name: 'push to hold (magnet + spring + friction)', line: {color: '#222', width: 1}},
    {x: [u, u], y: [0, 150 * K], name: 'push', mode: 'lines', line: {color: '#2e7d32', dash: 'dot'}, showlegend: false}],
    lay('Force at the cube vs push', 'push at the cube (mm)', fu,
        {yaxis: {title: fu, rangemode: 'tozero'}}), {displayModeBar: false});
  // live design map at this command, push and pivot
  const xs = [], ys = [], Z = [], M = [];
  const fx = o === 'link' ? [-56, -34] : [-37, -25], hz = o === 'link' ? [50, 64] : [42, 66];
  for (let j = 0; j <= 48; j++) ys.push(hz[0] + (hz[1] - hz[0]) * j / 48);
  for (let i = 0; i <= 48; i++) xs.push(fx[0] + (fx[1] - fx[0]) * i / 48);
  for (const h of ys){ const zr = [], mr = [];
    for (const x of xs){ const ok = P.checks(o, h, x, dp).every(c => c[1]); const f = P.state(o, u, h, x, a, dp, mu).F;
      zr.push(Math.log10(Math.max(f, 1e-3) * K)); mr.push(ok ? null : 1); }
    Z.push(zr); M.push(mr); }
  Plotly.react('pm', [
    {type: 'heatmap', x: xs, y: ys, z: Z, colorscale: 'Viridis', zmin: -1.5 + Math.log10(K), zmax: 2.2 + Math.log10(K),
     colorbar: {title: 'log10 ' + fu, len: 0.8}, hovertemplate: 'face X %{x:.1f}<br>axis Z %{y:.1f}<br>log10 ' + fu + ' %{z:.2f}<extra></extra>'},
    {type: 'heatmap', x: xs, y: ys, z: M, colorscale: [[0, 'rgba(255,255,255,0.7)'], [1, 'rgba(255,255,255,0.7)']], showscale: false, hoverinfo: 'skip'},
    {x: [face], y: [H], mode: 'markers', marker: {symbol: 'star', size: 14, color: 'lime', line: {color: 'black', width: 1}}, name: 'current'}],
    lay(`Design map: ${name(o)} at this push and command (pale: not feasible)`, 'Ledex face X (mm)', 'Ledex axis Z (mm)', {showlegend: false}),
    {displayModeBar: false});
  const vs = [], A = [], B = [];
  for (let i = 0; i <= 40; i++){ const v = 0.5 + 9.5 * i / 40; vs.push(v); const ai = P.current(v);
    A.push(P.state(o, 0, H, face, ai, dp, mu).F * K); B.push(P.state(other(o), 0, r.H, r.face, ai, dp, mu).F * K); }
  Plotly.react('pc', [
    {x: vs, y: A, name: name(o) + ' (this layout)', line: {color: '#c62828'}},
    {x: vs, y: B, name: name(other(o)) + ' (recommended)', line: {color: '#999', dash: 'dash'}}],
    lay('Resistance at neutral vs AO0 command (Imax at minimum)', 'AO0 command (V)', fu,
        {yaxis: {title: fu, rangemode: 'tozero'}}), {displayModeBar: false});
}
draw();
</script></body></html>
"""


def write_html(wf, tab):
    data = browser_data(wf, tab)
    ok = js_check(data, wf, tab)
    meshes = []
    for name, src, frame, color, opacity in MESHES:
        o = "link" if src in ("link_collar", "link_bar") else None
        meshes.append(dict(name=name, frame=frame, color=color, opacity=opacity, opt=o, tris=enc_i16(mesh(src))))
    data["meshes"] = meshes
    sub = ("measured holder, component and constrainer CAD; pivot %.1f mm below the shaft base (%.1f-%.1f tested); "
           "home stop %.2f mm at the cube" % (rg.PIVOT_DEPTH, PIVOT_RANGE[0], PIVOT_RANGE[1], rg.stop_push(rg.PIVOT_DEPTH)))
    html = HTML.replace("__PHYS__", PHYS_JS).replace("__DATA__", json.dumps(data)).replace("__SUBTITLE__", sub) \
        .replace("__HMIN__", "%g" % rf.H_RANGE[0]).replace("__HMAX__", "%g" % rf.H_RANGE[1])
    os.makedirs(OUT_FIG, exist_ok=True)
    path = os.path.join(OUT_FIG, "rig_explorer.html")
    open(path, "w").write(html)
    print("wrote", os.path.relpath(path, HERE), "%.1f MB" % (len(html) / 1e6))
    return ok


# ---------------------------------------------------------------- static figures
def placed_parts(opt, push, d_p=rg.PIVOT_DEPTH):
    """World triangles of every part for an option at its recommended layout and a push; plus Ledex solids."""
    r = rf.REC[opt]
    H, face = r["H"], r["face"]
    th = float(rg.tilt_for_push(push, d_p))
    if opt == "washers":
        tip = face + LX["protrude"]
    else:
        k = pl.kinematics(push, d_p, rg.shaft_z(H), rf.link_settings(H, face)[1])
        tip = float(k["pin_x"][0]) + rg.PIN_FROM_TIP
    out = []
    for name, src, frame, color, opacity in MESHES:
        if src in ("link_collar", "link_bar") and opt != "link":
            continue
        t = mesh(src)
        if frame == "moving":
            t = rg.tilt_world(t, d_p, th)
        elif frame == "ledex":
            t = t + np.array([face, 0, H])
        elif frame == "plunger":
            t = t + np.array([tip - LX["protrude"], 0, H])
        elif frame in ("upright", "base"):
            t = t + np.array([face, 0, 0])
        elif frame == "collar":
            t = rg.tilt_world(t + np.array([0, 0, H]), d_p, th)
        elif frame == "link":
            k = pl.kinematics(push, d_p, rg.shaft_z(H), rf.link_settings(H, face)[1])
            sx, sz, px = float(k["collar_x"][0]), float(k["collar_z"][0]), float(k["pin_x"][0])
            ang = np.arctan2(rg.shaft_z(H) - sz, px - sx)
            c, s_ = np.cos(ang), np.sin(ang)
            x, z = t[..., 0] * c - t[..., 2] * s_, t[..., 0] * s_ + t[..., 2] * c
            t = np.stack([x + sx, t[..., 1], z + rg.world_z(sz)], -1)
        out.append((name, t, color, opacity))
    solids = [("nut", face + rg.PLATE_T, face + rg.PLATE_T + rg.NUT_T, NUT_R * 0.866, "#a0a0a0")]
    pins = []
    if opt == "link":
        cx, cz = rg.rotate(-rg.ATTACH_R, rg.shaft_z(H), d_p, th)
        pins = [(tip - rg.PIN_FROM_TIP, H), (float(cx), float(rg.world_z(cz)))]
    return out, solids, pins, H, face, th


def side_view(path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
    for row, opt in enumerate(("washers", "link")):
        for col, push in enumerate((0.0, 15.0)):
            ax = axes[row, col]
            parts, solids, pins, H, face, th = placed_parts(opt, push)
            for name, t, color, _ in parts:
                seg = rg.slice_mesh(t, 1, CHEEK_Y if name.startswith("plunger") else 0.0)
                if len(seg):
                    ax.plot(seg[:, :, 0].T, seg[:, :, 2].T, color=color, lw=0.8)
                if name == "Ledex upright":
                    seg = rg.slice_mesh(t, 1, 17.9)
                    ax.plot(seg[:, :, 0].T, seg[:, :, 2].T, color=color, lw=0.5, alpha=0.4, ls="--")
            for name, x0, x1, r, color in solids:
                ax.add_patch(plt.Rectangle((x0, H - r), x1 - x0, 2 * r, fc=color, ec="k", lw=0.5, alpha=0.5))
            for x, z in pins:
                ax.add_patch(plt.Circle((x, z), rg.PIN_D / 2, fc="#303030", ec="none"))
            if opt == "washers":
                for sgn in (-1, 1):
                    for i in range(rg.N_WASHERS):
                        z0 = rg.WASHER_SEAT + i * rg.WASHER_T
                        px, pz = rg.rotate(np.array([sgn * rg.WASHER_RI, sgn * rg.WASHER_RO, sgn * rg.WASHER_RO,
                                                     sgn * rg.WASHER_RI]),
                                           np.array([z0, z0, z0 + rg.WASHER_T, z0 + rg.WASHER_T]), rg.PIVOT_DEPTH, th)
                        ax.fill(px, rg.world_z(pz), color="#888", lw=0)
            ax.plot(0, rg.SHAFT_BASE - rg.PIVOT_DEPTH, "o", color="m", ms=5)
            ax.axhline(0, color="k", lw=1)
            ax.set_aspect("equal")
            ax.set_xlim(-90, 35)
            ax.set_ylim(-3, 145)
            ax.grid(alpha=0.25)
            ttl = "Washer target" if opt == "washers" else "Plunger link"
            ax.set_title("%s, push %g mm: axis Z %.1f, face X %.1f" % (ttl, push, H, face), fontsize=10)
            if row == 1:
                ax.set_xlabel("X (mm, push direction; joystick axis at neutral = 0)")
            if col == 0:
                ax.set_ylabel("Z above the breadboard (mm)")
    fig.suptitle("Section at Y = 0 through the rig CAD (plunger at Y %.1f, through a slot cheek; dashed: upright wall "
                 "at Y 17.9; magenta: pivot %.1f mm below the shaft base)" % (CHEEK_Y, rg.PIVOT_DEPTH))
    fig.tight_layout()
    save(fig, os.path.basename(path), os.path.dirname(path))
    plt.close(fig)


def cyl_tris(x0, x1, r, zc, n=28):
    a = np.linspace(0, 2 * np.pi, n + 1)
    y, z = r * np.cos(a), zc + r * np.sin(a)
    q = []
    for i in range(n):
        q.append([[x0, y[i], z[i]], [x1, y[i], z[i]], [x1, y[i + 1], z[i + 1]]])
        q.append([[x0, y[i], z[i]], [x1, y[i + 1], z[i + 1]], [x0, y[i + 1], z[i + 1]]])
    return np.array(q)


def assembly_png(path):
    fig = plt.figure(figsize=(15, 7))
    for k, opt in enumerate(("washers", "link")):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        parts, solids, pins, H, face, th = placed_parts(opt, 0.0)
        light = np.array([-0.4, -0.6, 0.7]) / np.linalg.norm([-0.4, -0.6, 0.7])
        for name, t, color, opacity in parts + [(n, cyl_tris(x0, x1, r, H), c, 0.8) for n, x0, x1, r, c in solids]:
            n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            shade = 0.45 + 0.55 * np.abs(n @ light)
            rgb = np.array(matplotlib.colors.to_rgb(color))
            fc = np.c_[np.clip(rgb * shade[:, None], 0, 1), np.full(len(t), opacity)]
            ax.add_collection3d(Poly3DCollection(t, facecolors=fc, linewidths=0))
        ax.set_xlim(-90, 30); ax.set_ylim(-60, 60); ax.set_zlim(0, 120)
        ax.set_box_aspect((120, 120, 120))
        ax.view_init(elev=22, azim=-62)
        ax.set_xlabel("X push (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
        ttl = "Washer target" if opt == "washers" else "Plunger link"
        ax.set_title("%s: Ledex axis Z %.1f, face X %.1f" % (ttl, H, face), fontsize=10)
    fig.suptitle("Rig assembly at neutral with the adjustable Ledex holder")
    fig.tight_layout()
    save(fig, os.path.basename(path), os.path.dirname(path))
    plt.close(fig)


def main():
    wf = rf.WasherForce()
    tab = pl.plunger_table()
    ok = write_html(wf, tab)
    side_view(os.path.join(OUT_FIG, "side_view.png"))
    assembly_png(os.path.join(OUT_FIG, "assembly_3d.png"))
    if not ok:
        raise SystemExit("browser model does not match rig_forces.py")


if __name__ == "__main__":
    main()
