"""Narrow cube handle: the same handle cut from 20 mm to 11.5 mm wide (11.5 x 11.5 x 10 mm).

Between x = -7 and +7 the original is a plain extrusion along x (only the three shaft holes at x = 0 break it), so
the two rounded ends (x beyond +-7, 3 mm corner radius) are moved 4.25 mm inward each and the middle is kept to
+-2.75 mm. Push face, depth, height, edge fillets and the three holes (3.2 mm, y 0.55 / 4.25 / 7.95) are unchanged.

Run with a venv that has netgen-mesher and numpy:  python make_cube_11p5.py
Writes joystick_handle_cube_11p5.step/.stl next to the original.
"""
import os
import sys

import numpy as np
from netgen.occ import OCCGeometry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ledex-holder-adjustable"))
import make_ledex_holder as mh  # noqa: E402

SRC = os.path.join(HERE, "joystick_handle_cube.step")
OUT = os.path.join(HERE, "joystick_handle_cube_11p5")
WIDTH = 11.5
END = 7.0                       # the rounded ends start at |x| = END
SHIFT = (20.0 - WIDTH) / 2


def volume(T):
    return np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6


def main():
    src = OCCGeometry(SRC).shape
    keep = END - SHIFT
    left = (src * mh.box(-11, -END, -3, 12, -3, 10)).Move((SHIFT, 0, 0))
    right = (src * mh.box(END, 11, -3, 12, -3, 10)).Move((-SHIFT, 0, 0))
    middle = src * mh.box(-keep, keep, -3, 12, -3, 10)
    shape = (left + middle + right)
    shape.WriteStep(OUT + ".step")
    T = mh.triangles(shape, 0.5)
    mh.write_stl(OUT + ".stl", T)
    P = T.reshape(-1, 3)
    print("{}: {} solid(s), {} triangles, extent {} to {} mm, volume {:.0f} mm3 (original {:.0f})".format(
        os.path.basename(OUT), len(shape.solids), len(T), P.min(0).round(2), P.max(0).round(2), volume(T),
        volume(mh.triangles(src, 0.5))))


if __name__ == "__main__":
    main()
