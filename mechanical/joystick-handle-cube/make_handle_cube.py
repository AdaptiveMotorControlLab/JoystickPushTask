"""Narrow rounded-cube push handle (11.5 mm wide). Needs cadquery.

Coordinates match the earlier exports: x across the cube, y along the push axis, z vertical with the bottom face
at z = -1.5. Three blind holes open in the bottom face for the shaft (front hole = y 0.55, nearest the mouse).
Each hole is a cylinder with a hemispherical (ball-end) tip; "depth" below is to the tip apex.

    python make_handle_cube.py                 # writes the current revision (h15p1, d3.3, depth 4.2)
    python make_handle_cube.py --check-old     # rebuilds h14p1 (d3.2, depth 3.2) and compares to its archived STEP
"""
import os
import sys
import cadquery as cq

ARCHIVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "archive", "joystick-handle-cube")

W, Y0, Y1, Z0 = 11.5, -1.5, 10.0, -1.5
R_CORNER, R_TOP, R_BOTTOM = 3.0, 2.5, 0.1
HOLE_Y = (0.55, 4.25, 7.95)


def hole_tool(y, d, depth):
    r = d / 2
    zc = Z0 + depth - r
    return (cq.Workplane("XZ").moveTo(0, Z0 - 1).lineTo(r, Z0 - 1).lineTo(r, zc)
            .threePointArc((r * 0.7071067811865476, zc + r * 0.7071067811865476), (0, zc + r)).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)).translate((0, y, 0)))


def build(height, hole_d, hole_depth):
    L = Y1 - Y0
    b = (cq.Workplane("XY").workplane(offset=Z0).center(0, (Y0 + Y1) / 2)
         .rect(W, L).extrude(height))
    b = b.edges("|Z").fillet(R_CORNER)
    b = b.faces("<Z").edges().fillet(R_BOTTOM)
    b = b.faces(">Z").edges().fillet(R_TOP)
    for y in HOLE_Y:
        b = b.cut(hole_tool(y, hole_d, hole_depth))
    return b


if __name__ == "__main__":
    if "--check-old" in sys.argv:
        old = cq.importers.importStep(os.path.join(ARCHIVE, "joystick_handle_cube_11p5_h14p1.step")).val()
        new = build(14.1, 3.2, 3.2).val()
        print("old", old.Volume(), "rebuild", new.Volume(),
              "old-new", old.cut(new).Volume(), "new-old", new.cut(old).Volume())
        sys.exit()
    name = "joystick_handle_cube_11p5_h15p1_d3p3_dp4p2"
    s = build(15.1, 3.3, 4.2)
    print("volume", s.val().Volume())
    cq.exporters.export(s, name + ".step")
    cq.exporters.export(s, name + ".stl", tolerance=0.005, angularTolerance=0.05)
