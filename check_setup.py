"""
==============================================================================
 SMARTMIX ENVIRONMENT & DEPENDENCY VERIFICATION DOCTOR
==============================================================================
Checks whether all required tools, Python packages, and audio libraries are
correctly installed and configured on your computer.

Usage:
  python check_setup.py
==============================================================================
"""

import sys
import os
import subprocess
from pathlib import Path

def print_status(component, success, details="", fix_hint=""):
    mark = "[OK]" if success else "[FAIL]"
    print(f" {mark:7s} {component}")
    if details:
        print(f"         Details: {details}")
    if not success and fix_hint:
        print(f"         -> Action needed: {fix_hint}")

def main():
    print("=" * 78)
    print(" SMARTMIX SYSTEM SETUP & ENVIRONMENT VERIFICATION")
    print("=" * 78)
    all_ok = True

    # 1. Check Python Version
    py_ver = sys.version_info
    py_ok = (py_ver.major == 3 and py_ver.minor >= 10)
    ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    print_status(
        "Python Runtime (>= 3.10)",
        py_ok,
        f"Detected Python {ver_str} at {sys.executable}",
        "Install Python 3.10+ from https://python.org or run 'winget install Python.Python.3.12'"
    )
    if not py_ok:
        all_ok = False

    # 2. Check NumPy
    np_ok = False
    try:
        import numpy as np
        np_ok = True
        print_status("NumPy Library", True, f"Version {np.__version__}")
    except ImportError:
        print_status(
            "NumPy Library",
            False,
            "Module 'numpy' not found",
            "Run 'pip install numpy' or 'pip install -r requirements.txt'"
        )
        all_ok = False

    # 3. Check SciPy
    sp_ok = False
    try:
        import scipy
        import scipy.signal
        import scipy.io.wavfile
        sp_ok = True
        print_status("SciPy DSP Library", True, f"Version {scipy.__version__}")
    except ImportError:
        print_status(
            "SciPy DSP Library",
            False,
            "Module 'scipy' not found",
            "Run 'pip install scipy' or 'pip install -r requirements.txt'"
        )
        all_ok = False

    # 4. Check FFmpeg Binary & Essential Audio Filters
    ffmpeg_ok = False
    filters_ok = False
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if res.returncode == 0:
            ffmpeg_ok = True
            first_line = res.stdout.splitlines()[0] if res.stdout else "Available"
            print_status("FFmpeg Binary in System PATH", True, first_line)

            # Check for loudnorm & atempo filters
            res_filt = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
            filt_out = res_filt.stdout or ""
            has_loudnorm = "loudnorm" in filt_out
            has_atempo = "atempo" in filt_out

            if has_loudnorm and has_atempo:
                filters_ok = True
                print_status("FFmpeg Audio Filters", True, "loudnorm (EBU R128) & atempo (time-stretch) supported")
            else:
                missing = []
                if not has_loudnorm: missing.append("loudnorm")
                if not has_atempo: missing.append("atempo")
                print_status(
                    "FFmpeg Audio Filters",
                    False,
                    f"Missing filters: {', '.join(missing)}",
                    "Install a complete FFmpeg build: run 'winget install Gyan.FFmpeg'"
                )
                all_ok = False
    except FileNotFoundError:
        print_status(
            "FFmpeg Binary in System PATH",
            False,
            "Executable 'ffmpeg' was not found in system PATH",
            "Install FFmpeg by opening PowerShell and running: 'winget install Gyan.FFmpeg' (then restart terminal)"
        )
        all_ok = False

    # 5. Check VirtualDJ Data Files
    local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    vdj_dir = Path(local_appdata) / "VirtualDJ"
    vdj_folder = vdj_dir / "Sideview" / "automix.vdjfolder"
    vdj_db = vdj_dir / "database.xml"

    vdj_installed = vdj_dir.exists()
    print_status(
        "VirtualDJ Directory",
        vdj_installed,
        f"Located at {vdj_dir}" if vdj_installed else f"Not found at {vdj_dir}",
        "Download and install VirtualDJ from https://www.virtualdj.com"
    )

    if vdj_installed:
        db_ok = vdj_db.exists()
        print_status(
            "VirtualDJ Track Database",
            db_ok,
            str(vdj_db) if db_ok else "database.xml not found yet",
            "Open VirtualDJ and add/scan songs so database.xml is populated"
        )

        folder_ok = vdj_folder.exists()
        print_status(
            "VirtualDJ Automix Queue",
            folder_ok,
            str(vdj_folder) if folder_ok else "automix.vdjfolder not found yet",
            "In VirtualDJ, go to Sideview -> Automix and drag your songs into the playlist"
        )
        if not db_ok or not folder_ok:
            all_ok = False
    else:
        all_ok = False

    # Summary
    print("-" * 78)
    if all_ok:
        print(" ALL DEPENDENCIES VERIFIED! Your computer is 100% ready to run SmartMix.")
        print(" To compile your mixtape, simply run:")
        print("     run_smartmix.bat   (or: python smartmix.py)")
    else:
        print(" ACTION REQUIRED: Please review the missing items above.")
        print(" Quick install commands:")
        print("   1. Python dependencies : pip install -r requirements.txt")
        print("   2. FFmpeg installation : winget install Gyan.FFmpeg")
    print("=" * 78)

if __name__ == "__main__":
    main()
