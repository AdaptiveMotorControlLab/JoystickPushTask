-- FEMM 4.2 axisymmetric model: Ledex 195224-230 (STA 20 x 40 mm pull, 60 deg plunger)
-- attracting a steel target (default: five stacked M3 washers, 3.2 x 9 x 0.8 mm, mild steel)
-- placed on the axis in front of the protruding pull end.
--
-- Published: body 19.56 mm dia x 39.37 mm, M14 boss 9.52 mm, plunger 7.82 mm dia,
-- 1491 turns (30 AWG, 20.7 ohm). Measured: coil current per AO command (Checkpoint 4).
-- ASSUMED (not published): case wall and end-plate thickness, bobbin size, stop/cone
-- geometry, residual seat gap, plunger protrusion, steel grade.
--
-- Coordinates: r = radius, z = axis; z = 0 is the front (open) face of the case, the body
-- is at z > 0, the plunger tip is at z = -(PROTRUDE + STROKE), the target is below it.
--
-- Globals set by the caller before dofile() (see run_femm.ps1 / run_sweeps.ps1):
--   MODE = "forces" | "profile" | "stroke" | "map" | "sweep" | "fieldgrid"
--   optional overrides: PROTRUDE, SEAT, STROKE, STEEL, MESHW, WRI, WRO, WT
-- FEMM crashes when saving several bitmaps in one session, so each map is its own run.

OUT = "C:/Users/Mathis_Lab_1/Documents/JoystickPushTask/simulations/ledex_femm/"
RES = OUT .. "results/"
TMP = "C:/Users/Mathis_Lab_1/AppData/Local/Temp/ledex_femm/model.fem"

function default(name, value)
  if getglobal(name) == nil then setglobal(name, value) end
end

-- command volts and the coil current measured at that command (0.58 A = rated, needs Imax raised)
VOLTS = {1, 2, 5, 10, 0}
AMPS  = {0.074, 0.106, 0.180, 0.310, 0.58}
NI = 5
GAPS = {1, 2, 3, 5}
NG = 4
TURNS = 1491

default("PROTRUDE", 9.5)    -- plunger pull end beyond the front face when seated, mm (assumed)
default("SEAT", 0.1)        -- residual axial gap between plunger cone and stop, mm (assumed)
default("STROKE", 0)        -- plunger held out from its seat, mm (0 = fully seated)
default("STEEL", "1010 Steel")
default("MESHW", 0.15)      -- mesh size in the target, mm
default("WRI", 1.6)         -- target inner radius (0 = solid disc)
default("WRO", 4.5)         -- target outer radius
default("WT", 4.0)          -- target thickness (five washers x 0.8 mm)

RP   = 3.91         -- plunger radius (published 7.82 mm dia)
RB   = 4.06         -- bore radius (plunger clearance / bobbin inner)
RCI  = 4.56         -- coil inner radius
RCO  = 8.18         -- coil outer radius
RKI  = 8.28         -- case inner radius
RO   = 9.78         -- case outer radius (published 19.56 mm dia)
RBOSS = 7.0         -- M14 boss radius
TPL  = 2.5          -- end-plate thickness
LEN  = 39.37        -- case length (published)
LBOSS = 9.52        -- boss length (published)
ZCONE = 26.0        -- where the plunger cone starts (seated)
RTIP = 1.0          -- radius of the flat at the cone apex

ZT0 = -PROTRUDE
ZAPEX0 = ZCONE + (RP - RTIP) / 0.57735   -- 30 deg half-angle cone
function setstroke(s)
  STROKE = s
  ZT = ZT0 - s
  ZCP = ZCONE - s
  ZAPEX = ZAPEX0 - s
end
setstroke(STROKE)
STROKES = {0, 1.5, 3.2, 6.4, 9.5}
NS = 5

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

