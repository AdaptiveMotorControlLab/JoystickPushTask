"""Metal joystick shaft (reference model, not printed): replaces the printed 89 mm PLA shaft, which bent under load.

    /tmp/ngenv/bin/python make_joystick_metal.py      # writes joystick_metal_80mm.step/.stl next to this file

Measured with calipers (26 Nov 2026): 1.6 g, non-magnetic; base 6.35 mm diameter x 8 mm; a smooth transition 2.5 mm
tall into a 2.74 mm arm; 80 mm from the base bottom to the top of the rounded tip. The transition is drawn as a
concave arc from the base's top edge, tangent to the arm 2.5 mm higher (radius 2.63 mm): a true R2.5 fillet would
need a 2.5 mm shoulder and the base only leaves 1.8 mm. The tip is a hemisphere. The mounting screw in the base is not
modelled; with it the shaft stands 1 mm higher on the thumbstick stub than the printed shaft did
(simulations/ledex_femm/rig_geometry.py, SHAFT_LIFT).

Frame: z up the axis from the base bottom, axis at x = y = 0 (same as the printed shaft's STL).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

MASS_G = 1.6
BASE_R, BASE_H = 6.35 / 2, 8.0
ARM_R = 2.74 / 2
TRANSITION_H = 2.5
LENGTH = 80.0
NAME = "joystick_metal_80mm"


def transition_arc():
    """Centre (r, z) and radius of the concave arc from (BASE_R, BASE_H) tangent to the arm at BASE_H + TRANSITION_H."""
    w, h = BASE_R - ARM_R, TRANSITION_H
    R = (w ** 2 + h ** 2) / (2 * w)
    return (ARM_R + R, BASE_H + h), R


def profile(n=24):
    """(r, z) outline points, for rig_geometry's shaft_radius (base, sampled arc, arm, tip)."""
    (cr, cz), R = transition_arc()
    a0, a1 = np.arctan2(BASE_H - cz, BASE_R - cr), -np.pi
    pts = [(BASE_R, 0.0), (BASE_R, BASE_H)]
    pts += [(cr + R * np.cos(a), cz + R * np.sin(a)) for a in np.linspace(a0, a1, n)[1:]]
    tip0 = LENGTH - ARM_R
    pts += [(ARM_R, tip0)] + [(ARM_R * np.cos(a), tip0 + ARM_R * np.sin(a)) for a in np.linspace(0, np.pi / 2, 9)[1:]]
    return [(round(float(r), 4), round(float(z), 4)) for r, z in pts]


def shaft():
    from netgen.occ import ArcOfCircle, Axis, Face, Pnt, Segment, Wire, Z
    (cr, cz), R = transition_arc()
    am = (np.arctan2(BASE_H - cz, BASE_R - cr) - np.pi) / 2
    tip0 = LENGTH - ARM_R
    P = lambda r, z: Pnt(r, 0, z)
    edges = [
        Segment(P(0, 0), P(BASE_R, 0)),
        Segment(P(BASE_R, 0), P(BASE_R, BASE_H)),
        ArcOfCircle(P(BASE_R, BASE_H), P(cr + R * np.cos(am), cz + R * np.sin(am)), P(ARM_R, cz)),
        Segment(P(ARM_R, cz), P(ARM_R, tip0)),
        ArcOfCircle(P(ARM_R, tip0), P(ARM_R * np.cos(np.pi / 4), tip0 + ARM_R * np.sin(np.pi / 4)), P(0, LENGTH)),
        Segment(P(0, LENGTH), P(0, 0)),
    ]
    return Face(Wire(edges)).Revolve(Axis(Pnt(0, 0, 0), Z), 360)


def main():
    sys.path.insert(0, os.path.join(HERE, "..", "ledex-holder-adjustable"))
    import make_ledex_holder as mh
    s = shaft()
    s.WriteStep(os.path.join(HERE, NAME + ".step"))
    T = mh.triangles(s, 0.4)
    mh.write_stl(os.path.join(HERE, NAME + ".stl"), T)
    bb = T.reshape(-1, 3)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
    (_, _), R = transition_arc()
    print("{:24s} {:6d} tris  size {} mm".format(NAME, len(T), np.round(bb.max(0) - bb.min(0), 2)))
    print("volume {:.1f} mm^3, mass {} g -> {:.2f} g/cm^3 (aluminium 2.70); transition arc R {:.3f} mm".format(
        vol, MASS_G, MASS_G / vol * 1e3, R))


if __name__ == "__main__":
    main()
