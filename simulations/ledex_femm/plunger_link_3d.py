"""3D view of the plunger-link layout (needs the NGSolve venv for netgen.occ; see README).

    /tmp/ngenv/bin/python plunger_link_3d.py
        -> figures/plunger_link/assembly_3d.png, figures/plunger_link/assembly_3d.html (three.js from a CDN,
           push slider), results/plunger_link/apem_ts_outline.csv (thumbstick outline for the 2D side view)

Parts: the repo STL exports (shaft, cube handle, 1D constrainer, Ledex holder), APEM's TS-1D STEP (outer envelope,
downloaded to the temp folder on first use, castle cap removed) and simple solids for the Ledex case, boss,
plunger, link and shaft collar. Positions come from plunger_link.layout(); the joystick rotates about the pivot
(10 mm below the shaft base) and the plunger slides with the link, using plunger_link.kinematics().
"""
import base64
import csv
import io
import json
import os
import tempfile
import urllib.request
import zipfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import plunger_link as pl

TS_URL = "https://gsglobalresources.com/uploads/apem-joystick-TS-step-1.zip"
TS_AXIS = (-57.094, 13.15)       # STEP x, z of the stick axis (centre of the cap-top sphere)
TS_PANEL_Y = 22.21               # underside of the drop-in bezel = panel top (castle top is 19.2 mm above it)
TS_CAP_Y = 35.6                  # top of the boot; the castle cap above it is removed on the rig
OUTLINE_CSV = os.path.join(pl.OUT_RES, "apem_ts_outline.csv")
PUSHES = np.linspace(0, 15, 61)


# ---------------------------------------------------------------- meshes (triangles in lever coordinates)
def read_stl(path):
    import struct
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(50 * n), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return d["v"].reshape(-1, 3, 3).astype(float)


def cad(rel, fn):
    t = read_stl(os.path.join(pl.CAD, rel))
    return fn(t.reshape(-1, 3)).reshape(-1, 3, 3)


def cylinder_x(x0, x1, r, z, y=0.0, n=48):
    a = np.linspace(0, 2 * np.pi, n + 1)
    ring = np.stack([np.cos(a), np.sin(a)], 1) * r
    tris = []
    for i in range(n):
        (y0, z0), (y1, z1) = ring[i], ring[i + 1]
        p = [(x0, y + y0, z + z0), (x1, y + y0, z + z0), (x1, y + y1, z + z1), (x0, y + y1, z + z1)]
        tris += [[p[0], p[1], p[2]], [p[0], p[2], p[3]],
                 [(x0, y, z), p[3], p[0]], [(x1, y, z), p[1], p[2]]]
    return np.array(tris, float)


def cylinder_z(z0, z1, r, n=40):
    t = cylinder_x(z0, z1, r, 0.0, n=n)
    return t[..., [1, 2, 0]]


def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    c = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
                  [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]], [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]])
    q = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array([[c[a], c[b], c[d]] for a, b, cc, d in q for (a, b, d) in ((a, b, cc), (a, cc, d))])


