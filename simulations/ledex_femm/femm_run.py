"""Run the Ledex FEMM model (ledex_washer.lua) natively on Windows or through Wine on macOS/Linux.

Stdlib only, Python 3.6+. One FEMM session per job; jobs run in parallel, each writing its own
temporary CSV, which is merged afterwards (a crash loses at most one job).

    python femm_run.py sweeps [--only REGEX] [--no-grids]   # results/sweeps.csv + results/fieldgrid_*.csv
    python femm_run.py summary                              # results/forces.csv, stroke.csv, axial_B.csv
    python femm_run.py maps                                 # FEMM screenshots in figures/plots/femm/

FEMM location: C:\\femm42\\bin\\femm.exe on Windows. Elsewhere set FEMM_WINE (path to the wine
binary) and WINEPREFIX; the defaults match the Mac install described in README.md.
Model parameters not given explicitly use the defaults in ledex_washer.lua (the calibrated values).
"""
import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "ledex_washer.lua")
RES = os.path.join(HERE, "results")
FEMM_DIR = os.path.join(HERE, "figures", "plots", "femm")
WINDOWS = sys.platform.startswith("win")

WINE = os.environ.get("FEMM_WINE", os.path.expanduser(
    "~/Applications/wine/Wine Staging.app/Contents/Resources/wine/bin/wine"))
PREFIX = os.environ.get("WINEPREFIX", os.path.expanduser("~/.wine-femm"))
FEMM_EXE = r"C:\femm42\bin\femm.exe"
WORKERS = int(os.environ.get("FEMM_WORKERS", "8" if not WINDOWS else "4"))

SWEEP_HEADER = ("case,target,target_id_mm,target_od_mm,target_t_mm,protrude_mm,seat_mm,stroke_mm,bscale,"
                "tpl_mm,wall_mm,steel,target_mesh_mm,gap_mm,current_A,target_force_N,target_force_g,"
                "plunger_force_N,clr_mm,conea_deg")
PLUNGER_HEADER = "tag,protrude_mm,seat_mm,stroke_mm,bscale,tpl_mm,wall_mm,steel,target_mesh_mm,stroke,current_A,plunger_force_N"

# measured coil currents (A): 0.5, 1, 2, 3, 4, 5, 6, 8, 10 V, plus 0.4/0.5/0.58 A if Imax is raised
AMPS_FINE = [0.053, 0.074, 0.106, 0.121, 0.147, 0.180, 0.201, 0.273, 0.310, 0.40, 0.50, 0.58]
AMPS_KEY = [0.074, 0.106, 0.180, 0.310, 0.58]
AMPS_SENS = [0.074, 0.310, 0.58]
GAPS_FINE = [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]
GAPS_KEY = [1, 2, 3, 5]


def femm_path(path):
    """Absolute path as FEMM sees it (forward slashes; Z: drive under Wine)."""
    path = os.path.abspath(path)
    if WINDOWS:
        return path.replace("\\", "/")
    return "Z:" + os.path.realpath(path)


def lua_value(v):
    if isinstance(v, str):
        return '"{}"'.format(v)
    if isinstance(v, (list, tuple)):
        return "{" + ", ".join(lua_value(x) for x in v) + "}"
    return repr(float(v)) if isinstance(v, float) else str(v)


def run_lua(globals_, name, timeout=1800, hide=True):
    """Run ledex_washer.lua once with the given globals. Returns True if FEMM exited in time.
    Bitmap export needs a visible window (hide=False), at least under Wine."""
    tmp = tempfile.mkdtemp(prefix="ledex_femm_")
    try:
        g = dict(globals_)
        g.setdefault("TMP", femm_path(os.path.join(tmp, "model.fem")))
        g.setdefault("OUT", femm_path(HERE) + "/")
        g.setdefault("RES", femm_path(RES) + "/")
        lines = ["{} = {}".format(k, lua_value(v)) for k, v in g.items()]
        lines.append('dofile("{}")'.format(femm_path(MAIN)))
        wrapper = os.path.join(tmp, name + ".lua")
        with open(wrapper, "w") as f:
            f.write("\n".join(lines) + "\n")
        script = "-lua-script=" + (wrapper if WINDOWS else femm_path(wrapper))
        cmd = [FEMM_EXE, script] + (["-windowhide"] if hide else [])
        env = None
        if not WINDOWS:
            cmd = [WINE] + cmd
            env = dict(os.environ, WINEPREFIX=PREFIX, WINEDEBUG="-all")
        try:
            subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            print("{}: TIMEOUT".format(name))
            return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _job_file():
    d = os.path.join(tempfile.gettempdir(), "ledex_femm_out")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, uuid.uuid4().hex + ".csv")


