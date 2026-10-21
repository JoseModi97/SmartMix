# SmartMix One-Click Uninstaller for VirtualDJ 8.5+
param(
    [switch]$KeepDatabase
)

$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host "   SMARTMIX NATIVE VIRTUALDJ EXTENSION -- UNINSTALLER      " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow

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
    Write-Host "[!] VirtualDJ directory not found. Nothing to remove." -ForegroundColor Yellow
    exit 0
}

# 1. Close VirtualDJ if running
$vjdProc = Get-Process -Name "*virtualdj*" -ErrorAction SilentlyContinue
if ($vjdProc) {
    Write-Host "[*] Closing VirtualDJ process..." -ForegroundColor Cyan
    Stop-Process -Name "*virtualdj*" -Force
    Start-Sleep -Seconds 2
}

# 2. Remove Plugin DLLs
$autoDll = Join-Path $targetRoot "Plugins64\AutoStart\SmartMix64.dll"
$soundDll = Join-Path $targetRoot "Plugins64\SoundEffect\SmartMix64.dll"

if (Test-Path $autoDll) {
    Remove-Item $autoDll -Force
    Write-Host "[-] Removed: $autoDll" -ForegroundColor Green
}
if (Test-Path $soundDll) {
    Remove-Item $soundDll -Force
    Write-Host "[-] Removed: $soundDll" -ForegroundColor Green
}

# 3. Remove Skins
$skinZip = Join-Path $targetRoot "Skins\SmartMix.zip"
$skinFolder = Join-Path $targetRoot "Skins\SmartMix"

if (Test-Path $skinZip) {
    Remove-Item $skinZip -Force
    Write-Host "[-] Removed: $skinZip" -ForegroundColor Green
}
if (Test-Path $skinFolder) {
    Remove-Item $skinFolder -Recurse -Force
    Write-Host "[-] Removed: $skinFolder" -ForegroundColor Green
}

# 4. Handle Database
$dbPath = Join-Path $targetRoot "smartmix.db"
if (Test-Path $dbPath) {
    if ($KeepDatabase) {
        Write-Host "[i] Retained user playlist database: $dbPath" -ForegroundColor Yellow
    } else {
        $backupDb = Join-Path $targetRoot "smartmix.db.backup"
        Copy-Item $dbPath -Destination $backupDb -Force
        Remove-Item $dbPath -Force
        Write-Host "[-] Removed: $dbPath (Archived backup to $backupDb)" -ForegroundColor Green
    }
}

# 5. Restore Default Skin in settings.xml if active
$settingsPath = Join-Path $targetRoot "settings.xml"
if (Test-Path $settingsPath) {
    $settingsXml = Get-Content $settingsPath -Raw
    if ($settingsXml -match "SmartMix:Essentials") {
        $restoredXml = $settingsXml.Replace("SmartMix:Essentials", "Default:Essentials")
        Set-Content -Path $settingsPath -Value $restoredXml -Encoding UTF8
        Write-Host "[+] Reset active skin in settings.xml back to Default:Essentials." -ForegroundColor Green
    }
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   UNINSTALL COMPLETE!                                    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "VirtualDJ was cleanly restored to its original state." -ForegroundColor White
Write-Host "Your music library, native Automix, and hot cues remain completely intact." -ForegroundColor White