-- gap < 0 means no target
function build(gap, amps)
  newdocument(0)
  mi_probdef(0, "millimeters", "axi", 1e-8, 0, 30)
  mi_getmaterial("Air")
  mi_getmaterial(STEEL)
  mi_getmaterial("Copper")
  mi_addcircprop("coil", amps, 1)

  -- case shell + rear plate + boss + stop with conical recess (one steel body)
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
  seg(RO, LEN, RBOSS, LEN)
  seg(RBOSS, LEN, RBOSS, LEN + LBOSS)
  seg(RBOSS, LEN + LBOSS, 0, LEN + LBOSS)
  seg(0, LEN + LBOSS, 0, za)

  -- front plate (open end) with the plunger bore
  seg(RO, TPL, RO, 0)
  seg(RO, 0, RB, 0)
  seg(RB, 0, RB, TPL)
  seg(RB, TPL, RKI, TPL)

  -- coil
  seg(RCI, TPL + 0.1, RCO, TPL + 0.1)
  seg(RCO, TPL + 0.1, RCO, LEN - TPL - 0.1)
  seg(RCO, LEN - TPL - 0.1, RCI, LEN - TPL - 0.1)
  seg(RCI, LEN - TPL - 0.1, RCI, TPL + 0.1)

  -- plunger: cylinder then 30 deg half-angle cone
  seg(0, ZT, RP, ZT)
  seg(RP, ZT, RP, ZCP)
  seg(RP, ZCP, RTIP, ZAPEX)
  seg(RTIP, ZAPEX, 0, ZAPEX)
  seg(0, ZAPEX, 0, ZT)
  seg(0, ZAPEX, 0, za)

  -- target (ring, or solid disc when WRI = 0) and the axis below the plunger
  if gap >= 0 then
    local w1 = ZT - gap - WT
    local w2 = ZT - gap
    seg(WRI, w1, WRO, w1)
    seg(WRO, w1, WRO, w2)
    seg(WRO, w2, WRI, w2)
    seg(WRI, w2, WRI, w1)
    if WRI == 0 then
      seg(0, -55, 0, w1)
      seg(0, w2, 0, ZT)
    else
      seg(0, -55, 0, ZT)
    end
  else
    seg(0, -55, 0, ZT)
  end

  seg(0, LEN + LBOSS, 0, 85)
  mi_makeABC(7, 70, 0, 15, 0)

  label(30, 0, "Air", 0, "<None>", 0, 0)
  label((RKI + RO) / 2, LEN / 2, STEEL, 0, "<None>", 0, 1)
  label((RB + RO) / 2, TPL / 2, STEEL, 0, "<None>", 0, 1)
  label((RCI + RCO) / 2, LEN / 2, "Copper", 0, "coil", TURNS, 3)
  label(RP / 2, 5, STEEL, 0.4, "<None>", 0, 4)
  if gap >= 0 then
    label((WRI + WRO) / 2, ZT - gap - WT / 2, STEEL, MESHW, "<None>", 0, 2)
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

if MODE == "forces" then
  fh = openfile(RES .. "forces.csv", "w")
  write(fh, "gap_mm,command_V,current_A,washer_force_N,washer_force_g,plunger_force_N\n")
  flush(fh)
  for g = 1, NG do
    build(GAPS[g], AMPS[1])
    for i = 1, NI do
      solve(AMPS[i])
      local fw = target_force(GAPS[g])
      local fp = fz_block(RP / 2, 5)
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
      prof[i][k] = bmag(0.001, ZT - 0.05 - k * 0.5)
    end
    mo_close()
  end
  mi_close()
  fh = openfile(RES .. "axial_B.csv", "w")
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
  fh = openfile(RES .. "stroke.csv", "w")
  write(fh, "stroke_mm,command_V,current_A,washer_force_N,washer_force_g,plunger_force_N\n")
  flush(fh)
  for s = 1, NS do
    setstroke(STROKES[s])
    build(gap, AMPS[1])
    for j = 1, 3 do
      local i = idx[j]
      solve(AMPS[i])
      local fw = target_force(gap)
      local fp = fz_block(RP / 2, 5)
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
      local fp = fz_block(RP / 2, 5)
      write(fh, format("%s,%s,%g,%g,%g,%g,%g,%g,%s,%g,%g,%.4f,%.6f,%.4f,%.4f\n",
        CASE, TARGET, WRI * 2, WRO * 2, WT, PROTRUDE, SEAT, STROKE, STEEL, MESHW,
        GAPLIST[g], AMPLIST[i], fw, fw / 9.81 * 1000, fp))
      flush(fh)
      mo_close()
    end
    mi_close()
  end
  closefile(fh)
end

-- field on a regular r-z grid: GRIDGAP (-1 = no target), GRIDAMPS -> GRIDFILE
if MODE == "fieldgrid" then
  build(GRIDGAP, GRIDAMPS)
  solve(GRIDAMPS)
  fh = openfile(GRIDFILE, "w")
  write(fh, "r_mm,z_mm,Br_T,Bz_T,Bmag_T\n")
  for iz = 0, 120 do
    local z = -25 + iz * 0.25
    for ir = 0, 80 do
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
  mo_zoom(0, -20, 21.6, 4)
  mo_savebitmap(MAPFILE)
  mo_close()
  mi_close()
end

quit()