def _read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = [line.rstrip("\n") for line in f if line.strip()]
    os.remove(path)
    return rows


def plunger_job(params, strokes, amps, tag="fit"):
    """Plunger force (N, toward the seat) for each stroke x current. Returns rows of PLUNGER_HEADER."""
    out = _job_file()
    g = dict(params, MODE="plunger", TAG=tag, OUTFILE=femm_path(out),
             STROKELIST=list(strokes), NSTROKE=len(strokes), AMPLIST=list(amps), NAMP=len(amps))
    run_lua(g, "plunger_" + tag, timeout=600)
    return _read_rows(out)


def plunger_forces(params, strokes, amps, tag="fit", workers=None):
    """Parallel over strokes. Returns {(stroke, current): force_N}."""
    with ThreadPoolExecutor(workers or WORKERS) as ex:
        parts = list(ex.map(lambda s: plunger_job(params, [s], amps, tag), strokes))
    res = {}
    for rows in parts:
        for line in rows:
            p = line.split(",")
            res[(float(p[9]), round(float(p[10]), 4))] = float(p[11])
    return res


def sweep_job(case, target, over, gaps, amps):
    out = _job_file()
    g = dict(over, MODE="sweep", CASE=case, TARGET=target, OUTFILE=femm_path(out),
             GAPLIST=list(gaps), NGAP=len(gaps), AMPLIST=list(amps), NAMP=len(amps))
    run_lua(g, case, timeout=900)
    rows = _read_rows(out)
    print("{}: {} rows".format(case, len(rows)))
    return rows


def fieldgrid_job(gap, amps, path, over=None):
    g = dict(over or {}, MODE="fieldgrid", GRIDGAP=gap, GRIDAMPS=amps, GRIDFILE=femm_path(path))
    run_lua(g, os.path.splitext(os.path.basename(path))[0])
    print("wrote", os.path.relpath(path, HERE))


def sweep_jobs(over=None):
    """The standard sweep set (same cases as the original run_sweeps.ps1)."""
    o = dict(over or {})
    jobs = []
    for g in GAPS_FINE:
        jobs.append(("baseline_gap{:g}".format(g), "washers5_M3", o, [g], AMPS_FINE))
    targets = [("target_washers1", "washers1_M3", dict(WRI=1.6, WRO=4.5, WT=0.8)),
               ("target_washers3", "washers3_M3", dict(WRI=1.6, WRO=4.5, WT=2.4)),
               ("target_washers10", "washers10_M3", dict(WRI=1.6, WRO=4.5, WT=8.0)),
               ("target_washers20", "washers20_M3", dict(WRI=1.6, WRO=4.5, WT=16.0)),
               ("target_washers40", "washers40_M3", dict(WRI=1.6, WRO=4.5, WT=32.0)),
               ("target_disc8x4", "disc_8x4_solid", dict(WRI=0, WRO=3.91, WT=4.0)),
               ("target_disc9x4", "disc_9x4_solid", dict(WRI=0, WRO=4.5, WT=4.0)),
               ("target_disc12x4", "disc_12x4_solid", dict(WRI=0, WRO=6.0, WT=4.0)),
               ("target_disc16x6", "disc_16x6_solid", dict(WRI=0, WRO=8.0, WT=6.0))]
    for case, name, t in targets:
        jobs.append((case, name, dict(o, **t), GAPS_KEY, AMPS_KEY))
    for s in [0.5, 1, 1.5, 2, 3.2, 4.8, 6.4, 9.5]:
        jobs.append(("stroke_{:g}mm".format(s), "washers5_M3", dict(o, STROKE=s), [2], AMPS_KEY))
    sens = [("sens_reference", {}),
            ("sens_protrude23.51", dict(PROTRUDE=23.51)), ("sens_protrude24.11", dict(PROTRUDE=24.11)),
            ("sens_noslot", dict(SLOTR=0)),
            ("sens_steel1018", dict(STEEL="1018 Steel")), ("sens_pureiron", dict(STEEL="Pure Iron")),
            ("sens_mesh0.3", dict(MESHW=0.3)), ("sens_mesh0.075", dict(MESHW=0.075)),
            ("sens_plungermesh0.2", dict(MESHP=0.2))]
    for case, s in sens:
        jobs.append((case, "washers5_M3", dict(o, **s), [2], AMPS_SENS))
    return jobs


