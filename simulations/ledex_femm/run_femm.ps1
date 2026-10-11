# Runs ledex_washer.lua in FEMM 4.2 (C:\femm42): force sweep, axial field profile, then one
# FEMM session per field map (several bitmaps in one session crash FEMM). Maps are saved as PNG.
param([switch]$MapsOnly)

$femm = "C:\femm42\bin\femm.exe"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$main = (Join-Path $here "ledex_washer.lua") -replace '\\', '/'
$tmp = Join-Path $env:LOCALAPPDATA "Temp\ledex_femm"
New-Item -ItemType Directory -Force -Path $tmp, (Join-Path $here "figures") | Out-Null
Add-Type -AssemblyName System.Drawing

function Invoke-Femm([string]$preamble, [string]$name) {
    $wrapper = Join-Path $tmp "$name.lua"
    Set-Content -Path $wrapper -Encoding ASCII -Value ($preamble + "`ndofile(`"$main`")`n")
    $p = Start-Process -FilePath $femm -ArgumentList "-lua-script=`"$wrapper`"" -PassThru
    if (-not $p.WaitForExit(900000)) { $p.Kill(); throw "FEMM timed out on $name" }
    "{0}: exit {1}" -f $name, $p.ExitCode
}

if (-not $MapsOnly) {
    Invoke-Femm 'MODE = "forces"' "forces"
    Invoke-Femm 'MODE = "profile"' "profile"
    Invoke-Femm 'MODE = "stroke"' "stroke"
}

# gap (-1 = no washer), current (A), colour-scale maximum (T), output name
$maps = @(
    @(-1, 0.074, 0.05, "field_nowasher_1V_0.074A"),
    @(-1, 0.106, 0.05, "field_nowasher_2V_0.106A"),
    @(-1, 0.180, 0.05, "field_nowasher_5V_0.180A"),
    @(-1, 0.310, 0.05, "field_nowasher_10V_0.310A"),
    @(-1, 0.580, 0.05, "field_nowasher_rated_0.580A"),
    @(2, 0.074, 0.05, "washer_gap2mm_1V_0.074A"),
    @(2, 0.310, 0.05, "washer_gap2mm_10V_0.310A"),
    @(2, 0.580, 0.05, "washer_gap2mm_rated_0.580A")
)
foreach ($m in $maps) {
    $bmp = Join-Path $tmp ($m[3] + ".bmp")
    $pre = "MODE = `"map`"`nMAPGAP = {0}`nMAPAMPS = {1}`nMAPBMAX = {2}`nMAPFILE = `"{3}`"" -f $m[0], $m[1], $m[2], ($bmp -replace '\\', '/')
    Invoke-Femm $pre $m[3]
    if (Test-Path $bmp) {
        $img = [System.Drawing.Image]::FromFile($bmp)
        $img.Save((Join-Path $here ("figures\" + $m[3] + ".png")), [System.Drawing.Imaging.ImageFormat]::Png)
        $img.Dispose()
        Remove-Item $bmp
    }
}

# overview: top row no washer, bottom row washer stack 2 mm from the tip, same 0-0.05 T scale
$rows = @(
    @(@("field_nowasher_1V_0.074A", "1 V (0.074 A)"), @("field_nowasher_2V_0.106A", "2 V (0.106 A)"),
      @("field_nowasher_5V_0.180A", "5 V (0.180 A)"), @("field_nowasher_10V_0.310A", "10 V (0.310 A)"),
      @("field_nowasher_rated_0.580A", "rated 0.58 A (Imax raised)")),
    @(@("washer_gap2mm_1V_0.074A", "washers 2 mm, 1 V"), @("washer_gap2mm_10V_0.310A", "washers 2 mm, 10 V"),
      @("washer_gap2mm_rated_0.580A", "washers 2 mm, 0.58 A"))
)
$tw = 450; $th = 500; $cap = 40
$sheet = New-Object System.Drawing.Bitmap (5 * $tw), (2 * ($th + $cap))
$g = [System.Drawing.Graphics]::FromImage($sheet)
$g.Clear([System.Drawing.Color]::White)
$font = New-Object System.Drawing.Font "Segoe UI", 16
for ($r = 0; $r -lt $rows.Count; $r++) {
    for ($c = 0; $c -lt $rows[$r].Count; $c++) {
        $png = Join-Path $here ("figures\" + $rows[$r][$c][0] + ".png")
        if (-not (Test-Path $png)) { continue }
        $img = [System.Drawing.Image]::FromFile($png)
        $y = $r * ($th + $cap)
        $g.DrawString($rows[$r][$c][1], $font, [System.Drawing.Brushes]::Black, ($c * $tw + 8), ($y + 6))
        $g.DrawImage($img, ($c * $tw), ($y + $cap), $tw, $th)
        $img.Dispose()
    }
}
$g.Dispose()
$sheet.Save((Join-Path $here "figures\overview.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$sheet.Dispose()
