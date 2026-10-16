"""Ledex 195224-230 body and plunger geometry, shared by every model of the solenoid.

Used by the reference CAD (mechanical/3d-print/ledex-holder-adjustable/make_ledex_holder.py), the rig model
(rig_geometry.py), FEMM (femm_run.py passes femm_globals() to ledex_washer.lua) and the 3D model (fea3d.py).
Stdlib only, so it also runs under the rig PC's Python 3.6.

From the datasheet drawing (page F34, energised = seated): case 19.56 x 39.37 mm, M14 x 1.5 boss 9.52 mm long,
plunger 7.82 mm dia and 20.1 g, pull end 19.05 + 4.76 = 23.81 mm beyond the body face; tip slot 2.5 +-0.3 wide and
9.5 +-0.3 deep across the whole diameter; cross hole 2.5/2.6 mm through both cheeks, 4.76 +-0.30 from the tip, at
right angles to the slot plane. The 60 deg cone (half-angle, apex flat) is the FEMM calibration
(results/calibration/best_params.json); the plunger length follows from its mass. The internals (seat gap, bore
clearance, plates, case wall, steel) are fitted in the magnetic models only.
"""
import math

LEDEX = dict(case_r=9.78, case_len=39.37, boss_r=7.0, boss_len=9.52, plunger_r=3.91, protrude=23.81,
             tip_slot_w=2.5, tip_slot_d=9.5, hole_from_tip=4.76, hole_d=2.55, plunger_g=20.1,
             cone_half_deg=37.52, cone_flat_r=1.0, steel_g_mm3=7.85e-3)


def slot_area(L=LEDEX):
    """Cross-section (mm^2, normal to the axis) removed by the tip slot."""
    rp, w = L["plunger_r"], L["tip_slot_w"]
    return w * 2 * math.sqrt(rp * rp - (w / 2) ** 2)


def hole_volume(L=LEDEX):
    """Steel removed by the cross hole through both cheeks (mm^3)."""
    return math.pi * (L["hole_d"] / 2) ** 2 * (2 * L["plunger_r"] - L["tip_slot_w"])


def plunger_dims(L=LEDEX, cone_half_deg=None):
    """(cylinder length, cone length, total length) in mm, from the plunger mass."""
    rp, rt = L["plunger_r"], L["cone_flat_r"]
    conel = (rp - rt) / math.tan(math.radians(cone_half_deg or L["cone_half_deg"]))
    vcone = math.pi / 3 * conel * (rp * rp + rp * rt + rt * rt)
    lcyl = (L["plunger_g"] / L["steel_g_mm3"] - vcone + slot_area(L) * L["tip_slot_d"] + hole_volume(L)) \
        / (math.pi * rp * rp)
    return lcyl, conel, lcyl + conel


def axisym_tip(L=LEDEX):
    """Axisymmetric stand-ins for the tip (FEMM): the slot as an axial hole of the same cross-section, the cross hole
    as an outer groove of the same width and volume. Returns (slot hole radius, groove inner radius)."""
    rp = L["plunger_r"]
    groove = hole_volume(L) / L["hole_d"]
    return math.sqrt(slot_area(L) / math.pi), math.sqrt(rp * rp - groove / math.pi)


def femm_globals(L=LEDEX):
    """Plunger and case geometry for ledex_washer.lua (the calibrated internals keep their defaults there)."""
    slotr, holer = axisym_tip(L)
    return dict(PROTRUDE=L["protrude"], PMASS=L["plunger_g"], RP=L["plunger_r"], RTIP=L["cone_flat_r"],
                SLOTW=L["tip_slot_w"], SLOTD=L["tip_slot_d"], SLOTR=round(slotr, 4),
                HOLED=L["hole_d"], HOLEZ=L["hole_from_tip"], HOLER=round(holer, 4),
                RO=L["case_r"], LEN=L["case_len"], LBOSS=L["boss_len"])


if __name__ == "__main__":
    lcyl, conel, total = plunger_dims()
    slotr, holer = axisym_tip()
    print("plunger %.2f mm (cylinder %.2f + cone %.2f); slot %.2f mm^2 -> axial hole r %.3f; "
          "cross hole %.1f mm^3 -> groove r %.3f" % (total, lcyl, conel, slot_area(), slotr, hole_volume(), holer))