def run_sweeps(only=".*", grids=True, over=None, outfile=None):
    outfile = outfile or os.path.join(RES, "sweeps.csv")
    jobs = [j for j in sweep_jobs(over) if re.search(only, j[0])]
    with ThreadPoolExecutor(WORKERS) as ex:
        parts = list(ex.map(lambda j: sweep_job(*j), jobs))
    new = not os.path.exists(outfile)
    with open(outfile, "a") as f:
        if new:
            f.write(SWEEP_HEADER + "\n")
        for rows in parts:
            for line in rows:
                f.write(line + "\n")
    print("appended to", os.path.relpath(outfile, HERE))
    if not grids:
        return
    grid_jobs = []
    for a in AMPS_KEY:
        grid_jobs.append((-1, a, "fieldgrid_notarget_{:.3f}A".format(a)))
        grid_jobs.append((2, a, "fieldgrid_washers5_gap2mm_{:.3f}A".format(a)))
    for a in [0.310, 0.58]:
        grid_jobs.append((1, a, "fieldgrid_washers5_gap1mm_{:.3f}A".format(a)))
    grid_jobs = [j for j in grid_jobs if re.search(only, j[2])]
    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(lambda j: fieldgrid_job(j[0], j[1], os.path.join(RES, j[2] + ".csv"), over), grid_jobs))


def run_summary(over=None):
    jobs = [dict(over or {}, MODE=m) for m in ("forces", "profile", "stroke")]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda g: run_lua(g, g["MODE"]), jobs))
    print("wrote results/forces.csv, axial_B.csv, stroke.csv")


def run_maps(over=None):
    """FEMM density-plot screenshots (BMP via FEMM, converted to PNG with Pillow if available)."""
    os.makedirs(FEMM_DIR, exist_ok=True)
    maps = [(-1, 0.074, "field_nowasher_1V_0.074A"), (-1, 0.106, "field_nowasher_2V_0.106A"),
            (-1, 0.180, "field_nowasher_5V_0.180A"), (-1, 0.310, "field_nowasher_10V_0.310A"),
            (-1, 0.580, "field_nowasher_rated_0.580A"), (2, 0.074, "washer_gap2mm_1V_0.074A"),
            (2, 0.310, "washer_gap2mm_10V_0.310A"), (2, 0.580, "washer_gap2mm_rated_0.580A")]
    tmp = tempfile.mkdtemp(prefix="ledex_maps_")
    for gap, amps, name in maps:   # sequential: FEMM bitmap export is fragile
        bmp = os.path.join(tmp, name + ".bmp")
        run_lua(dict(over or {}, MODE="map", MAPGAP=gap, MAPAMPS=amps, MAPBMAX=0.05, MAPFILE=femm_path(bmp)), name, hide=False)
        if os.path.exists(bmp):
            try:
                from PIL import Image
                Image.open(bmp).save(os.path.join(FEMM_DIR, name + ".png"))
                print("wrote", name + ".png")
            except ImportError:
                shutil.copy(bmp, os.path.join(FEMM_DIR, name + ".bmp"))
        else:
            print(name + ": no bitmap written")
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("what", choices=["sweeps", "summary", "maps"])
    p.add_argument("--only", default=".*", help="regex on job names (sweeps)")
    p.add_argument("--no-grids", action="store_true")
    a = p.parse_args()
    if a.what == "sweeps":
        run_sweeps(a.only, not a.no_grids)
    elif a.what == "summary":
        run_summary()
    else:
        run_maps()


if __name__ == "__main__":
    main()
