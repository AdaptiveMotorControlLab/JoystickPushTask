-- FEMM 4.2 axisymmetric model: Ledex 195224-230 (STA 20 x 40 mm pull, 60 deg plunger)
-- attracting a steel target (default: five stacked M3 washers, 3.2 x 9 x 0.8 mm, mild steel)
-- placed on the axis in front of the protruding pull end.
--
-- Published (datasheet pages F18/F34, drawing in the energised = seated state; the shared values are in
-- ledex_geometry.py): body 19.56 mm dia x 39.37 mm; M14 x 1.5 boss 9.52 mm long on the plunger side;
-- plunger 7.82 mm dia, pull end 19.05 + 4.76 = 23.81 mm beyond the body face; 2.5 mm wide x 9.5 mm
-- deep slot and 2.5/2.6 mm cross hole at the pull end; plunger mass 20.1 g; 1491 turns (30 AWG, 20.7 ohm).
-- Measured: coil current per AO command (Checkpoint 4).
-- Derived: plunger length (and so the seat position) from the plunger mass.
-- Calibrated against the datasheet force-stroke curves (see calibrate.py): seat gap, radial
-- clearance, steel saturation scale, end-plate thickness, case wall, cone angle. Their defaults
-- below are the best-fit values.
--
-- Coordinates: r = radius, z = axis; z = 0 is the front face of the case body (boss side), the
-- body is at z > 0, the boss at -LBOSS < z < 0, the plunger tip at z = -(PROTRUDE + STROKE).
--
-- Globals set by the caller before dofile() (see femm_run.py):
--   MODE = "forces" | "profile" | "stroke" | "map" | "sweep" | "fieldgrid" | "plunger"
--   paths: OUT, RES, TMP; overrides: any default(...) below
-- FEMM crashes when saving several bitmaps in one session, so each map is its own run.

function default(name, value)
  if getglobal(name) == nil then setglobal(name, value) end
end

default("OUT", "C:/Users/Mathis_Lab_1/Documents/JoystickPushTask/simulations/ledex_femm/")
default("RES", OUT .. "results/femm/")
default("TMP", "C:/Users/Mathis_Lab_1/AppData/Local/Temp/ledex_femm/model.fem")

-- command volts and the coil current measured at that command (0.58 A = rated, needs Imax raised)
VOLTS = {1, 2, 5, 10, 0}
AMPS  = {0.074, 0.106, 0.180, 0.310, 0.58}
NI = 5
GAPS = {1, 2, 3, 5}
NG = 4
TURNS = 1491

-- published geometry (mm); femm_run.py passes these from ledex_geometry.py (the defaults are the same values)
default("PROTRUDE", 23.81)  -- seated pull end beyond the body face (19.05 + 4.76)
default("STROKE", 0)        -- plunger held out from its seat, mm (0 = fully seated)
default("PMASS", 20.1)      -- plunger mass, g (sets the plunger length)
default("RP", 3.91)         -- plunger radius (7.82 mm dia)
default("RO", 9.78)         -- case outer radius (19.56 mm dia)
default("LEN", 39.37)       -- case body length
default("LBOSS", 9.52)      -- M14 boss length, plunger side
RBOSS = 6.6                 -- M14 x 1.5 boss, mean of major and minor radius
default("RTIP", 1.0)        -- radius of the flat at the cone apex (assumed)
-- tip slot (2.5 wide x 9.5 deep across the diameter) and cross hole (2.55 dia, 4.76 from the tip, through both
-- cheeks); axisymmetric stand-ins: the slot as an axial hole of the same cross-section (SLOTR, 0 = no slot), the
-- cross hole as an outer groove of the same width and volume (HOLER, 0 = no groove)
default("SLOTW", 2.5)
default("SLOTD", 9.5)
default("SLOTR", sqrt(SLOTW * 2 * sqrt(RP * RP - SLOTW * SLOTW / 4) / 3.14159265))
default("HOLED", 2.55)
default("HOLEZ", 4.76)
default("HOLER", sqrt(RP * RP - (HOLED / 2) * (HOLED / 2) * (2 * RP - SLOTW) / HOLED))
-- unpublished, calibrated against the datasheet force-stroke curves (results/calibration/)
default("CONEA", 37.52)     -- cone half-angle from the axis, degrees (uncalibrated guess was 30)
default("SEAT", 1.0)        -- axial gap between plunger cone and stop (built-in spacer), mm
default("BSCALE", 0.984)    -- B multiplier on the 1010 steel B-H curve (saturation level)
default("TPL", 1.579)       -- end-plate thickness, mm
default("WALL", 0.8)        -- case wall thickness, mm
default("CLR", 0.8)         -- radial non-magnetic gap plunger to bore (nylon bearing), mm
default("BOB", 0.5)         -- bobbin wall, mm (assumed)
default("STEEL", "1010 Steel")   -- base B-H curve for the solenoid steel
default("TSTEEL", "1010 Steel")  -- target steel (not scaled)
default("MESHW", 0.15)      -- mesh size in the target, mm
default("MESHP", 0.4)       -- mesh size in the plunger, mm
default("WRI", 1.6)         -- target inner radius (0 = solid disc)
default("WRO", 4.5)         -- target outer radius
default("WT", 4.0)          -- target thickness (five washers x 0.8 mm)
default("RA", 130)          -- radius of the open boundary

