import os
import zipfile
import re

# 1. Update database.xml
db_path = r"C:\Users\odhis\AppData\Local\VirtualDJ\database.xml"
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8", errors="ignore") as f:
        db_content = f.read()

    # Song 1: Zzero Sufuri Otero
    # Ensure Cue 1 (12.910092), Cue 2 (90.064801), cutStart/fadeStart (12.910092), cutEnd/fadeEnd (90.064801), Action POI
    zzero_target = 'FilePath="C:\\Users\\odhis\\Videos\\Zzero Sufuri Otero Ft Toxic Lyrikali (Official Music Video) (via DW YouTube Downloader).mkv"'
    pos = db_content.find(zzero_target)
    if pos != -1:
        end_song = db_content.find("</Song>", pos)
        song_block = db_content[pos:end_song]
        
        # Remove old automix / action / cue POIs in this block to reconstruct cleanly
        # Keep Tags, Infos, Scan
        scan_end = song_block.find("Flag=\"32768\" />")
        if scan_end != -1:
            scan_end += len("Flag=\"32768\" />")
            header_part = song_block[:scan_end]
            new_pois = """
  <Poi Pos="12.910092" Type="automix" Point="realStart" />
  <Poi Pos="12.910092" Type="automix" Point="fadeStart" />
  <Poi Pos="12.910092" Type="automix" Point="cutStart" />
  <Poi Pos="12.910092" Num="1" Type="cue" />
  <Poi Pos="90.064801" Num="2" Type="cue" />
  <Poi Name="SmartMix Cutoff" Pos="90.064801" Type="action" Action="deck 2 volume 100% &amp; deck 2 match_bpm &amp; deck 2 goto_cue 1 &amp; deck 2 play &amp; deck 1 stop &amp; deck 1 volume 0% &amp; crossfader 100%" />
  <Poi Pos="90.064801" Type="automix" Point="cutEnd" />
  <Poi Pos="90.064801" Type="automix" Point="fadeEnd" />
  <Poi Pos="90.064801" Type="automix" Point="realEnd" />
 """
            new_song_block = header_part + new_pois
            db_content = db_content[:pos] + new_song_block + db_content[end_song:]
            print("Updated Zzero Sufuri Otero in database.xml")

    # Song 2: Toxic Lyrikali - Lowkey
    lowkey_target = 'FilePath="C:\\Users\\odhis\\Downloads\\Toxic Lyrikali - Lowkey (Official Video).mp3"'
    pos_lk = db_content.find(lowkey_target)
    if pos_lk != -1:
        end_song_lk = db_content.find("</Song>", pos_lk)
        song_block_lk = db_content[pos_lk:end_song_lk]
        scan_end_lk = song_block_lk.find("Flag=\"32768\" />")
        if scan_end_lk != -1:
            scan_end_lk += len("Flag=\"32768\" />")
            header_part_lk = song_block_lk[:scan_end_lk]
            new_pois_lk = """
  <Poi Pos="4.029613" Type="automix" Point="realStart" />
  <Poi Pos="4.029613" Type="automix" Point="fadeStart" />
  <Poi Pos="4.029613" Type="automix" Point="cutStart" />
  <Poi Pos="4.029613" Num="1" Type="cue" />
  <Poi Pos="18.405315" Num="2" Type="cue" />
  <Poi Name="SmartMix Cutoff" Pos="18.405315" Type="action" Action="deck 1 volume 100% &amp; deck 1 match_bpm &amp; deck 1 goto_cue 1 &amp; deck 1 play &amp; deck 2 stop &amp; deck 2 volume 0% &amp; crossfader 0%" />
  <Poi Pos="18.405315" Type="automix" Point="cutEnd" />
  <Poi Pos="18.405315" Type="automix" Point="fadeEnd" />
  <Poi Pos="18.405315" Type="automix" Point="realEnd" />
 """
            new_song_block_lk = header_part_lk + new_pois_lk
            db_content = db_content[:pos_lk] + new_song_block_lk + db_content[end_song_lk:]
            print("Updated Toxic Lyrikali Lowkey in database.xml")

    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("Saved database.xml successfully")

