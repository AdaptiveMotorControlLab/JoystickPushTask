# Parameter sweeps and raw field grids for the Ledex + steel-target FEMM model.
# Writes results/sweeps.csv (long format, one row per solve) and results/fieldgrid_*.csv.
# One FEMM session per job, so a crash loses at most one job. Re-running appends to
# sweeps.csv; delete it first for a clean run. -Only <regex> runs matching job names.
param([string]$Only = ".*", [switch]$NoGrids)

$femm = "C:\femm42\bin\femm.exe"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$main = (Join-Path $here "ledex_washer.lua") -replace '\\', '/'
$res = Join-Path $here "results"
$tmp = Join-Path $env:LOCALAPPDATA "Temp\ledex_femm"
New-Item -ItemType Directory -Force -Path $tmp, $res | Out-Null
$sweeps = Join-Path $res "sweeps.csv"
if (-not (Test-Path $sweeps)) {
    Set-Content -Path $sweeps -Encoding ASCII -Value "case,target,target_id_mm,target_od_mm,target_t_mm,protrude_mm,seat_mm,stroke_mm,steel,target_mesh_mm,gap_mm,current_A,target_force_N,target_force_g,plunger_force_N"
}

function Invoke-Femm([string]$preamble, [string]$name) {
    $wrapper = Join-Path $tmp "$name.lua"
    Set-Content -Path $wrapper -Encoding ASCII -Value ($preamble + "`ndofile(`"$main`")`n")
    $t0 = Get-Date
    $p = Start-Process -FilePath $femm -ArgumentList "-lua-script=`"$wrapper`"" -PassThru
    if (-not $p.WaitForExit(1800000)) { $p.Kill(); "{0}: TIMEOUT" -f $name; return }
    "{0}: exit {1}, {2:N0} s" -f $name, $p.ExitCode, ((Get-Date) - $t0).TotalSeconds
}

function LuaList($values) { "{" + (($values | ForEach-Object { $_.ToString([Globalization.CultureInfo]::InvariantCulture) }) -join ", ") + "}" }

function Sweep([string]$case, [string]$target, [hashtable]$over, $gaps, $amps) {
    if ($case -notmatch $Only) { return }
    $lines = @("MODE = `"sweep`"", "CASE = `"$case`"", "TARGET = `"$target`"",
        "OUTFILE = `"$($sweeps -replace '\\', '/')`"",
        "GAPLIST = $(LuaList $gaps)", "NGAP = $($gaps.Count)",
        "AMPLIST = $(LuaList $amps)", "NAMP = $($amps.Count)")
    foreach ($k in $over.Keys) {
        $v = $over[$k]
        if ($v -is [string]) { $lines += "$k = `"$v`"" } else { $lines += "$k = $($v.ToString([Globalization.CultureInfo]::InvariantCulture))" }
    }
    Invoke-Femm ($lines -join "`n") $case
}

# measured coil currents (A): 0.5, 1, 2, 3, 4, 5, 6, 8, 10 V, plus 0.4/0.5/0.58 A if Imax is raised
$ampsFine = @(0.053, 0.074, 0.106, 0.121, 0.147, 0.180, 0.201, 0.273, 0.310, 0.40, 0.50, 0.58)
$ampsKey = @(0.074, 0.106, 0.180, 0.310, 0.58)
$ampsSens = @(0.074, 0.310, 0.58)
$gapsFine = @(0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
$gapsKey = @(1, 2, 3, 5)

# 1) baseline: five M3 washers, plunger seated, fine gap x current grid (one session per gap)
foreach ($g in $gapsFine) {
    Sweep ("baseline_gap{0}" -f $g) "washers5_M3" @{} @($g) $ampsFine
}

# 2) alternative targets (all mild steel, plunger seated)
Sweep "target_washers1" "washers1_M3" @{ WRI = 1.6; WRO = 4.5; WT = 0.8 } $gapsKey $ampsKey
Sweep "target_washers3" "washers3_M3" @{ WRI = 1.6; WRO = 4.5; WT = 2.4 } $gapsKey $ampsKey
Sweep "target_disc8x4" "disc_8x4_solid" @{ WRI = 0; WRO = 3.91; WT = 4.0 } $gapsKey $ampsKey
Sweep "target_disc9x4" "disc_9x4_solid" @{ WRI = 0; WRO = 4.5; WT = 4.0 } $gapsKey $ampsKey
Sweep "target_disc12x4" "disc_12x4_solid" @{ WRI = 0; WRO = 6.0; WT = 4.0 } $gapsKey $ampsKey
Sweep "target_disc16x6" "disc_16x6_solid" @{ WRI = 0; WRO = 8.0; WT = 6.0 } $gapsKey $ampsKey

# 3) plunger held out from its seat (needs a stop), washers 2 mm from the moved tip
foreach ($s in @(0.5, 1, 1.5, 2, 3.2, 4.8, 6.4, 9.5)) {
    Sweep ("stroke_{0}mm" -f $s) "washers5_M3" @{ STROKE = $s } @(2) $ampsKey
}

# 4) sensitivity to the assumed / numerical parameters (washers 2 mm, seated)
Sweep "sens_reference" "washers5_M3" @{} @(2) $ampsSens
Sweep "sens_protrude6.35" "washers5_M3" @{ PROTRUDE = 6.35 } @(2) $ampsSens
Sweep "sens_protrude12.7" "washers5_M3" @{ PROTRUDE = 12.7 } @(2) $ampsSens
Sweep "sens_seat0.05" "washers5_M3" @{ SEAT = 0.05 } @(2) $ampsSens
Sweep "sens_seat0.2" "washers5_M3" @{ SEAT = 0.2 } @(2) $ampsSens
Sweep "sens_steel1018" "washers5_M3" @{ STEEL = "1018 Steel" } @(2) $ampsSens
Sweep "sens_pureiron" "washers5_M3" @{ STEEL = "Pure Iron" } @(2) $ampsSens
Sweep "sens_mesh0.3" "washers5_M3" @{ MESHW = 0.3 } @(2) $ampsSens
Sweep "sens_mesh0.075" "washers5_M3" @{ MESHW = 0.075 } @(2) $ampsSens

# 5) raw field grids (r 0-20 mm, z -25..5 mm, 0.25 mm step) for re-plotting
if (-not $NoGrids) {
    $grids = @()
    foreach ($a in $ampsKey) { $grids += , @(-1, $a, ("fieldgrid_notarget_{0:0.000}A" -f $a)) }
    foreach ($a in $ampsKey) { $grids += , @(2, $a, ("fieldgrid_washers5_gap2mm_{0:0.000}A" -f $a)) }
    foreach ($a in @(0.310, 0.58)) { $grids += , @(1, $a, ("fieldgrid_washers5_gap1mm_{0:0.000}A" -f $a)) }
    foreach ($gr in $grids) {
        if ($gr[2] -notmatch $Only) { continue }
        $file = (Join-Path $res ($gr[2] + ".csv")) -replace '\\', '/'
        $pre = "MODE = `"fieldgrid`"`nGRIDGAP = {0}`nGRIDAMPS = {1}`nGRIDFILE = `"{2}`"" -f $gr[0], $gr[1].ToString([Globalization.CultureInfo]::InvariantCulture), $file
        Invoke-Femm $pre $gr[2]
    }
}
