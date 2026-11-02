"""Wide-window revision of the 1D-axis constrainer: almost the whole home (mouse-side) wall is open.

The earlier window revision (16 mm wide, now in archive/) kept 11 mm pillars on each side of the home wall. Here the
opening is as wide as the cavity (26 mm, the 6 mm side walls stay as full-thickness posts) and runs from the top of the
socket (part z 10, where the socket ring rests on the holder frame) up to the cavity ceiling (part z 53). The socket
ring below z 10 (3 mm wall) is closed again (the arch's opening there is filled) and the top plate with its 1D slot is
untouched.

Run with a venv that has ngsolve + numpy + scipy:  python make_wide_window.py
Source: the original arched part in archive/. Writes the STEP and STL next to this script.
"""
import os
import sys

import numpy as np
from netgen.occ import OCCGeometry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ledex-holder-adjustable"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "simulations", "ledex_femm"))
import make_ledex_holder as mh  # noqa: E402
import rig_geometry as rg  # noqa: E402

SRC = os.path.join(HERE, "..", "..", "archive", "joystick-1d-axis-constrainer",
                   "joystick_1d_axis_constrainer_38x38x56.step")
OUT = os.path.join(HERE, rg.CON_WINDOW_FILE)
ORIG_ARCH_HALF_W = 8.0   # the original arch (16 mm wide) also opens the 3 mm socket wall down to z 0


def window_cut():
    """Window box in the part's own frame: part y = world X (push), part x = -world Y, part z = world Z - CON_Z0."""
    y0, y1 = -rg.CON_OUTER - 0.5, -rg.CON_INNER + 0.5     # through the 6 mm home wall (0.5 mm overshoot, outside / into the cavity)
    return mh.box(-rg.ARCH_HALF_W, rg.ARCH_HALF_W, y0, y1, rg.ARCH_BOTTOM - rg.CON_Z0, rg.WINDOW_TOP - rg.CON_Z0)


def bottom_fill():
    """Closes the original arch's opening in the 3 mm socket wall (part z 0-10), below the window."""
    return mh.box(-ORIG_ARCH_HALF_W, ORIG_ARCH_HALF_W, -rg.CON_OUTER, -rg.CON_INNER_SOCKET,
                  0.0, rg.ARCH_BOTTOM - rg.CON_Z0)


def volume(shape):
    T = mh.triangles(shape, 1.0)
    return T, np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6


def main():
    src = OCCGeometry(SRC).shape
    shape = (src - window_cut()) + bottom_fill()
    shape.WriteStep(OUT + ".step")
    T, vol = volume(shape)
    mh.write_stl(OUT + ".stl", T)
    _, vol0 = volume(src)
    print("{}: {} triangles, volume {:.0f} mm3 (original arch {:.0f}, removed {:.0f})".format(
        os.path.basename(OUT), len(T), vol, vol0, vol0 - vol))


if __name__ == "__main__":
    main()
