"""
==============================================================================
 SMARTMIX STUDIO: MODERN DESKTOP USER INTERFACE
==============================================================================
A sleek, modern dark-themed graphical interface for the SmartMix DJ mixtape
compilation engine.

Features:
  - Configure mix title and custom export destination folder
  - Live preview and refresh of VirtualDJ Automix queue & Cue markers
  - Choose transition style (Gradual Cue 2 -> Cue 3 DJ Crossfade)
  - Loudness targets and true-peak limiter controls
  - Real-time compilation progress bar and streamed terminal logs
  - 1-click 'Open in Explorer' and 'Play Mix' buttons upon completion
==============================================================================
"""

import os
import sys
import threading
import subprocess
from pathlib import Path

try:
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    ctk = None

import generate_mixtape as gm

# Set modern appearance if CustomTkinter is available
if ctk is not None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

class SmartMixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartMix Studio — DJ Continuous Mixtape Engine")
        self.root.geometry("980x820")
        self.root.minsize(860, 680)

        # Application state
        self.tracks = []
        self.compile_process = None
        self.is_compiling = False
        self.last_output_file = None

        # Build UI
        self._build_header()
        self._build_main_layout()

        # Initial playlist load from VirtualDJ
        self.refresh_playlist(show_alert=False)

    def _build_header(self):
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=("#1a1a24", "#121218")) if ctk else tk.Frame(self.root, bg="#121218")
        header_frame.pack(fill="x", padx=0, pady=0)

        title_sub_frame = ctk.CTkFrame(header_frame, fg_color="transparent") if ctk else tk.Frame(header_frame, bg="#121218")
        title_sub_frame.pack(side="left", padx=20, pady=12)

        if ctk:
            title_lbl = ctk.CTkLabel(
                title_sub_frame,
                text="🎧 SMARTMIX STUDIO",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=("#3b8ed0", "#60cdff")
            )
            title_lbl.pack(anchor="w")

            subtitle_lbl = ctk.CTkLabel(
                title_sub_frame,
                text="VirtualDJ On-Beat Continuous Mixtape & Cue Transition Engine",
                font=ctk.CTkFont(size=12),
                text_color=("#999999", "#aaaaaa")
            )
            subtitle_lbl.pack(anchor="w")
        else:
            tk.Label(title_sub_frame, text="🎧 SMARTMIX STUDIO", font=("Arial", 18, "bold"), fg="#60cdff", bg="#121218").pack(anchor="w")
            tk.Label(title_sub_frame, text="VirtualDJ On-Beat Continuous Mixtape Engine", font=("Arial", 10), fg="#aaaaaa", bg="#121218").pack(anchor="w")

        # Status badge
        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● SYSTEM READY",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4ade80",
            fg_color=("#1e293b", "#1e293b"),
            corner_radius=12,
            padx=14,
            pady=4
        ) if ctk else tk.Label(header_frame, text="● READY", fg="#4ade80", bg="#1e293b")
        self.status_badge.pack(side="right", padx=20, pady=16)

    def _build_main_layout(self):
        # Scrollable container for all configuration cards
        main_container = ctk.CTkScrollableFrame(self.root, fg_color="transparent") if ctk else tk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=16, pady=10)

        # ---------------------------------------------------------------------
        # CARD 1: EXPORT CONFIGURATION (Name & Destination Folder)
        # ---------------------------------------------------------------------
        export_card = self._create_card(main_container, "📁 Export Configuration & Output Location")
        export_card.pack(fill="x", pady=6)

        # Mix Name input
        name_row = ctk.CTkFrame(export_card, fg_color="transparent") if ctk else tk.Frame(export_card)
        name_row.pack(fill="x", padx=14, pady=6)

        lbl_name = ctk.CTkLabel(name_row, text="Mix Title / Genre:", width=140, anchor="w", font=ctk.CTkFont(weight="bold")) if ctk else tk.Label(name_row, text="Mix Title:")
        lbl_name.pack(side="left")

        self.mix_name_var = tk.StringVar(value="")
        self.mix_name_var.trace_add("write", lambda *args: self._update_preview_path())

        self.entry_name = ctk.CTkEntry(
            name_row,
            textvariable=self.mix_name_var,
            placeholder_text="Auto-detected from folder (e.g. Y2K, Amapiano, Afrobeats)",
            width=320
        ) if ctk else tk.Entry(name_row, textvariable=self.mix_name_var, width=30)
        self.entry_name.pack(side="left", padx=10, fill="x", expand=True)

        # Destination Folder input
        dest_row = ctk.CTkFrame(export_card, fg_color="transparent") if ctk else tk.Frame(export_card)
        dest_row.pack(fill="x", padx=14, pady=6)

        lbl_dest = ctk.CTkLabel(dest_row, text="Export Destination:", width=140, anchor="w", font=ctk.CTkFont(weight="bold")) if ctk else tk.Label(dest_row, text="Export Destination:")
        lbl_dest.pack(side="left")

        default_dest = str(Path.home() / "Downloads")
        self.dest_var = tk.StringVar(value=default_dest)
        self.dest_var.trace_add("write", lambda *args: self._update_preview_path())

        self.entry_dest = ctk.CTkEntry(dest_row, textvariable=self.dest_var, width=420) if ctk else tk.Entry(dest_row, textvariable=self.dest_var)
        self.entry_dest.pack(side="left", padx=10, fill="x", expand=True)

        btn_browse = ctk.CTkButton(
            dest_row,
            text="📂 Browse...",
            width=100,
            command=self.browse_destination
        ) if ctk else tk.Button(dest_row, text="Browse...", command=self.browse_destination)
        btn_browse.pack(side="right")

        # Output preview label
        preview_row = ctk.CTkFrame(export_card, fg_color="transparent") if ctk else tk.Frame(export_card)
        preview_row.pack(fill="x", padx=14, pady=(2, 8))

        lbl_preview_title = ctk.CTkLabel(preview_row, text="Output File Preview:", width=140, anchor="w", font=ctk.CTkFont(size=11), text_color="#888888") if ctk else tk.Label(preview_row, text="Output Preview:")
        lbl_preview_title.pack(side="left")

        self.lbl_preview_path = ctk.CTkLabel(
            preview_row,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#38bdf8"
        ) if ctk else tk.Label(preview_row, text="", fg="#38bdf8")
        self.lbl_preview_path.pack(side="left", fill="x", expand=True, padx=10)

        self._update_preview_path()

        # ---------------------------------------------------------------------
        # CARD 2: VIRTUALDJ AUTOMIX QUEUE (Live Playlist Preview)
        # ---------------------------------------------------------------------
        queue_card = self._create_card(main_container, "🎵 Active VirtualDJ Automix Queue")
        queue_card.pack(fill="x", pady=6)

        queue_top = ctk.CTkFrame(queue_card, fg_color="transparent") if ctk else tk.Frame(queue_card)
        queue_top.pack(fill="x", padx=14, pady=(4, 8))

        self.queue_info_lbl = ctk.CTkLabel(
            queue_top,
            text="Scanning VirtualDJ Automix list...",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ) if ctk else tk.Label(queue_top, text="Scanning...")
        self.queue_info_lbl.pack(side="left")

        btn_reload = ctk.CTkButton(
            queue_top,
            text="🔄 Reload from VirtualDJ",
            width=160,
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.refresh_playlist(show_alert=True)
        ) if ctk else tk.Button(queue_top, text="Reload", command=lambda: self.refresh_playlist(show_alert=True))
        btn_reload.pack(side="right")

        # Scrollable track table box
        self.table_box = ctk.CTkTextbox(
            queue_card,
            height=140,
            font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True
        ) if ctk else tk.Text(queue_card, height=7, font=("Consolas", 10))
        self.table_box.pack(fill="x", padx=14, pady=(0, 10))

        # ---------------------------------------------------------------------
        # CARD 3: AUDIO & TRANSITION SETTINGS
        # ---------------------------------------------------------------------
        settings_card = self._create_card(main_container, "🎛️ Transition & Studio Mastering Controls")
        settings_card.pack(fill="x", pady=6)

        opts_row = ctk.CTkFrame(settings_card, fg_color="transparent") if ctk else tk.Frame(settings_card)
        opts_row.pack(fill="x", padx=14, pady=8)

        # Transition Mode: Normal Cut vs Gradual Crossfade vs Both
        col_mode = ctk.CTkFrame(opts_row, fg_color="transparent") if ctk else tk.Frame(opts_row)
        col_mode.pack(side="left", fill="x", expand=True, padx=6)
        if ctk:
            ctk.CTkLabel(col_mode, text="Transition Mode:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            self.mode_var = tk.StringVar(value="Gradual DJ Crossfade (Cue 2 -> Cue 3)")
            self.mode_var.trace_add("write", lambda *args: self._update_preview_path())
            self.opt_mode = ctk.CTkOptionMenu(
                col_mode,
                values=[
                    "Gradual DJ Crossfade (Cue 2 -> Cue 3)",
                    "Normal Transition (Clean Cut, Zero Overlap)",
                    "Both (Normal & Crossfaded)"
                ],
                variable=self.mode_var
            )
            self.opt_mode.pack(fill="x", pady=4)
        else:
            self.mode_var = tk.StringVar(value="Gradual DJ Crossfade (Cue 2 -> Cue 3)")

        # Target Loudness
        col_loud = ctk.CTkFrame(opts_row, fg_color="transparent") if ctk else tk.Frame(opts_row)
        col_loud.pack(side="left", fill="x", expand=True, padx=6)
        if ctk:
            ctk.CTkLabel(col_loud, text="Loudness Target:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            self.lufs_var = tk.StringVar(value="-14.0 LUFS (DJ / Club Standard)")
            self.opt_lufs = ctk.CTkOptionMenu(
                col_loud,
                values=["-14.0 LUFS (DJ / Club Standard)", "-12.0 LUFS (Loud Club)", "-16.0 LUFS (Streaming/Radio)"],
                variable=self.lufs_var
            )
            self.opt_lufs.pack(fill="x", pady=4)
        else:
            self.lufs_var = tk.StringVar(value="-14.0 LUFS")

        # Headroom True Peak
        col_tp = ctk.CTkFrame(opts_row, fg_color="transparent") if ctk else tk.Frame(opts_row)
        col_tp.pack(side="left", fill="x", expand=True, padx=6)
        if ctk:
            ctk.CTkLabel(col_tp, text="True Peak Ceiling:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            self.tp_var = tk.StringVar(value="-1.5 dBTP (Headroom Margin)")
            self.opt_tp = ctk.CTkOptionMenu(
                col_tp,
                values=["-1.5 dBTP (Headroom Margin)", "-1.0 dBTP", "-2.0 dBTP"],
                variable=self.tp_var
            )
            self.opt_tp.pack(fill="x", pady=4)
        else:
            self.tp_var = tk.StringVar(value="-1.5 dBTP")

        # Scratch preview checkbox
        self.with_scratch_var = tk.BooleanVar(value=False)
        chk_row = ctk.CTkFrame(settings_card, fg_color="transparent") if ctk else tk.Frame(settings_card)
        chk_row.pack(fill="x", padx=14, pady=(0, 8))
        if ctk:
            ctk.CTkCheckBox(
                chk_row,
                text="Generate standalone DJ Scratch Routine preview for Track 1",
                variable=self.with_scratch_var,
                font=ctk.CTkFont(size=12)
            ).pack(side="left")

        # ---------------------------------------------------------------------
        # CARD 4: LIVE COMPILATION CONSOLE & ACTIONS
        # ---------------------------------------------------------------------
        action_card = self._create_card(main_container, "⚡ Live Mixtape Compilation Console")
        action_card.pack(fill="both", expand=True, pady=6)

        # Primary compile button
        btn_row = ctk.CTkFrame(action_card, fg_color="transparent") if ctk else tk.Frame(action_card)
        btn_row.pack(fill="x", padx=14, pady=10)

        self.btn_compile = ctk.CTkButton(
            btn_row,
            text="🚀 COMPILE MASTER MIXTAPE",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.start_compilation
        ) if ctk else tk.Button(btn_row, text="COMPILE MIXTAPE", command=self.start_compilation, height=2)
        self.btn_compile.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="⏹ Cancel",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=46,
            width=110,
            fg_color="#ef4444",
            hover_color="#dc2626",
            state="disabled",
            command=self.cancel_compilation
        ) if ctk else tk.Button(btn_row, text="Cancel", command=self.cancel_compilation)
        self.btn_cancel.pack(side="right")

        # Animated Progress bar
        self.progress_bar = ctk.CTkProgressBar(action_card) if ctk else None
        if self.progress_bar:
            self.progress_bar.set(0)
            self.progress_bar.pack(fill="x", padx=14, pady=(0, 8))

        # Real-time console log textbox
        self.console_box = ctk.CTkTextbox(
            action_card,
            height=180,
            font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True
        ) if ctk else tk.Text(action_card, height=10, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0")
        self.console_box.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Action bar when done (Open folder / Play mix)
        self.done_row = ctk.CTkFrame(action_card, fg_color="transparent") if ctk else tk.Frame(action_card)
        self.done_row.pack(fill="x", padx=14, pady=(0, 10))

        self.btn_open_folder = ctk.CTkButton(
            self.done_row,
            text="📂 Open Export Folder",
            width=180,
            state="disabled",
            fg_color="#334155",
            command=self.open_export_folder
        ) if ctk else tk.Button(self.done_row, text="Open Folder", command=self.open_export_folder)
        self.btn_open_folder.pack(side="left", padx=(0, 8))

        self.btn_play_mix = ctk.CTkButton(
            self.done_row,
            text="▶ Play Mix in Audio Player",
            width=200,
            state="disabled",
            fg_color="#15803d",
            hover_color="#166534",
            command=self.play_compiled_mix
        ) if ctk else tk.Button(self.done_row, text="Play Mix", command=self.play_compiled_mix)
        self.btn_play_mix.pack(side="left")

    def _create_card(self, parent, title):
        frame = ctk.CTkFrame(parent, corner_radius=8, fg_color=("#222230", "#181822")) if ctk else tk.LabelFrame(parent, text=title)
        if ctk:
            title_lbl = ctk.CTkLabel(
                frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
                text_color=("#60cdff", "#38bdf8")
            )
            title_lbl.pack(fill="x", padx=14, pady=(10, 4))
        return frame

    def _update_preview_path(self):
        curr_name = (self.mix_name_var.get() or "").strip()
        tracks = getattr(self, "tracks", None)
        mix_name = gm.resolve_mix_name(curr_name, tracks)
        dest_dir = self.dest_var.get().strip() or str(Path.home() / "Downloads")
        mode_val = self.mode_var.get() if hasattr(self, "mode_var") else "Crossfade"
        if "Crossfade" in mode_val:
            suffix = "Crossfaded"
        elif "Both" in mode_val:
            suffix = "Normal & Crossfaded"
        else:
            suffix = "Normal"
        out_file = os.path.join(dest_dir, f"{mix_name}_Continuous_Mix_{suffix}.mp3")
        if hasattr(self, "lbl_preview_path"):
            if ctk:
                self.lbl_preview_path.configure(text=out_file)
            else:
                self.lbl_preview_path.config(text=out_file)

    def browse_destination(self):
        chosen = filedialog.askdirectory(initialdir=self.dest_var.get(), title="Select Destination Folder for Compiled Mix")
        if chosen:
            self.dest_var.set(chosen)

    def refresh_playlist(self, show_alert=False):
        """Scans VirtualDJ Automix queue and Cue Database to update track table."""
        class DummyArgs:
            entry_cue = 1
            fade_cue = 2
            exit_cue = 3
            use_last_cues = False

        try:
            tracks = gm.get_track_data(DummyArgs())
            self.tracks = tracks

            # Auto-populate destination directory and mix name from track location if present
            if tracks and len(tracks) > 0 and tracks[0].get("path"):
                p_dir = str(Path(tracks[0]["path"]).parent)
                if os.path.exists(p_dir):
                    self.dest_var.set(p_dir)
                detected = gm.resolve_mix_name(None, tracks)
                curr = self.mix_name_var.get().strip()
                if not curr or curr in ("Amapiano", "Mixtape"):
                    self.mix_name_var.set(detected)

            self.table_box.configure(state="normal") if ctk else None
            self.table_box.delete("1.0", "end")

            if not tracks:
                msg = "No tracks currently detected in VirtualDJ Automix.\nIn VirtualDJ, drag songs into Sideview -> Automix and click Save (or close VirtualDJ)."
                self.table_box.insert("end", msg)
                self.queue_info_lbl.configure(text="0 tracks loaded | Queue is empty", text_color="#f87171") if ctk else None
            else:
                self.queue_info_lbl.configure(
                    text=f"✓ Successfully loaded {len(tracks)} track{'s' if len(tracks) > 1 else ''} from VirtualDJ Automix",
                    text_color="#4ade80"
                ) if ctk else None

                header = f"{'#':<3} | {'Artist & Title':<46} | {'BPM':<6} | {'Cue 1(In)':<9} | {'Cue 2(Fade)':<11} | {'Cue 3(Cut)':<10} | {'Duration'}\n"
                separator = "-" * 105 + "\n"
                self.table_box.insert("end", header)
                self.table_box.insert("end", separator)

                for i, t in enumerate(tracks):
                    art_title = f"{t['artist']} - {t['title']}"
                    if len(art_title) > 46:
                        art_title = art_title[:43] + "..."
                    c1 = gm.format_time(t["cue_entry"])
                    c2 = gm.format_time(t["cue_fade"])
                    c3 = gm.format_time(t["cue_exit"])
                    dur = gm.format_time(t["length"])
                    line = f"{i+1:<3} | {art_title:<46} | {t['bpm']:<6.1f} | {c1:<9} | {c2:<11} | {c3:<10} | {dur}\n"
                    self.table_box.insert("end", line)

            self.table_box.configure(state="disabled") if ctk else None

            if show_alert:
                if tracks:
                    messagebox.showinfo("VirtualDJ Synced", f"Successfully loaded {len(tracks)} tracks from your active VirtualDJ Automix queue!")
                else:
                    messagebox.showwarning("VirtualDJ Queue Empty", "VirtualDJ Automix folder is empty or not yet saved by VirtualDJ.\n\nMake sure to click the Automix panel menu -> Save or close VirtualDJ to update the playlist.")

        except Exception as e:
            self.table_box.delete("1.0", "end")
            self.table_box.insert("end", f"Notice reading VirtualDJ files: {e}")
            if show_alert:
                messagebox.showerror("Error", f"Failed to read VirtualDJ playlist: {e}")

    def log_console(self, text):
        self.console_box.configure(state="normal") if ctk else None
        self.console_box.insert("end", text)
        self.console_box.see("end")
        self.console_box.configure(state="disabled") if ctk else None

    def start_compilation(self):
        if self.is_compiling:
            return

        curr_name = (self.mix_name_var.get() or "").strip()
        mix_name = gm.resolve_mix_name(curr_name, getattr(self, "tracks", None))
        dest_dir = self.dest_var.get().strip() or str(Path.home() / "Downloads")
        os.makedirs(dest_dir, exist_ok=True)

        # Parse LUFS
        raw_lufs = self.lufs_var.get()
        target_lufs = -14.0
        if "-12" in raw_lufs:
            target_lufs = -12.0
        elif "-16" in raw_lufs:
            target_lufs = -16.0

        # Parse True Peak
        raw_tp = self.tp_var.get()
        true_peak = -1.5
        if "-1.0" in raw_tp:
            true_peak = -1.0
        elif "-2.0" in raw_tp:
            true_peak = -2.0

        mode_str = self.mode_var.get() if hasattr(self, "mode_var") else "Normal"
        if "Crossfade" in mode_str:
            target_mode = "crossfade"
            suffix = "Crossfaded"
        elif "Both" in mode_str:
            target_mode = "both"
            suffix = "Normal"
        else:
            target_mode = "normal"
            suffix = "Normal"

        with_scratch = self.with_scratch_var.get()
        out_file = os.path.join(dest_dir, f"{mix_name}_Continuous_Mix_{suffix}.mp3")
        self.last_output_file = out_file

        # UI state during compiling
        self.is_compiling = True
        self.btn_compile.configure(state="disabled", text="⏳ MIXING IN PROGRESS...") if ctk else None
        self.btn_cancel.configure(state="normal") if ctk else None
        self.btn_open_folder.configure(state="disabled") if ctk else None
        self.btn_play_mix.configure(state="disabled") if ctk else None
        self.status_badge.configure(text="● COMPILING MIX...", text_color="#38bdf8") if ctk else None
        if self.progress_bar:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()

        self.console_box.configure(state="normal") if ctk else None
        self.console_box.delete("1.0", "end")
        self.console_box.configure(state="disabled") if ctk else None

        self.log_console("Starting SmartMix compilation pipeline...\n")
        self.log_console(f"Mix Title   : {mix_name}\n")
        self.log_console(f"Destination : {dest_dir}\n")
        self.log_console(f"Output File : {out_file}\n")
        self.log_console(f"Mode        : {target_mode.upper()} ({'Clean Cue-Drop Transitions, Zero Crossfade' if target_mode == 'normal' else 'Gradual Crossfade' if target_mode == 'crossfade' else 'Both Normal and Crossfade'})\n")
        self.log_console("-" * 72 + "\n")

        # Launch compilation in background worker thread
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "smartmix.py"),
            "--mix-name", mix_name,
            "--output-dir", dest_dir,
            "--mode", target_mode,
            "--target-lufs", str(target_lufs),
            "--true-peak", str(true_peak)
        ]
        if with_scratch:
            cmd.append("--with-scratch-preview")

        thread = threading.Thread(target=self._run_compiler_thread, args=(cmd,), daemon=True)
        thread.start()

    def _run_compiler_thread(self, cmd):
        try:
            self.compile_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in self.compile_process.stdout:
                self.root.after(0, self.log_console, line)

            self.compile_process.wait()
            ret_code = self.compile_process.returncode

            self.root.after(0, self._on_compile_finished, ret_code)
        except Exception as e:
            self.root.after(0, self.log_console, f"\nCompilation error: {e}\n")
            self.root.after(0, self._on_compile_finished, 1)

    def _on_compile_finished(self, returncode):
        self.is_compiling = False
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0 if returncode == 0 else 0.0)

        self.btn_compile.configure(state="normal", text="🚀 COMPILE MASTER MIXTAPE") if ctk else None
        self.btn_cancel.configure(state="disabled") if ctk else None

        if returncode == 0:
            self.status_badge.configure(text="✓ MASTERING COMPLETE", text_color="#4ade80") if ctk else None
            self.btn_open_folder.configure(state="normal") if ctk else None
            self.btn_play_mix.configure(state="normal") if ctk else None
            messagebox.showinfo("SmartMix Success", f"Your master continuous mix has been generated successfully!\n\nSaved to:\n{self.last_output_file}")
        else:
            self.status_badge.configure(text="⚠ COMPILATION STOPPED", text_color="#ef4444") if ctk else None
            messagebox.showwarning("Notice", "Compilation finished with errors or was cancelled. Check console log for details.")

    def cancel_compilation(self):
        if self.compile_process and self.is_compiling:
            try:
                self.compile_process.terminate()
                self.log_console("\n[CANCELLED] Compilation process was terminated by user.\n")
            except Exception:
                pass

    def open_export_folder(self):
        dest_dir = self.dest_var.get().strip()
        if os.path.exists(dest_dir):
            if os.name == 'nt':
                os.startfile(dest_dir)
            else:
                subprocess.Popen(["xdg-open", dest_dir])

    def play_compiled_mix(self):
        if self.last_output_file and os.path.exists(self.last_output_file):
            if os.name == 'nt':
                os.startfile(self.last_output_file)
            else:
                subprocess.Popen(["xdg-open", self.last_output_file])
        else:
            messagebox.showwarning("File Not Found", "The compiled mix file could not be found.")

def main():
    if ctk:
        root = ctk.CTk()
    else:
        root = tk.Tk()
    app = SmartMixApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