def ts_step():
    folder = os.path.join(tempfile.gettempdir(), "apem_ts")
    path = os.path.join(folder, "ts1d.step")
    if not os.path.exists(path):
        os.makedirs(folder, exist_ok=True)
        print("downloading", TS_URL)
        req = urllib.request.Request(TS_URL, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            name = [n for n in z.namelist() if n.endswith("TS-1D.STEP")][0]
            with open(path, "wb") as f:
                f.write(z.read(name))
    return path


def ts_mesh(maxh=5.0):
    """Thumbstick envelope (castle cap removed), panel at z = -SHAFT_BASE; also writes the 2D outline CSV."""
    from netgen.occ import OCCGeometry
    from netgen.meshing import MeshingStep
    m = OCCGeometry(ts_step()).GenerateMesh(maxh=maxh, perfstepsend=MeshingStep.MESHSURFACE)
    P = np.array([p.p for p in m.Points()])
    F = np.array([[v.nr - 1 for v in el.vertices] for el in m.Elements2D()])
    F = F[P[F, 1].max(axis=1) <= TS_CAP_Y]
    T = P[F]
    out = np.stack([T[..., 0] - TS_AXIS[0], T[..., 2] - TS_AXIS[1], T[..., 1] - TS_PANEL_Y - pl.SHAFT_BASE], -1)
    h = (P[np.unique(F), 1] - TS_PANEL_Y)
    half = np.abs(P[np.unique(F), 0] - TS_AXIS[0])
    bins = np.arange(np.floor(h.min()), np.ceil(h.max()) + 0.5, 0.5)
    os.makedirs(pl.OUT_RES, exist_ok=True)
    with open(OUTLINE_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["height_above_panel_mm", "half_width_mm"])
        for b0, b1 in zip(bins[:-1], bins[1:]):
            sel = (h >= b0) & (h < b1)
            if sel.any():
                w.writerow(["%.2f" % ((b0 + b1) / 2), "%.2f" % half[sel].max()])
    print("wrote", os.path.relpath(OUTLINE_CSV, pl.HERE))
    return out


def parts(z_a, s0, d_p):
    """[(name, triangles, colour, opacity, group)] at home; group: static / rot (joystick) / plunger."""
    L = pl.layout(z_a, s0)
    zc = L["constrainer"]
    lx = pl.LEDEX
    out = [
        ("plate (thumbstick panel)", box((-100, -30, L["panel"] - 3), (30, 30, L["panel"])), "#c8c8c8", 0.35, "static"),
        ("thumbstick body (APEM TS, cap removed)", ts_mesh(), "#3a3a3a", 1.0, "static"),
        ("1D constrainer", cad("joystick-1d-axis-constrainer/joystick_1d_axis_constrainer_38x38x56.stl",
                               lambda v: np.stack([v[:, 1], v[:, 0], v[:, 2] + zc], 1)), "#6fa8dc", 0.3, "static"),
        ("Ledex holder", cad("ledex-holder/ledex_195224-230_holder_30mm_axis.stl",
                             lambda v: np.stack([v[:, 0] - 10 + L["face"], v[:, 1], v[:, 2] + L["panel"] + z_a - 14.5], 1)),
         "#f6b26b", 0.45, "static"),
        ("Ledex case", cylinder_x(L["face"] - lx["case_len"], L["face"], lx["case_r"], z_a), "#b7b7b7", 1.0, "static"),
        ("Ledex boss", cylinder_x(L["face"], L["face"] + lx["boss_len"], lx["boss_r"], z_a), "#999999", 1.0, "static"),
        ("plunger", cylinder_x(L["face"] - 6, L["tip0"], lx["plunger_r"], z_a), "#5b5b5b", 1.0, "plunger"),
        ("shaft (printed)", cad("joystick/joystick_89mm.stl", lambda v: v), "#f3f3f3", 1.0, "rot"),
        ("cube handle (printed)", cad("joystick-handle-cube/joystick_handle_cube.stl",
                                      lambda v: np.stack([v[:, 1] - 4.25, v[:, 0], v[:, 2] + 88.9], 1)),
         "#45b5aa", 1.0, "rot"),
        ("shaft collar (link pin)", cylinder_z(z_a - 2.5, z_a + 2.5, 4.0), "#cc0000", 1.0, "rot"),
    ]
    return out, L


def frames(z_a, s0, d_p, tab):
    k = pl.kinematics(PUSHES, d_p, z_a, s0)
    L = pl.layout(z_a, s0)
    force = {name: np.round(pl.handle_curves(tab, a, d_p, z_a, s0, PUSHES), 3).tolist() for a, name in pl.COMMANDS}
    return dict(push=PUSHES.round(3).tolist(), tilt=np.radians(k["tilt_deg"]).round(6).tolist(),
                stroke=k["stroke_mm"].round(3).tolist(), collar=np.stack([k["collar_x"], k["collar_z"]], 1).round(4).tolist(),
                plunger_dx=(k["pin_x"] - L["pin0"]).round(4).tolist(), force=force, z_a=z_a, s0=s0, d_p=d_p,
                link=pl.LINK, pin_from_tip=pl.PIN_FROM_TIP)


# ---------------------------------------------------------------- PNG render
def shade(tris, color, light=(0.4, -0.6, 0.7)):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    lam = 0.45 + 0.55 * np.abs(n @ (np.array(light) / np.linalg.norm(light)))
    rgb = np.array(matplotlib.colors.to_rgb(color))
    return np.clip(rgb[None] * lam[:, None], 0, 1)


def posed(tris, group, f, i, d_p, z_a):
    t = tris.copy()
    if group == "rot":
        th = f["tilt"][i]
        x, z = t[..., 0], t[..., 2] + d_p
        t[..., 0], t[..., 2] = x * np.cos(th) + z * np.sin(th), -x * np.sin(th) + z * np.cos(th) - d_p
    elif group == "plunger":
        t[..., 0] += f["plunger_dx"][i]
    return t


def link_tris(f, i, z_a, L):
    cx, cz = f["collar"][i]
    px = L["pin0"] + f["plunger_dx"][i]
    t = box((0, -0.75, -1.0), (1, 0.75, 1.0))
    ang = np.arctan2(cz - z_a, cx - px)
    length = np.hypot(cx - px, cz - z_a)
    t[..., 0] *= length
    x, z = t[..., 0], t[..., 2]
    t[..., 0], t[..., 2] = px + x * np.cos(ang) - z * np.sin(ang), z_a + x * np.sin(ang) + z * np.cos(ang)
    return t


def render_png(items, L, f, z_a, d_p, path):
    fig = plt.figure(figsize=(16, 7.5))
    views = ((22, -125, "from the mouse side, push 0 mm"), (0, -90, "side view, push 0 mm (grey ghost: 15 mm)"))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        polys, cols = [], []
        for name, tris, color, alpha, group in items:
            t = posed(tris, group, f, 0, d_p, z_a)
            polys.append(t)
            c = np.c_[shade(t, color), np.full(len(t), alpha)]
            cols.append(c)
            if k == 1 and group in ("rot", "plunger"):
                g = posed(tris, group, f, len(f["push"]) - 1, d_p, z_a)
                polys.append(g)
                cols.append(np.c_[shade(g, "#bbbbbb"), np.full(len(g), 0.25)])
        lt = link_tris(f, 0, z_a, L)
        polys.append(lt)
        cols.append(np.c_[shade(lt, "#d4a017"), np.ones(len(lt))])
        P = np.concatenate(polys)
        ax.add_collection3d(Poly3DCollection(P, facecolors=np.concatenate(cols), linewidths=0))
        ax.set_xlim(-100, 30); ax.set_ylim(-32, 32); ax.set_zlim(L["panel"] - 20, 100)
        ax.set_box_aspect((130, 64, 120 - L["panel"]))
        ax.view_init(elev=elev, azim=azim)
        ax.set_xlabel("push direction x (mm)"); ax.set_ylabel("y"); ax.set_zlabel("z (mm)")
        ax.set_title(title, fontsize=10)
    fig.suptitle("Plunger-link layout (link at shaft z {:g} mm, home stroke {:g} mm, pivot {:g} mm below the shaft base)"
                 .format(z_a, L["s0"], d_p))
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print("wrote", os.path.relpath(path, pl.HERE))


# ---------------------------------------------------------------- HTML viewer
HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Plunger-link layout</title>
<style>
body{margin:0;font-family:system-ui,sans-serif;background:#f4f4f4;overflow:hidden}
#ui{position:absolute;top:10px;left:10px;background:rgba(255,255,255,.92);padding:10px 14px;border-radius:8px;
    font-size:13px;max-width:380px;box-shadow:0 1px 4px rgba(0,0,0,.2)}
#ui input[type=range]{width:260px}
.sw{display:inline-block;width:10px;height:10px;margin-right:5px;border:1px solid #666}
small{color:#555}
</style>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js",
"three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div id="ui">
<b>Plunger linked to the joystick</b><br>
<small>__SUBTITLE__</small><br><br>
push at the cube <input id="push" type="range" min="0" max="15" step="0.1" value="0"> <span id="pv"></span><br>
command <select id="cmd"></select><br><br>
<div id="read"></div><br>
<div id="parts"></div>
<small>Drag to orbit, scroll to zoom, right-drag to pan. Positions of the constrainer and holder are assumptions
(see README, "Plunger link").</small>
</div>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const D = __DATA__;
function bytes(s){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u.buffer;}
const f32=s=>new Float32Array(bytes(s)), u32=s=>new Uint32Array(bytes(s));
const scene=new THREE.Scene(); scene.background=new THREE.Color(0xf4f4f4);
const cam=new THREE.PerspectiveCamera(35,innerWidth/innerHeight,1,2000);
const ren=new THREE.WebGLRenderer({antialias:true}); ren.setSize(innerWidth,innerHeight); ren.setPixelRatio(devicePixelRatio);
document.body.appendChild(ren.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x888888,1.6));
const dl=new THREE.DirectionalLight(0xffffff,1.6); dl.position.set(-150,200,180); scene.add(dl);
// lever coordinates (x push, y lateral, z up) -> three (x, z, -y)
const world=new THREE.Group(); world.rotation.x=-Math.PI/2; scene.add(world);
const pivot=new THREE.Group(); pivot.position.set(0,0,-D.frames.d_p); world.add(pivot);
const rot=new THREE.Group(); rot.position.set(0,0,D.frames.d_p); pivot.add(rot);
const plunger=new THREE.Group(); world.add(plunger);
const parts=document.getElementById('parts');
for(const p of D.parts){
  const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(f32(p.pos),3));
  g.setIndex(new THREE.BufferAttribute(u32(p.idx),1)); g.computeVertexNormals();
  const m=new THREE.MeshStandardMaterial({color:p.color,transparent:p.opacity<1,opacity:p.opacity,side:THREE.DoubleSide,
     flatShading:true,depthWrite:p.opacity>=1,metalness:0.1,roughness:0.7});
  const mesh=new THREE.Mesh(g,m);
  ({static:world,rot:rot,plunger:plunger})[p.group].add(mesh);
  const id='c'+parts.children.length;
  parts.insertAdjacentHTML('beforeend',`<label><input type="checkbox" id="${id}" checked> <span class="sw" style="background:${p.color}"></span>${p.name}</label><br>`);
  document.getElementById(id).onchange=e=>{mesh.visible=e.target.checked;};
}
const link=new THREE.Mesh(new THREE.BoxGeometry(1,1.5,2),new THREE.MeshStandardMaterial({color:'#d4a017'})); world.add(link);
const pv=new THREE.Mesh(new THREE.SphereGeometry(1.2,20,12),new THREE.MeshStandardMaterial({color:'#ff00ff'}));
pv.position.set(0,0,-D.frames.d_p); world.add(pv);
const cmd=document.getElementById('cmd');
for(const k of Object.keys(D.frames.force)) cmd.insertAdjacentHTML('beforeend',`<option>${k}</option>`);
cmd.value='10 V';
function interp(arr,u){const F=D.frames.push,n=F.length-1,t=Math.min(Math.max(u/F[n]*n,0),n),i=Math.min(Math.floor(t),n-1),w=t-i;
  if(Array.isArray(arr[0])) return arr[i].map((v,j)=>v*(1-w)+arr[i+1][j]*w); return arr[i]*(1-w)+arr[i+1]*w;}
function update(){
  const u=+document.getElementById('push').value, F=D.frames;
  pivot.rotation.y=interp(F.tilt,u);
  const dx=interp(F.plunger_dx,u); plunger.position.x=dx;
  const [cx,cz]=interp(F.collar,u), px=D.pin0+dx, L=Math.hypot(cx-px,cz-F.z_a);
  link.scale.set(L,1,1); link.position.set((cx+px)/2,0,(cz+F.z_a)/2); link.rotation.y=-Math.atan2(cz-F.z_a,cx-px);
  document.getElementById('pv').textContent=u.toFixed(1)+' mm';
  const f=interp(F.force[cmd.value],u);
  document.getElementById('read').innerHTML=`tilt ${(interp(F.tilt,u)*180/Math.PI).toFixed(1)}&deg; &nbsp; stroke ${interp(F.stroke,u).toFixed(2)} mm<br>`+
    `magnet resistance at the cube: <b>${f.toFixed(1)} gf</b> (${(f*9.80665).toFixed(0)} mN)<br>`+
    `<small>plus the centring spring (weakest safe ~${D.p_min.toFixed(1)} gf at home) and ~${D.fric.toFixed(1)} gf plunger friction</small>`;
}
document.getElementById('push').oninput=update; cmd.onchange=update; update();
const ctl=new OrbitControls(cam,ren.domElement); ctl.target.set(-25,30,0); cam.position.set(-280,200,300); ctl.update();
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();ren.setSize(innerWidth,innerHeight);});
(function loop(){requestAnimationFrame(loop);ren.render(scene,cam);})();
</script></body></html>
"""


def indexed(tris):
    """Shared vertices (rounded to 0.01 mm) and a triangle index, base64-encoded for the viewer."""
    v, idx = np.unique(np.round(tris.reshape(-1, 3), 2), axis=0, return_inverse=True)
    enc = lambda a: base64.b64encode(a.tobytes()).decode()
    return enc(v.astype("<f4")), enc(idx.reshape(-1).astype("<u4"))


def write_html(items, L, f, path, p_min, fric):
    data = dict(parts=[dict(zip(("name", "color", "opacity", "group", "pos", "idx"), (n, c, a, g) + indexed(t)))
                       for n, t, c, a, g in items],
                frames=f, pin0=L["pin0"], p_min=p_min, fric=fric)
    sub = ("link at shaft z {:g} mm, home stroke {:g} mm, pivot {:g} mm below the shaft base (magenta); "
           "magnet values: datasheet-anchored FEMM, current held constant").format(L["z_a"], L["s0"], f["d_p"])
    html = HTML.replace("__DATA__", json.dumps(data)).replace("__SUBTITLE__", sub)
    with open(path, "w") as fh:
        fh.write(html)
    print("wrote", os.path.relpath(path, pl.HERE), "%.1f MB" % (len(html) / 1e6))


def main():
    z_a, s0, d_p = pl.REC["z_a"], pl.REC["s0"], pl.REC["d_p"]
    tab = pl.plunger_table()
    items, L = parts(z_a, s0, d_p)
    f = frames(z_a, s0, d_p, tab)
    mu = pl.MU[1]
    fric = pl.friction_plunger_N(mu) * pl.kinematics(0.0, d_p, z_a, s0)["ratio"][0] / pl.G * 1e3
    write_html(items, L, f, os.path.join(pl.OUT_FIG, "assembly_3d.html"), pl.min_preload_gf(mu, d_p, z_a, s0), fric)
    render_png(items, L, f, z_a, d_p, os.path.join(pl.OUT_FIG, "assembly_3d.png"))


if __name__ == "__main__":
    main()