RB  = RP + CLR      -- bore radius
RKI = RO - WALL     -- case inner radius
RCI = RB + BOB      -- coil inner radius
RCO = RKI - 0.1     -- coil outer radius

-- plunger length from its mass: cylinder + cone, minus slot and cross hole (FEMM trig is in radians)
CONEL = (RP - RTIP) / tan(CONEA * 3.14159265 / 180)
VCONE = 3.14159265 / 3 * CONEL * (RP * RP + RP * RTIP + RTIP * RTIP)
VSLOT = SLOTW * 2 * sqrt(RP * RP - SLOTW * SLOTW / 4) * SLOTD
VHOLE = 3.14159265 * (HOLED / 2) * (HOLED / 2) * (2 * RP - SLOTW)
LCYL = (PMASS / 7.85e-3 - VCONE + VSLOT + VHOLE) / (3.14159265 * RP * RP)
default("ZCONE", -PROTRUDE + LCYL)   -- where the plunger cone starts (seated)

ZT0 = -PROTRUDE
ZAPEX0 = ZCONE + CONEL
function setstroke(s)
  STROKE = s
  ZT = ZT0 - s
  ZCP = ZCONE - s
  ZAPEX = ZAPEX0 - s
end
setstroke(STROKE)
STROKES = {0, 1.5, 3.2, 6.4, 9.5}
NS = 5

-- 1010 steel B-H curve from the FEMM library (B in T, H in A/m); B is scaled by BSCALE
BH_B = {0, 0.211862, 0.265665, 0.332377, 0.414377, 0.513811, 0.631899, 0.767784, 0.917018,
  1.070353, 1.214255, 1.334637, 1.422981, 1.480634, 1.517214, 1.544515, 1.571296, 1.602049,
  1.638404, 1.68049, 1.727311, 1.776659, 1.825401, 1.870557, 1.910809, 1.947222, 1.982328,
  2.018252, 2.055398, 2.092545, 2.128095, 2.161612, 2.194644, 2.230339, 2.272386, 2.324282,
  2.389356, 2.471238}
BH_H = {0, 79.577472, 100.182101, 126.121793, 158.77793, 199.889571, 251.646061, 316.80362,
  398.832128, 502.099901, 632.106325, 795.774715, 1001.821011, 1261.217929, 1587.779301,
  1998.89571, 2516.460605, 3168.036204, 3988.321282, 5020.999013, 6321.06325, 7957.747155,
  10018.210114, 12612.179293, 15877.79301, 19988.957103, 25164.606052, 31680.362037,
  39883.212823, 50209.990127, 63210.632497, 79577.471546, 100182.101136, 126121.792926,
  158777.930096, 199889.57103, 251646.060522, 316803.62037}

