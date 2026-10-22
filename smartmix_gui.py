"""
==============================================================================
 SMARTMIX STUDIO: MODERN DESKTOP USER INTERFACE & TRANSITION DIRECTOR
==============================================================================
A sleek, modern dark-themed graphical interface for the SmartMix DJ mixtape
compilation engine with interactive per-transition auditioning.

Features:
  - Configure mix title and custom export destination folder (1 master output file)
  - Live preview and refresh of VirtualDJ Automix queue & Cue markers
  - Interactive Transition Director: customize each song-to-song transition individually
    (Gradual DJ Crossfade, Normal Outro to Cue 3, Immediate Cut, Filter-Sweep, Echo-Out)
  - Instant Transition Auditioning: listen to how any transition sounds before compiling!
  - Loudness targets and true-peak limiter controls (EBU R128)
  - Real-time compilation progress bar and streamed terminal logs
  - 1-click 'Open in Explorer' and 'Play Mix' buttons upon completion
==============================================================================
"""

import os
import sys
import threading
import subprocess
import tempfile
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None

import numpy as np
from scipy.io import wavfile

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

TRANSITION_MODES = [
    "Gradual DJ Crossfade",
    "Normal Cut (Hear Out to Cue 3)",
    "Immediate Cut (Drop)",
    "Filter-Sweep Wash",
    "Echo-Out Decay",
    "Equal-Power Blend"
]

MODE_TO_CLI = {
    "Gradual DJ Crossfade": "gradual",
    "Normal Cut (Hear Out to Cue 3)": "normal",
    "Immediate Cut (Drop)": "immediate",
    "Filter-Sweep Wash": "filter-sweep",
    "Echo-Out Decay": "echo-out",
    "Equal-Power Blend": "equal-power"
}

class SmartMixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartMix Studio — DJ Continuous Mixtape Engine & Transition Director")
        self.root.geometry("1060x860")
        self.root.minsize(920, 720)

        # Application state
        self.tracks = []
        self.compile_process = None
        self.is_compiling = False
        self.last_output_file = None

        # Per-transition controls
        self.trans_vars = {}
        self.trans_audition_btns = {}
        self.current_audition_idx = None

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
                text="VirtualDJ Cue Transition Director & Studio Master Compiler",
                font=ctk.CTkFont(size=12),
                text_color=("#999999", "#aaaaaa")
            )
            subtitle_lbl.pack(anchor="w")
        else:
            tk.Label(title_sub_frame, text="🎧 SMARTMIX STUDIO", font=("Arial", 18, "bold"), fg="#60cdff", bg="#121218").pack(anchor="w")
            tk.Label(title_sub_frame, text="VirtualDJ Cue Transition Director & Studio Master Compiler", font=("Arial", 10), fg="#aaaaaa", bg="#121218").pack(anchor="w")

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
            placeholder_text="Auto-detected from playlist folder",
            width=340
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

        # Output preview label (Single master output file for SmartMix Studio)
        preview_row = ctk.CTkFrame(export_card, fg_color="transparent") if ctk else tk.Frame(export_card)
        preview_row.pack(fill="x", padx=14, pady=(2, 8))

        lbl_preview_title = ctk.CTkLabel(preview_row, text="Master Output File:", width=140, anchor="w", font=ctk.CTkFont(size=11), text_color="#888888") if ctk else tk.Label(preview_row, text="Master Output File:")
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
        # CARD 2: VIRTUALDJ AUTOMIX QUEUE SUMMARY
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
            width=170,
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.refresh_playlist(show_alert=True)
        ) if ctk else tk.Button(queue_top, text="Reload", command=lambda: self.refresh_playlist(show_alert=True))
        btn_reload.pack(side="right")

        # ---------------------------------------------------------------------
        # CARD 3: TRANSITION DIRECTOR & AUDITION STUDIO
        # ---------------------------------------------------------------------
        trans_card = self._create_card(main_container, "🎚️ Transition Director & Audition Studio")
        trans_card.pack(fill="x", pady=6)

        trans_header = ctk.CTkFrame(trans_card, fg_color="transparent") if ctk else tk.Frame(trans_card)
        trans_header.pack(fill="x", padx=14, pady=(2, 6))

        if ctk:
            ctk.CTkLabel(
                trans_header,
                text="Audition and choose the transition style for each song pair. Mix different transitions to fit each vibe!",
                font=ctk.CTkFont(size=11),
                text_color="#94a3b8"
            ).pack(anchor="w")

        # Scrollable container for individual transition rows
        self.transitions_container = ctk.CTkFrame(trans_card, fg_color=("#181822", "#0f172a"), corner_radius=6) if ctk else tk.Frame(trans_card, bg="#0f172a")
        self.transitions_container.pack(fill="x", padx=14, pady=(0, 10))

        # ---------------------------------------------------------------------
        # CARD 4: MASTERING CONTROLS
        # ---------------------------------------------------------------------
        settings_card = self._create_card(main_container, "🎛️ Studio Mastering & Headroom Controls")
        settings_card.pack(fill="x", pady=6)

        opts_row = ctk.CTkFrame(settings_card, fg_color="transparent") if ctk else tk.Frame(settings_card)
        opts_row.pack(fill="x", padx=14, pady=8)

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
        # CARD 5: LIVE COMPILATION CONSOLE & ACTIONS
        # ---------------------------------------------------------------------
        action_card = self._create_card(main_container, "⚡ Master Mixtape Compilation Console")
        action_card.pack(fill="both", expand=True, pady=6)

        # Primary compile button
        btn_row = ctk.CTkFrame(action_card, fg_color="transparent") if ctk else tk.Frame(action_card)
        btn_row.pack(fill="x", padx=14, pady=10)

        self.btn_compile = ctk.CTkButton(
            btn_row,
            text="🚀 COMPILE MASTER MIXTAPE (1 FILE)",
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
            height=160,
            font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True
        ) if ctk else tk.Text(action_card, height=8, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0")
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
        # SmartMix Studio produces exactly 1 unified continuous mix output file
        out_file = os.path.join(dest_dir, f"{mix_name}_Continuous_Mix.mp3")
        self.last_output_file = out_file
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
        """Scans VirtualDJ Automix queue, populates metadata, and builds transition controls."""
        class DummyArgs:
            entry_cue = 1
            fade_cue = 2
            exit_cue = 3
            use_last_cues = False

        self.stop_audition()

        try:
            tracks = gm.get_track_data(DummyArgs())
            self.tracks = tracks

            # Auto-populate destination directory and mix name from track location
            if tracks and len(tracks) > 0 and tracks[0].get("path"):
                p_dir = str(Path(tracks[0]["path"]).parent)
                if os.path.exists(p_dir):
                    self.dest_var.set(p_dir)
                detected = gm.resolve_mix_name(None, tracks)
                curr = self.mix_name_var.get().strip()
                if not curr or curr in ("Amapiano", "Mixtape"):
                    self.mix_name_var.set(detected)

            # Rebuild Transition Rows
            for widget in self.transitions_container.winfo_children():
                widget.destroy()

            self.trans_vars.clear()
            self.trans_audition_btns.clear()

            if not tracks or len(tracks) < 2:
                self.queue_info_lbl.configure(
                    text="VirtualDJ Automix list has fewer than 2 tracks. Load at least 2 tracks to mix.",
                    text_color="#f87171"
                ) if ctk else None
                return

            self.queue_info_lbl.configure(
                text=f"✓ Loaded {len(tracks)} tracks from VirtualDJ Automix ({len(tracks) - 1} Transitions Available)",
                text_color="#4ade80"
            ) if ctk else None

            # Populate each transition
            for i in range(len(tracks) - 1):
                t_a = tracks[i]
                t_b = tracks[i + 1]
                self._build_transition_row(i, t_a, t_b)

            self._update_preview_path()

            if show_alert:
                messagebox.showinfo("VirtualDJ Synced", f"Loaded {len(tracks)} tracks with {len(tracks) - 1} customizable transitions!")

        except Exception as e:
            if show_alert:
                messagebox.showerror("Error", f"Failed to read VirtualDJ playlist: {e}")

    def _build_transition_row(self, idx, t_a, t_b):
        """Builds an interactive transition configuration row with style picker and audition button."""
        bpm_a = t_a.get("bpm") or 118.0
        bpm_b = t_b.get("bpm") or 118.0
        fade_time = gm.format_time(t_a.get("cue_fade"))
        exit_time = gm.format_time(t_a.get("cue_exit"))
        
        has_fade = t_a.get("cue_fade") is not None
        has_exit = t_a.get("cue_exit") is not None
        is_immediate = has_fade and has_exit and (t_a["cue_exit"] <= t_a["cue_fade"] + 0.1)
        dur_s = (t_a["cue_exit"] - t_a["cue_fade"]) if (has_fade and has_exit) else 0.0

        row = ctk.CTkFrame(self.transitions_container, fg_color=("#1f2937" if idx % 2 == 0 else "#111827"), corner_radius=6) if ctk else tk.Frame(self.transitions_container)
        row.pack(fill="x", padx=6, pady=3)

        # Left Column: Track Info
        info_col = ctk.CTkFrame(row, fg_color="transparent") if ctk else tk.Frame(row)
        info_col.pack(side="left", fill="x", expand=True, padx=10, pady=6)

        title_a = t_a["title"][:22] + "..." if len(t_a["title"]) > 25 else t_a["title"]
        title_b = t_b["title"][:22] + "..." if len(t_b["title"]) > 25 else t_b["title"]
        main_text = f"#{idx+1}  {title_a}  ➔  {title_b}"

        if is_immediate:
            detail_text = f"Cue 2 == Cue 3 ({fade_time}) | Immediate Cut | {bpm_a:.1f} ➔ {bpm_b:.1f} BPM"
            default_style = "Immediate Cut (Drop)"
        else:
            detail_text = f"Cue 2 ({fade_time}) ➔ Cue 3 ({exit_time}) [{dur_s:.1f}s] | {bpm_a:.1f} ➔ {bpm_b:.1f} BPM"
            default_style = "Gradual DJ Crossfade"

        if ctk:
            ctk.CTkLabel(info_col, text=main_text, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_col, text=detail_text, font=ctk.CTkFont(size=10), text_color="#94a3b8", anchor="w").pack(anchor="w")
        else:
            tk.Label(info_col, text=main_text, font=("Arial", 10, "bold")).pack(anchor="w")
            tk.Label(info_col, text=detail_text, font=("Arial", 8), fg="#94a3b8").pack(anchor="w")

        # Right Column: Transition Style Dropdown + Audition Button
        ctrl_col = ctk.CTkFrame(row, fg_color="transparent") if ctk else tk.Frame(row)
        ctrl_col.pack(side="right", padx=10, pady=6)

        style_var = tk.StringVar(value=default_style)
        self.trans_vars[idx] = style_var

        if ctk:
            opt = ctk.CTkOptionMenu(
                ctrl_col,
                values=TRANSITION_MODES,
                variable=style_var,
                width=190,
                font=ctk.CTkFont(size=11)
            )
            opt.pack(side="left", padx=6)
        else:
            opt = tk.OptionMenu(ctrl_col, style_var, *TRANSITION_MODES)
            opt.pack(side="left", padx=6)

        btn_audition = ctk.CTkButton(
            ctrl_col,
            text="▶ Audition",
            width=92,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda i=idx: self.toggle_audition(i)
        ) if ctk else tk.Button(ctrl_col, text="Audition", command=lambda i=idx: self.toggle_audition(i))
        btn_audition.pack(side="left", padx=4)

        self.trans_audition_btns[idx] = btn_audition

    def toggle_audition(self, idx):
        """Toggles audio playback auditioning for the selected transition."""
        if not winsound:
            messagebox.showinfo("Audition Notice", "Audio playback (winsound) is not available on this platform.")
            return

        # If currently playing this transition, stop it
        if self.current_audition_idx == idx:
            self.stop_audition()
            return

        self.stop_audition()

        btn = self.trans_audition_btns.get(idx)
        if btn:
            if ctk:
                btn.configure(text="⏳ Loading...", state="disabled")
            else:
                btn.config(text="⏳ Loading...", state="disabled")

        def _worker():
            try:
                t_a = self.tracks[idx]
                t_b = self.tracks[idx + 1]
                choice_str = self.trans_vars[idx].get()
                mode_key = MODE_TO_CLI.get(choice_str, "gradual")

                clip = gm.render_transition_preview(t_a, t_b, mode=mode_key)
                temp_wav = os.path.join(tempfile.gettempdir(), f"_smartmix_audition_{idx}.wav")
                wavfile.write(temp_wav, 44100, (np.clip(clip, -1.0, 1.0) * 32767).astype(np.int16))

                def _start_playback():
                    self.current_audition_idx = idx
                    if btn:
                        if ctk:
                            btn.configure(text="⏹ Stop", fg_color="#ef4444", hover_color="#dc2626", state="normal")
                        else:
                            btn.config(text="⏹ Stop", state="normal")
                    winsound.PlaySound(temp_wav, winsound.SND_ASYNC | winsound.SND_FILENAME)
                    clip_len_ms = int((len(clip) / 44100.0) * 1000) + 300
                    self.root.after(clip_len_ms, lambda: self._on_audition_finished(idx))

                self.root.after(0, _start_playback)
            except Exception as e:
                def _error_reset():
                    if btn:
                        if ctk:
                            btn.configure(text="▶ Audition", fg_color="#0284c7", hover_color="#0369a1", state="normal")
                        else:
                            btn.config(text="▶ Audition", state="normal")
                    messagebox.showwarning("Audition Notice", f"Could not preview transition: {e}")
                self.root.after(0, _error_reset)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_audition_finished(self, idx):
        if self.current_audition_idx == idx:
            self.stop_audition()

    def stop_audition(self):
        if winsound:
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass
        if self.current_audition_idx is not None:
            old_btn = self.trans_audition_btns.get(self.current_audition_idx)
            if old_btn:
                if ctk:
                    old_btn.configure(text="▶ Audition", fg_color="#0284c7", hover_color="#0369a1", state="normal")
                else:
                    old_btn.config(text="▶ Audition", state="normal")
            self.current_audition_idx = None

    def log_console(self, text):
        self.console_box.configure(state="normal") if ctk else None
        self.console_box.insert("end", text)
        self.console_box.see("end")
        self.console_box.configure(state="disabled") if ctk else None

    def start_compilation(self):
        if self.is_compiling:
            return

        self.stop_audition()

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

        # Build per-transition custom styles
        style_entries = []
        for idx, var in sorted(self.trans_vars.items()):
            choice_str = var.get()
            mode_key = MODE_TO_CLI.get(choice_str, "gradual")
            style_entries.append(f"{idx+1}={mode_key}")
        trans_style_arg = ",".join(style_entries)

        # SmartMix Studio produces 1 unified master output file
        out_file = os.path.join(dest_dir, f"{mix_name}_Continuous_Mix.mp3")
        self.last_output_file = out_file
        with_scratch = self.with_scratch_var.get()

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

        self.log_console("Starting SmartMix Studio master compilation pipeline...\n")
        self.log_console(f"Mix Title   : {mix_name}\n")
        self.log_console(f"Destination : {dest_dir}\n")
        self.log_console(f"Master Output: {out_file}\n")
        self.log_console(f"Transitions : {len(style_entries)} customized song-to-song transitions\n")
        self.log_console("-" * 72 + "\n")

        # Launch compilation in background worker thread
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "smartmix.py"),
            "--mix-name", mix_name,
            "--output-file", out_file,
            "--mode", "crossfade",
            "--trans-style", trans_style_arg,
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

        self.btn_compile.configure(state="normal", text="🚀 COMPILE MASTER MIXTAPE (1 FILE)") if ctk else None
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
