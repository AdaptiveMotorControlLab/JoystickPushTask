"""Constrainer revision for the Ledex plunger link: the home-wall arch becomes a straight window up to the ceiling.

The original arch (16 mm wide, round top at world Z 63.41) leaves ~1 mm over the plunger at the link height and
~1.4 mm at the ends of the plunger pin. The window keeps the width and squares the top off at the cavity ceiling
(the top plate and its 1D slot are untouched).

Run with the NGSolve venv:  /tmp/ngenv/bin/python make_ledex_window.py
Writes joystick_1d_axis_constrainer_38x38x56_ledex_window.step/.stl next to the original.
"""
import os
import sys

import numpy as np
from netgen.occ import OCCGeometry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ledex-holder-adjustable"))
import make_ledex_holder as mh  # noqa: E402
import rig_geometry as rg  # noqa: E402

SRC = os.path.join(HERE, "joystick_1d_axis_constrainer_38x38x56.step")
OUT = os.path.join(HERE, rg.CON_WINDOW_FILE)


def window_cut():
    """Window box in the part's own frame: part y = world X (push), part x = -world Y, part z = world Z - CON_Z0."""
    x0, x1 = -rg.CON_OUTER - 0.5, -rg.CON_INNER + 0.5
    return mh.box(-rg.ARCH_HALF_W, rg.ARCH_HALF_W, x0, x1, rg.ARCH_SPRING - rg.CON_Z0, rg.WINDOW_TOP - rg.CON_Z0)


def main():
    shape = OCCGeometry(SRC).shape - window_cut()
    shape.WriteStep(OUT + ".step")
    T = mh.triangles(shape, 1.0)
    mh.write_stl(OUT + ".stl", T)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
    T0 = mh.triangles(OCCGeometry(SRC).shape, 1.0)
    vol0 = np.einsum("ij,ij->i", T0[:, 0], np.cross(T0[:, 1], T0[:, 2])).sum() / 6
    print("{}: {} triangles, volume {:.0f} mm3 (original {:.0f}, removed {:.0f})".format(
        os.path.basename(OUT), len(T), vol, vol0, vol0 - vol))


if __name__ == "__main__":
    main()