function add_solenoid_steel()
  if STEEL == "1010 Steel" then
    SSTEEL = "Ledex steel"
    mi_addmaterial(SSTEEL, 902.6, 902.6, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    for k = 1, getn(BH_B) do
      mi_addbhpoint(SSTEEL, BH_B[k] * BSCALE, BH_H[k])
    end
  else
    SSTEEL = STEEL
    mi_getmaterial(STEEL)
  end
end

function seg(x1, y1, x2, y2)
  mi_addnode(x1, y1)
  mi_addnode(x2, y2)
  mi_addsegment(x1, y1, x2, y2)
end

function label(x, y, mat, meshsize, circ, turns, group)
  mi_addblocklabel(x, y)
  mi_selectlabel(x, y)
  if meshsize > 0 then
    mi_setblockprop(mat, 0, meshsize, circ, 0, group, turns)
  else
    mi_setblockprop(mat, 1, 0, circ, 0, group, turns)
  end
  mi_clearselected()
end

function sortnum(t)
  local n = getn(t)
  for i = 2, n do
    local v = t[i]
    local j = i - 1
    while j >= 1 and t[j] > v do
      t[j + 1] = t[j]
      j = j - 1
    end
    t[j + 1] = v
  end
end

-- gap < 0 means no target
function build(gap, amps)
  newdocument(0)
  mi_probdef(0, "millimeters", "axi", 1e-8, 0, 30)
  mi_getmaterial("Air")
  mi_getmaterial("Copper")
  mi_getmaterial(TSTEEL)
  if STEEL == TSTEEL and STEEL ~= "1010 Steel" then
    SSTEEL = STEEL
  else
    add_solenoid_steel()
  end
  mi_addcircprop("coil", amps, 1)

  -- case wall + rear plate + stop with conical recess (one steel body)
  local zs = ZCONE + SEAT
  local za = ZAPEX0 + SEAT
  seg(0, za, RTIP, za)
  seg(RTIP, za, RP, zs)
  seg(RP, zs, RB, zs)
  seg(RB, zs, RB, LEN - TPL)
  seg(RB, LEN - TPL, RKI, LEN - TPL)
  seg(RKI, LEN - TPL, RKI, TPL)
  seg(RKI, TPL, RO, TPL)
  seg(RO, TPL, RO, LEN)
  seg(RO, LEN, 0, LEN)

  -- front plate with the boss on the plunger side (one steel body)
  seg(RO, TPL, RO, 0)
  seg(RO, 0, RBOSS, 0)
  seg(RBOSS, 0, RBOSS, -LBOSS)
  seg(RBOSS, -LBOSS, RB, -LBOSS)
  seg(RB, -LBOSS, RB, TPL)
  seg(RB, TPL, RKI, TPL)

  -- coil
  seg(RCI, TPL + 0.1, RCO, TPL + 0.1)
  seg(RCO, TPL + 0.1, RCO, LEN - TPL - 0.1)
  seg(RCO, LEN - TPL - 0.1, RCI, LEN - TPL - 0.1)
  seg(RCI, LEN - TPL - 0.1, RCI, TPL + 0.1)

  -- plunger: cylinder (with the tip slot as an axial hole) then the cone
  local axis = {-RA, ZAPEX, za, LEN, RA}
  if SLOTR > 0 then
    seg(SLOTR, ZT, RP, ZT)
    seg(SLOTR, ZT, SLOTR, ZT + SLOTD)
    seg(SLOTR, ZT + SLOTD, 0, ZT + SLOTD)
    tinsert(axis, ZT + SLOTD)
  else
    seg(0, ZT, RP, ZT)
    tinsert(axis, ZT)
  end
  if HOLER > 0 and HOLER < RP then
    local g1 = ZT + HOLEZ - HOLED / 2
    local g2 = ZT + HOLEZ + HOLED / 2
    seg(RP, ZT, RP, g1)
    seg(RP, g1, HOLER, g1)
    seg(HOLER, g1, HOLER, g2)
    seg(HOLER, g2, RP, g2)
    seg(RP, g2, RP, ZCP)
  else
    seg(RP, ZT, RP, ZCP)
  end
  seg(RP, ZCP, RTIP, ZAPEX)
  seg(RTIP, ZAPEX, 0, ZAPEX)

  -- target (ring, or solid disc when WRI = 0)
  if gap >= 0 then
    local w1 = ZT - gap - WT
    local w2 = ZT - gap
    seg(WRI, w1, WRO, w1)
    seg(WRO, w1, WRO, w2)
    seg(WRO, w2, WRI, w2)
    seg(WRI, w2, WRI, w1)
    if WRI == 0 then
      tinsert(axis, w1)
      tinsert(axis, w2)
    end
  end

  -- symmetry axis between all axis nodes, then the open boundary
  sortnum(axis)
  for k = 1, getn(axis) - 1 do
    if axis[k + 1] > axis[k] then seg(0, axis[k], 0, axis[k + 1]) end
  end
  mi_makeABC(7, RA, 0, 0, 0)

  label(RA / 2, 0, "Air", 0, "<None>", 0, 0)
  label((RKI + RO) / 2, LEN / 2, SSTEEL, 0, "<None>", 0, 1)
  label((RB + RBOSS) / 2, -LBOSS / 2, SSTEEL, 0, "<None>", 0, 1)
  label((RCI + RCO) / 2, LEN / 2, "Copper", 0, "coil", TURNS, 3)
  label(RP * 0.75, ZCP - 2, SSTEEL, MESHP, "<None>", 0, 4)
  if gap >= 0 then
    label((WRI + WRO) / 2, ZT - gap - WT / 2, TSTEEL, MESHW, "<None>", 0, 2)
  end

  mi_saveas(TMP)
end

function solve(amps)
  mi_modifycircprop("coil", 1, amps)
  mi_analyze(1)
  mi_loadsolution()
end

function bmag(x, y)
  local A, B1, B2 = mo_getpointvalues(x, y)
  return sqrt(B1 * B1 + B2 * B2)
end

function fz_block(x, y)
  mo_clearblock()
  mo_selectblock(x, y)
  local f = mo_blockintegral(19)
  mo_clearblock()
  return f
end

function target_force(gap)
  return fz_block((WRI + WRO) / 2, ZT - gap - WT / 2)
end

function plunger_force()
  return fz_block(RP * 0.75, ZCP - 2)   -- positive = pulled into the body (toward +z)
end

function paramcols()
  return format("%g,%g,%g,%g,%g,%g,%s,%g", PROTRUDE, SEAT, STROKE, BSCALE, TPL, WALL, STEEL, MESHW)
end

if MODE == "forces" then
  fh = openfile(RES .. "femm_forces_5washers_coaxial.csv", "w")
  write(fh, "gap_mm,command_V,current_A,washer_force_N,washer_force_g,plunger_force_N\n")
  flush(fh)
  for g = 1, NG do
    build(GAPS[g], AMPS[1])
    for i = 1, NI do
      solve(AMPS[i])
      local fw = target_force(GAPS[g])
      local fp = plunger_force()
      write(fh, format("%g,%g,%.3f,%.5f,%.3f,%.4f\n", GAPS[g], VOLTS[i], AMPS[i], fw, fw / 9.81 * 1000, fp))
      flush(fh)
      mo_close()
    end
    mi_close()
  end
  closefile(fh)
end

if MODE == "profile" then
  build(-1, AMPS[1])
  prof = {}
  for i = 1, NI do
    solve(AMPS[i])
    prof[i] = {}
    for k = 0, 40 do
      prof[i][k] = bmag(RP, ZT - 0.05 - k * 0.5)  -- along the plunger outer edge (r = RP), not the slotted axis
    end
    mo_close()
  end
  mi_close()
  fh = openfile(RES .. "femm_field_along_plunger_edge_no_target.csv", "w")
  write(fh, "distance_from_tip_mm")
  for i = 1, NI do write(fh, format(",B_T_at_%.3fA", AMPS[i])) end
  write(fh, "\n")
  for k = 0, 40 do
    write(fh, format("%.2f", 0.05 + k * 0.5))
    for i = 1, NI do write(fh, format(",%.5f", prof[i][k])) end
    write(fh, "\n")
  end
  closefile(fh)
end

if MODE == "stroke" then
  -- plunger held out from its seat; washer stack 2 mm in front of the (moved) tip
  local gap = 2
  local idx = {1, 4, 5}
  fh = openfile(RES .. "femm_stroke_5washers_coaxial.csv", "w")
  write(fh, "stroke_mm,command_V,current_A,washer_force_N,washer_force_g,plunger_force_N\n")
  flush(fh)
  for s = 1, NS do
    setstroke(STROKES[s])
    build(gap, AMPS[1])
    for j = 1, 3 do
      local i = idx[j]
      solve(AMPS[i])
      local fw = target_force(gap)
      local fp = plunger_force()
      write(fh, format("%g,%g,%.3f,%.5f,%.3f,%.4f\n", STROKES[s], VOLTS[i], AMPS[i], fw, fw / 9.81 * 1000, fp))
      flush(fh)
      mo_close()
    end
    mi_close()
  end
  closefile(fh)
end

-- generic sweep: CASE, TARGET (labels), GAPLIST/NGAP, AMPLIST/NAMP, appends to OUTFILE
if MODE == "sweep" then
  fh = openfile(OUTFILE, "a")
  for g = 1, NGAP do
    build(GAPLIST[g], AMPLIST[1])
    for i = 1, NAMP do
      solve(AMPLIST[i])
      local fw = target_force(GAPLIST[g])
      local fp = plunger_force()
      write(fh, format("%s,%s,%g,%g,%g,%s,%g,%.4f,%.6f,%.4f,%.4f,%g,%g\n",
        CASE, TARGET, WRI * 2, WRO * 2, WT, paramcols(),
        GAPLIST[g], AMPLIST[i], fw, fw / 9.81 * 1000, fp, CLR, CONEA))
      flush(fh)
      mo_close()
    end
    mi_close()
  end
  closefile(fh)
end

-- plunger force only (no target): STROKELIST/NSTROKE x AMPLIST/NAMP, appends TAG rows to OUTFILE
if MODE == "plunger" then
  fh = openfile(OUTFILE, "a")
  for s = 1, NSTROKE do
    setstroke(STROKELIST[s])
    build(-1, AMPLIST[1])
    for i = 1, NAMP do
      solve(AMPLIST[i])
      write(fh, format("%s,%s,%g,%.4f,%.5f\n", TAG, paramcols(), STROKELIST[s], AMPLIST[i], plunger_force()))
      flush(fh)
      mo_close()
    end
    mi_close()
  end
  closefile(fh)
end

-- field on a regular r-z grid: GRIDGAP (-1 = no target), GRIDAMPS -> GRIDFILE
if MODE == "fieldgrid" then
  default("GZ0", -45)
  default("GNZ", 200)
  default("GNR", 80)
  build(GRIDGAP, GRIDAMPS)
  solve(GRIDAMPS)
  fh = openfile(GRIDFILE, "w")
  write(fh, "r_mm,z_mm,Br_T,Bz_T,Bmag_T\n")
  for iz = 0, GNZ do
    local z = GZ0 + iz * 0.25
    for ir = 0, GNR do
      local r = ir * 0.25
      if r == 0 then r = 0.001 end
      local A, B1, B2 = mo_getpointvalues(r, z)
      write(fh, format("%.2f,%.2f,%.5g,%.5g,%.5g\n", ir * 0.25, z, B1, B2, sqrt(B1 * B1 + B2 * B2)))
    end
  end
  closefile(fh)
  mo_close()
  mi_close()
end

if MODE == "map" then
  main_resize(900, 1000)
  build(MAPGAP, MAPAMPS)
  solve(MAPAMPS)
  mo_showdensityplot(1, 0, MAPBMAX, 0, "bmag")
  mo_zoom(0, ZT - 12, 21.6, 4)
  mo_savebitmap(MAPFILE)
  mo_close()
  mi_close()
end

quit()
