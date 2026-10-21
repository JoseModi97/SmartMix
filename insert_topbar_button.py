import os
import zipfile

topbar_button = """
	<!-- TOP BAR QUICK ACCESS: START SMARTMIX BUTTON -->
	<group name="topbar_smartmix" x="600" y="6">
		<button class="button_master" x="+0" y="+0" width="155" height="30" action="var '@$smartmix_running' ? set '@$smartmix_running' 0 &amp; repeat_stop 'smartmix_watch' : set '@$smartmix_running' 1 &amp; skin_panel 'smartmix_panel' on &amp; (deck 1 play ? nothing : deck 2 play ? nothing : deck 1 volume 100% &amp; deck 1 goto_cue 1 &amp; deck 1 play) &amp; repeat_start 'smartmix_watch' 50ms &amp; (deck 1 play ? (deck 1 has_cue 2 ? (param_bigger `deck 1 songpos` `deck 1 cue_pos 2` ? deck 2 volume 100% &amp; deck 2 match_bpm &amp; deck 2 goto_cue 1 &amp; deck 2 play &amp; deck 1 stop &amp; deck 1 volume 0% &amp; crossfader 100% : nothing) : nothing) : (deck 2 play ? (deck 2 has_cue 2 ? (param_bigger `deck 2 songpos` `deck 2 cue_pos 2` ? deck 1 volume 100% &amp; deck 1 match_bpm &amp; deck 1 goto_cue 1 &amp; deck 1 play &amp; deck 2 stop &amp; deck 2 volume 0% &amp; crossfader 0% : nothing) : nothing) : nothing))" text="START SMARTMIX" textaction="var '@$smartmix_running' ? 'SMARTMIX ON (STOP)' : 'START SMARTMIX'" tooltip="Start Automated Cue-Based SmartMix and open SmartMix Editor" />
	</group>
"""

skin_files = [
    r"C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml",
    r"C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix\Essentials.xml"
]

for sf in skin_files:
    if os.path.exists(sf):
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove old topbar_smartmix if already present
        if '<group name="topbar_smartmix"' in content:
            pos_old = content.find('<group name="topbar_smartmix"')
            pos_old_end = content.find('</group>', pos_old) + len('</group>')
            content = content[:pos_old] + content[pos_old_end:]

        # Insert right after </group> of sandbox
        pos_sb = content.find('name="sandbox"')
        if pos_sb != -1:
            sb_end = content.find('</group>', pos_sb) + len('</group>')
            content = content[:sb_end] + topbar_button + content[sb_end:]
            print("Inserted topbar_smartmix into:", sf)

        with open(sf, "w", encoding="utf-8") as f:
            f.write(content)

# Repack zips
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