# 2. Update Essentials.xml in AppData and Documents
new_panel_code = r"""				<panel name="smartmix_panel" group="mixer" visible="no">
		<visual name="smartmix_bg" x="+4" y="+32">
			<size width="384" height="286"/>
			<off color="mixerbackground" shape="square" border="bordercolor" border_size="1" radius="5"/>
		</visual>

		<!-- TOP CONTROL BAR: START SMARTMIX & OPTIONS & MIX NOW -->
		<group name="sm_top_bar" x="+12" y="+38">
			<!-- START SMARTMIX TOGGLE WITH REALTIME WATCHER -->
			<button class="button_master" x="+0" y="+0" width="168" height="34" action="var '@$smartmix_running' ? set '@$smartmix_running' 0 &amp; repeat_stop 'smartmix_watch' : set '@$smartmix_running' 1 &amp; (deck 1 play ? nothing : deck 2 play ? nothing : deck 1 volume 100% &amp; deck 1 goto_cue 1 &amp; deck 1 play) &amp; repeat_start 'smartmix_watch' 50ms &amp; (deck 1 play ? (deck 1 has_cue 2 ? (param_bigger `deck 1 songpos` `deck 1 cue_pos 2` ? deck 2 volume 100% &amp; deck 2 match_bpm &amp; deck 2 goto_cue 1 &amp; deck 2 play &amp; deck 1 stop &amp; deck 1 volume 0% &amp; crossfader 100% : nothing) : nothing) : (deck 2 play ? (deck 2 has_cue 2 ? (param_bigger `deck 2 songpos` `deck 2 cue_pos 2` ? deck 1 volume 100% &amp; deck 1 match_bpm &amp; deck 1 goto_cue 1 &amp; deck 1 play &amp; deck 2 stop &amp; deck 2 volume 0% &amp; crossfader 0% : nothing) : nothing) : nothing))" text="START SMARTMIX" textaction="var '@$smartmix_running' ? 'SMARTMIX ON (STOP)' : 'START SMARTMIX'" tooltip="Start or Stop Automated Cue-Based SmartMix" />

			<!-- SMARTMIX OPTIONS MENU -->
			<menu class="menubutton" tooltip="SMARTMIX OPTIONS&#x0A;Configure transition curves, EQ swap, and cutoff rules">
				<pos x="+176" y="+0"/>
				<size width="96" height="34"/>
				<visual>
					<pos x="+0" y="+0"/>
					<size width="96" height="34"/>
					<off shape="square" color="topmenu" radius="4" border_size="1" border="bordercolor2"/>
				</visual>
				<text dx="8" width="70" fontsize="10" weight="bold" color="textoff3" colorover="textover" align="left" text="OPTIONS" important="true"/>
				<icon dx="38" dy="-1" sysicon="chevrondown" height="14" width="14" color="textdark" colorover="textover" colordown="texton"/>
				<item text="SmartMix Editor (Active)" action="skin_panel 'smartmix_panel' on" check="true"/>
				<separator/>
				<item text="Curve: Equal Power (Smooth)" action="set '@$sm_curve' 0" check="var_equal '@$sm_curve' 0"/>
				<item text="Curve: Linear Fade" action="set '@$sm_curve' 1" check="var_equal '@$sm_curve' 1"/>
				<item text="Curve: Sharp Cut (Slam Mix)" action="set '@$sm_curve' 2" check="var_equal '@$sm_curve' 2"/>
				<item text="EQ Bass Swap at Midpoint" action="toggle '@$sm_bass_swap'" check="var_equal '@$sm_bass_swap' 1"/>
				<separator/>
				<item text="Strict Non-Destructive Cutoff" check="true"/>
				<item text="Auto-Sync BPM (No Phase Jump)" check="true"/>
				<separator/>
				<item text="Reset Crossfader &amp; Volume" action="deck all volume 100% &amp; crossfader 50% &amp; deck all mute off"/>
			</menu>

			<!-- TRANSITION NOW (ONE-CLICK MANUAL TRIGGER) -->
			<button class="button_master" x="+278" y="+0" width="90" height="34" action="deck 1 play ? deck 2 volume 100% &amp; deck 2 match_bpm &amp; deck 2 goto_cue 1 &amp; deck 2 play &amp; deck 1 stop &amp; deck 1 volume 0% &amp; crossfader 100% : deck 2 play ? deck 1 volume 100% &amp; deck 1 match_bpm &amp; deck 1 goto_cue 1 &amp; deck 1 play &amp; deck 2 stop &amp; deck 2 volume 0% &amp; crossfader 0% : deck 1 volume 100% &amp; deck 1 goto_cue 1 &amp; deck 1 play" text="MIX NOW" tooltip="Mechanically fire SmartMix transition immediately" />
		</group>

		<!-- SEPARATOR LINE -->
		<line x="+12" y="+78" width="368" height="1" color="bordercolor" />

		<!-- DECK A (OUTGOING) - CUE CENTERED CONTROLS -->
		<group name="sm_deck_a" x="+12" y="+84">
			<visual x="+0" y="+0">
				<size width="176" height="20"/>
				<off color="waveform_active1" shape="square" radius="3"/>
			</visual>
			<textzone x="+0" y="+2">
				<size width="176" height="16"/>
				<text fontsize="11" weight="bold" color="texton" align="center" text="DECK A - OUTGOING"/>
			</textzone>

			<!-- Cue Jump & Selection Buttons -->
			<textzone x="+0" y="+24">
				<size width="176" height="14"/>
				<text fontsize="9" color="textbright" align="center" text="Auto-Selected Cues:"/>
			</textzone>
			<button class="button_master" x="+0" y="+40" width="84" height="28" action="deck 1 goto_cue 1" text="CUE 1 (START)" tooltip="Jump Deck A to Cue 1 (Start at 12.91s)"/>
			<button class="button_master" x="+92" y="+40" width="84" height="28" action="deck 1 goto_cue 2" text="CUE 2 (CUTOFF)" tooltip="Jump Deck A to Cue 2 (Cutoff point at 90.06s)"/>
			<button class="button_master" x="+0" y="+72" width="84" height="24" action="deck 1 goto_cue 3" text="CUE 3" tooltip="Jump Deck A to Cue 3"/>
			<button class="button_master" x="+92" y="+72" width="84" height="24" action="deck 1 goto_cue 4" text="CUE 4" tooltip="Jump Deck A to Cue 4"/>

			<!-- Cutout Action Button -->
			<button class="button_master" x="+0" y="+100" width="176" height="22" action="deck 1 stop &amp; deck 1 volume 0% &amp; deck 1 unload" text="CUT OUT SONG A (CLEAR)" tooltip="Immediately cut out, silence, and unload Deck A"/>

			<!-- Cue Configuration Labels -->
			<textzone x="+0" y="+124">
				<size width="176" height="14"/>
				<text fontsize="9" color="textoff3" align="center" text="Trigger: Cue 1 | Cutoff: Cue 2"/>
			</textzone>
		</group>

		<!-- VERTICAL DIVIDER -->
		<line x="+196" y="+84" width="1" height="140" color="bordercolor" />

		<!-- DECK B (INCOMING) - CUE CENTERED CONTROLS -->
		<group name="sm_deck_b" x="+204" y="+84">
			<visual x="+0" y="+0">
				<size width="176" height="20"/>
				<off color="waveform_active2" shape="square" radius="3"/>
			</visual>
			<textzone x="+0" y="+2">
				<size width="176" height="16"/>
				<text fontsize="11" weight="bold" color="texton" align="center" text="DECK B - INCOMING"/>
			</textzone>

			<!-- Cue Jump & Selection Buttons -->
			<textzone x="+0" y="+24">
				<size width="176" height="14"/>
				<text fontsize="9" color="textbright" align="center" text="Auto-Selected Cues:"/>
			</textzone>
			<button class="button_master" x="+0" y="+40" width="84" height="28" action="deck 2 goto_cue 1" text="CUE 1 (START)" tooltip="Jump Deck B to Cue 1"/>
			<button class="button_master" x="+92" y="+40" width="84" height="28" action="deck 2 goto_cue 2" text="CUE 2 (CUTOFF)" tooltip="Jump Deck B to Cue 2"/>
			<button class="button_master" x="+0" y="+72" width="84" height="24" action="deck 2 goto_cue 3" text="CUE 3" tooltip="Jump Deck B to Cue 3"/>
			<button class="button_master" x="+92" y="+72" width="84" height="24" action="deck 2 goto_cue 4" text="CUE 4" tooltip="Jump Deck B to Cue 4"/>

			<!-- Cutout Action Button -->
			<button class="button_master" x="+0" y="+100" width="176" height="22" action="deck 2 stop &amp; deck 2 volume 0% &amp; deck 2 unload" text="CUT OUT SONG B (CLEAR)" tooltip="Immediately cut out, silence, and unload Deck B"/>

			<!-- Cue Configuration Labels -->
			<textzone x="+0" y="+124">
				<size width="176" height="14"/>
				<text fontsize="9" color="textoff3" align="center" text="Start: Cue 1 | Cutoff: Cue 2"/>
			</textzone>
		</group>

		<!-- SEPARATOR LINE -->
		<line x="+12" y="+230" width="368" height="1" color="bordercolor" />

		<!-- BOTTOM ACTIONS: RELOAD / LOAD BUTTONS -->
		<group name="sm_bottom_actions" x="+12" y="+236">
			<button class="button_master" x="+0" y="+0" width="180" height="26" action="deck 1 volume 100% &amp; deck 1 load 'C:\Users\odhis\Videos\Zzero Sufuri Otero Ft Toxic Lyrikali (Official Music Video) (via DW YouTube Downloader).mkv' &amp; deck 1 goto_cue 1" text="LOAD TO DECK A" tooltip="Load Zzero Sufuri Otero onto Deck A at Cue 1" />
			<button class="button_master" x="+188" y="+0" width="180" height="26" action="deck 2 volume 100% &amp; deck 2 load 'C:\Users\odhis\Downloads\Toxic Lyrikali - Lowkey (Official Video).mp3' &amp; deck 2 goto_cue 1" text="LOAD TO DECK B" tooltip="Load Toxic Lyrikali Lowkey onto Deck B at Cue 1" />
		</group>
	</panel>"""

skin_files = [
    r"C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml",
    r"C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix\Essentials.xml"
]

for sf in skin_files:
    if os.path.exists(sf):
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()
        p_start = content.find('<panel name="smartmix_panel"')
        p_end = content.find('</panel>', p_start) + len('</panel>')
        content = content[:p_start] + new_panel_code + content[p_end:]
        with open(sf, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated skin file:", sf)

# Repack SmartMix.zip for both AppData and Documents
zip_dirs = [
    (r"C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix", r"C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix.zip"),
    (r"C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix", r"C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix.zip")
]

for src_dir, zip_dest in zip_dirs:
    if os.path.exists(src_dir):
        with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, src_dir)
                    zf.write(full_p, rel_p)
        print("Repacked zip:", zip_dest)
