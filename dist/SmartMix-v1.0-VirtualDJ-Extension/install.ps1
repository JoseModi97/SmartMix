# SmartMix One-Click Installer for VirtualDJ 8.5+
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SMARTMIX NATIVE VIRTUALDJ EXTENSION -- INSTALLER        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Locate VirtualDJ Root
$vjdRoots = @(
    "$env:LOCALAPPDATA\VirtualDJ",
    "$env:USERPROFILE\Documents\VirtualDJ",
    "$env:USERPROFILE\OneDrive\Documents\VirtualDJ"
)

$targetRoot = $null
foreach ($r in $vjdRoots) {
    if (Test-Path $r) {
        $targetRoot = $r
        break
    }
}

if (-not $targetRoot) {
    Write-Error "Could not locate VirtualDJ directory. Please ensure VirtualDJ 8.5+ is installed."
    exit 1
}

Write-Host "[+] Found VirtualDJ data root: $targetRoot" -ForegroundColor Green

# 2. Check if VirtualDJ is currently running
$vjdProc = Get-Process -Name "*virtualdj*" -ErrorAction SilentlyContinue
if ($vjdProc) {
    Write-Warning "VirtualDJ is currently running. Please close VirtualDJ before installation."
    if (-not $Force) {
        $ans = Read-Host "Would you like the installer to close VirtualDJ now? (y/n)"
        if ($ans -eq 'y') {
            Stop-Process -Name "*virtualdj*" -Force
            Start-Sleep -Seconds 2
        } else {
            Write-Host "Installation aborted. Close VirtualDJ and run again." -ForegroundColor Red
            exit 1
        }
    } else {
        Stop-Process -Name "*virtualdj*" -Force
        Start-Sleep -Seconds 2
    }
}

# 3. Deploy C++ Plugin DLLs
$autoStartDir = Join-Path $targetRoot "Plugins64\AutoStart"
$soundFxDir = Join-Path $targetRoot "Plugins64\SoundEffect"
New-Item -ItemType Directory -Force -Path $autoStartDir | Out-Null
New-Item -ItemType Directory -Force -Path $soundFxDir | Out-Null

$srcDll = Join-Path $scriptDir "SmartMix64.dll"
if (Test-Path $srcDll) {
    Copy-Item $srcDll -Destination (Join-Path $autoStartDir "SmartMix64.dll") -Force
    Copy-Item $srcDll -Destination (Join-Path $soundFxDir "SmartMix64.dll") -Force
    Write-Host "[+] Installed SmartMix64.dll to AutoStart and SoundEffect." -ForegroundColor Green
} else {
    Write-Error "SmartMix64.dll not found in installer directory: $srcDll"
}

# 4. Deploy Skin
$skinsDir = Join-Path $targetRoot "Skins"
New-Item -ItemType Directory -Force -Path $skinsDir | Out-Null

$srcSkinZip = Join-Path $scriptDir "SmartMix.zip"
$srcSkinFolder = Join-Path $scriptDir "SmartMix"

if (Test-Path $srcSkinZip) {
    Copy-Item $srcSkinZip -Destination (Join-Path $skinsDir "SmartMix.zip") -Force
    Write-Host "[+] Installed SmartMix.zip skin package." -ForegroundColor Green
}

if (Test-Path $srcSkinFolder) {
    $destSkinFolder = Join-Path $skinsDir "SmartMix"
    New-Item -ItemType Directory -Force -Path $destSkinFolder | Out-Null
    Copy-Item "$srcSkinFolder\*" -Destination $destSkinFolder -Recurse -Force
    Write-Host "[+] Installed SmartMix unpacked skin directory." -ForegroundColor Green
}

# 5. Deploy Database (Preserve existing if user already has playlists)
$destDb = Join-Path $targetRoot "smartmix.db"
$srcDb = Join-Path $scriptDir "smartmix.db"
if (Test-Path $srcDb) {
    if (-not (Test-Path $destDb)) {
        Copy-Item $srcDb -Destination $destDb -Force
        Write-Host "[+] Initialized local SQLite playlist database: smartmix.db" -ForegroundColor Green
    } else {
        Write-Host "[i] Preserved existing user smartmix.db database." -ForegroundColor Yellow
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   INSTALLATION COMPLETE!                                " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Launch VirtualDJ." -ForegroundColor White
Write-Host "2. Go to Settings (gear icon) -> Interface." -ForegroundColor White
Write-Host "3. Under Skins, select SmartMix." -ForegroundColor White
Write-Host "4. Look at the SideView tabs in your browser:" -ForegroundColor White
Write-Host "   Sidelist | Remixes | Sampler | Automix | SmartMix | Karaoke" -ForegroundColor Yellow
Write-Host "5. Click SmartMix to access the exact cue transition arranger." -ForegroundColor White
