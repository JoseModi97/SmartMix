smartmix_xml = '''
<!-- ===================================================================== -->
<!-- SMARTMIX NATIVE VIRTUALDJ EXTENSION - TAB BAR & BROWSER INTEGRATION  -->
<!-- ===================================================================== -->

<!-- 1. SmartMix Tab Switcher inside the SideView Header (Top of Automix/SideView) -->
<group name="smartmix_header_tabs">
	<panel name="sm_header_tabs">
		<pos x="1220" y="573"/>
		<size width="220" height="26"/>
		<!-- Automix Tab -->
		<button class="button_main" action="sideview 'automix' &amp; set '@$smartmix_active' 0" query="sideview 'automix' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+0" y="+0"/>
			<size width="105" height="24"/>
			<text text="Automix" fontsize="11" weight="bold"/>
		</button>
		<!-- SmartMix Tab (Immediately to the right of Automix) -->
		<button class="button_main" action="set '@$smartmix_active' 1" query="var_equal '@$smartmix_active' 1">
			<pos x="+110" y="+0"/>
			<size width="105" height="24"/>
			<text text="SmartMix" fontsize="11" weight="bold" color="browser_automix"/>
		</button>
	</panel>
</group>

<!-- 2. SmartMix Navigation Tab Bar across the bottom of the Browser (Over Native Bottom Tabs) -->
<group name="smartmix_sideview_tabs">
	<panel name="smartmix_tab_bar">
		<pos x="720" y="1036"/>
		<size width="950" height="34"/>

		<!-- Tab 1: Sidelist -->
		<button class="button_main" action="sideview 'sidelist' &amp; set '@$smartmix_active' 0" query="sideview 'sidelist' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+0" y="+0"/>
			<size width="145" height="32"/>
			<text text="Sidelist" fontsize="11"/>
		</button>

		<!-- Tab 2: Remixes -->
		<button class="button_main" action="sideview 'remixes' &amp; set '@$smartmix_active' 0" query="sideview 'remixes' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+150" y="+0"/>
			<size width="145" height="32"/>
			<text text="Remixes" fontsize="11"/>
		</button>

		<!-- Tab 3: Sampler -->
		<button class="button_main" action="sideview 'sampler' &amp; set '@$smartmix_active' 0" query="sideview 'sampler' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+300" y="+0"/>
			<size width="145" height="32"/>
			<text text="Sampler" fontsize="11"/>
		</button>

		<!-- Tab 4: Automix -->
		<button class="button_main" action="sideview 'automix' &amp; set '@$smartmix_active' 0" query="sideview 'automix' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+450" y="+0"/>
			<size width="145" height="32"/>
			<text text="Automix" fontsize="11"/>
		</button>

		<!-- Tab 5: SmartMix (Placed IMMEDIATELY AFTER Automix) -->
		<button class="button_main" action="set '@$smartmix_active' 1" query="var_equal '@$smartmix_active' 1">
			<pos x="+600" y="+0"/>
			<size width="155" height="32"/>
			<text text="SmartMix" fontsize="12" weight="bold" color="browser_automix"/>
		</button>

		<!-- Tab 6: Karaoke -->
		<button class="button_main" action="sideview 'karaoke' &amp; set '@$smartmix_active' 0" query="sideview 'karaoke' &amp;&amp; var_equal '@$smartmix_active' 0">
			<pos x="+760" y="+0"/>
			<size width="145" height="32"/>
			<text text="Karaoke" fontsize="11"/>
		</button>
	</panel>
</group>

<!-- 3. SmartMix Main Browser Panel (Occupies SideView footprint when SmartMix is active) -->
<panel name="smartmix_panel" visibility="var_equal '@$smartmix_active' 1">
	<pos x="1106" y="570"/>
	<size width="540" height="466"/>

	<square x="0" y="0" width="540" height="466" color="browserback" border="bordercolor" border_size="1"/>

	<!-- Top Control Bar -->
	<panel name="sm_toolbar">
		<pos x="0" y="0"/>
		<size width="540" height="42"/>
		<square x="0" y="0" width="540" height="42" color="browser_button" border="bordercolor" border_size="1"/>
		<text x="12" y="13" fontsize="13" weight="bold" color="texton" text="SMARTMIX ARRANGER"/>
		<text x="165" y="15" fontsize="10" color="browser_automix" text="EXACT CUE TRANSITIONS"/>

		<!-- Start / Stop Button -->
		<button class="button_main" action="var_equal '@$smartmix_running' 1 ? (set '@$smartmix_running' 0 &amp; automix off) : (set '@$smartmix_running' 1 &amp; automix on)" query="var_equal '@$smartmix_running' 1 ? on : off">
			<pos x="300" y="6"/>
			<size width="140" height="30"/>
			<text text="START SMARTMIX" fontsize="11" textcolor="textbright"/>
		</button>

		<!-- Edit Modal Toggle -->
		<button class="button_main" action="skin_panel 'smartmix_editor' toggle">
			<pos x="445" y="6"/>
			<size width="85" height="30"/>
			<text text="PRESETS ▼" fontsize="10"/>
		</button>
	</panel>

	<!-- Table Column Headers -->
	<panel name="sm_table_headers">
		<pos x="0" y="42"/>
		<size width="540" height="24"/>
		<square x="0" y="0" width="540" height="24" color="browserback" border="bordercolor" border_size="1"/>
		<text x="8" y="6" fontsize="10" weight="bold" color="textdark" text="#"/>
		<text x="25" y="6" fontsize="10" weight="bold" color="textdark" text="TRACK TITLE"/>
		<text x="195" y="6" fontsize="10" weight="bold" color="textdark" text="BPM"/>
		<text x="235" y="6" fontsize="10" weight="bold" color="textdark" text="TRIGGER CUE"/>
		<text x="325" y="6" fontsize="10" weight="bold" color="textdark" text="START CUE"/>
		<text x="405" y="6" fontsize="10" weight="bold" color="textdark" text="CUTOFF CUE"/>
		<text x="485" y="6" fontsize="10" weight="bold" color="textdark" text="STATUS"/>
	</panel>

	<!-- Track Row 1 -->
	<panel name="sm_row_1">
		<pos x="0" y="66"/>
		<size width="540" height="46"/>
		<square x="0" y="0" width="540" height="46" color="browserstripe" border="bordercolor" border_size="1"/>
		<square x="0" y="0" width="4" height="46" color="browser_automix"/>

		<text x="8" y="15" fontsize="11" weight="bold" color="browser_automix" text="1"/>
		<text x="25" y="8" fontsize="11" weight="bold" color="textbright" text="J Cole - The Blow Up (Instrumental)"/>
		<text x="25" y="25" fontsize="9" color="textdark" text="03:58 • Key: 8A"/>
		<text x="195" y="15" fontsize="11" weight="bold" color="texton" text="91.0"/>

		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="235" y="10"/>
			<size width="85" height="26"/>
			<text text="Cue 5 (02:30)" fontsize="9"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="325" y="10"/>
			<size width="75" height="26"/>
			<text text="Start (0:00)" fontsize="9"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="405" y="10"/>
			<size width="75" height="26"/>
			<text text="Cue 7 (02:45)" fontsize="9" textcolor="colormasterover"/>
		</button>
		<text x="485" y="15" fontsize="10" weight="bold" color="browser_automix" text="PLAYING"/>
	</panel>

	<!-- Track Row 2 -->
	<panel name="sm_row_2">
		<pos x="0" y="112"/>
		<size width="540" height="46"/>
		<square x="0" y="0" width="540" height="46" color="browserback" border="bordercolor" border_size="1"/>
		<text x="8" y="15" fontsize="11" weight="bold" color="textdark" text="2"/>
		<text x="25" y="8" fontsize="11" weight="bold" color="textbright" text="Kendrick Lamar - The Spiteful Chant"/>
		<text x="25" y="25" fontsize="9" color="textdark" text="04:22 • Key: 8A"/>
		<text x="195" y="15" fontsize="11" weight="bold" color="texton" text="91.0"/>

		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="235" y="10"/>
			<size width="85" height="26"/>
			<text text="Cue 4 (03:10)" fontsize="9"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="325" y="10"/>
			<size width="75" height="26"/>
			<text text="Cue 3 (00:15)" fontsize="9" textcolor="browser_scan"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="405" y="10"/>
			<size width="75" height="26"/>
			<text text="Cue 6 (03:30)" fontsize="9" textcolor="colormasterover"/>
		</button>
		<text x="485" y="15" fontsize="10" weight="bold" color="textbright" text="NEXT"/>
	</panel>

	<!-- Track Row 3 -->
	<panel name="sm_row_3">
		<pos x="0" y="158"/>
		<size width="540" height="46"/>
		<square x="0" y="0" width="540" height="46" color="browserstripe" border="bordercolor" border_size="1"/>
		<text x="8" y="15" fontsize="11" weight="bold" color="textdark" text="3"/>
		<text x="25" y="8" fontsize="11" weight="bold" color="textbright" text="PHY ft. King Kaka - RUKA"/>
		<text x="25" y="25" fontsize="9" color="textdark" text="03:45 • Key: 9A"/>
		<text x="195" y="15" fontsize="11" weight="bold" color="texton" text="95.0"/>

		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="235" y="10"/>
			<size width="85" height="26"/>
			<text text="Cue 6 (02:50)" fontsize="9"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="325" y="10"/>
			<size width="75" height="26"/>
			<text text="Cue 1 (00:20)" fontsize="9" textcolor="browser_scan"/>
		</button>
		<button class="button_main" action="skin_panel 'smartmix_editor' on">
			<pos x="405" y="10"/>
			<size width="75" height="26"/>
			<text text="Cue 8 (03:15)" fontsize="9" textcolor="colormasterover"/>
		</button>
		<text x="485" y="15" fontsize="10" color="textdark" text="QUEUED"/>
	</panel>

	<!-- Bottom Safety & Automation Status -->
	<panel name="sm_bottom_status">
		<pos x="0" y="424"/>
		<size width="540" height="42"/>
		<square x="0" y="0" width="540" height="42" color="browser_button" border="bordercolor" border_size="1"/>
		<text x="10" y="8" fontsize="10" weight="bold" color="texton" text="Song A (Cue 5: 02:30) -> Song B (Cue 3: 00:15)"/>
		<text x="10" y="22" fontsize="9" color="browser_scan" text="Audio past Cutoff (02:45) is 100% excluded. Non-destructive."/>

		<button class="button_main" action="skin_panel 'smartmix_editor' toggle">
			<pos x="420" y="7"/>
			<size width="110" height="28"/>
			<text text="EDIT TRANSITION" fontsize="9"/>
		</button>
	</panel>
</panel>

<!-- 4. SmartMix Transition Editor Modal -->
<panel name="smartmix_editor" visible="no">
	<pos x="1106" y="570"/>
	<size width="540" height="466"/>
	<square x="0" y="0" width="540" height="466" color="browserback" border="bordercolor" border_size="2"/>

	<!-- Header -->
	<square x="0" y="0" width="540" height="40" color="browser_button" border="bordercolor" border_size="1"/>
	<text x="12" y="13" fontsize="12" weight="bold" color="textbright" text="TRANSITION EDITOR - CUE AUTOMATION"/>
	<button class="button_main" action="skin_panel 'smartmix_editor' off">
		<pos x="505" y="6"/>
		<size width="28" height="26"/>
		<text text="X" fontsize="11"/>
	</button>

	<!-- Song A Box -->
	<square x="10" y="48" width="520" height="100" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="18" y="58" fontsize="11" weight="bold" color="texton" text="OUTGOING (Song A): J Cole - The Blow Up"/>
	<text x="18" y="78" fontsize="9" color="textdark" text="Trigger Cue (Starts Song B immediately without beat waiting):"/>
	<button class="button_main">
		<pos x="18" y="98"/>
		<size width="150" height="28"/>
		<text text="Cue 5 (02:30)" fontsize="10" color="browser_automix"/>
	</button>

	<text x="190" y="78" fontsize="9" color="textdark" text="Cutoff Cue (Song A stops immediately. Audio past this is cut):"/>
	<button class="button_main">
		<pos x="190" y="98"/>
		<size width="150" height="28"/>
		<text text="Cue 7 (02:45)" fontsize="10" textcolor="colormasterover"/>
	</button>

	<!-- Song B Box -->
	<square x="10" y="156" width="520" height="88" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="18" y="166" fontsize="11" weight="bold" color="texton" text="INCOMING (Song B): Kendrick Lamar - The Spiteful Chant"/>
	<text x="18" y="186" fontsize="9" color="textdark" text="Start Cue (Song B starts immediately from this point):"/>
	<button class="button_main">
		<pos x="18" y="206"/>
		<size width="150" height="28"/>
		<text text="Cue 3 (00:15)" fontsize="10" color="browser_scan"/>
	</button>
	<button class="button_main">
		<pos x="190" y="206"/>
		<size width="150" height="28"/>
		<text text="BPM Sync: Instant Lock" fontsize="10" textcolor="textbright"/>
	</button>

	<!-- Curves & EQ Box -->
	<square x="10" y="252" width="520" height="135" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="18" y="262" fontsize="11" weight="bold" color="texton" text="AUTOMATION PROFILE &amp; EQ CROSSOVER"/>
	<text x="18" y="284" fontsize="9" color="textdark" text="Fade Curve:"/>

	<button class="button_main">
		<pos x="18" y="302"/>
		<size width="100" height="26"/>
		<text text="Smooth Fade" fontsize="9" textcolor="textbright"/>
	</button>
	<button class="button_main">
		<pos x="124" y="302"/>
		<size width="75" height="26"/>
		<text text="Linear" fontsize="9"/>
	</button>
	<button class="button_main">
		<pos x="205" y="302"/>
		<size width="95" height="26"/>
		<text text="Equal Power" fontsize="9"/>
	</button>
	<button class="button_main">
		<pos x="306" y="302"/>
		<size width="75" height="26"/>
		<text text="Sharp Cut" fontsize="9"/>
	</button>

	<text x="18" y="340" fontsize="9" color="textdark" text="EQ Automation: Bass Swap at 50% midpoint • Prevents low-end mud"/>
	<text x="18" y="358" fontsize="9" color="browser_scan" text="Safety: Audio after 02:45 is strictly excluded from master playback."/>

	<!-- Close Button -->
	<button class="button_main" action="skin_panel 'smartmix_editor' off">
		<pos x="410" y="415"/>
		<size width="120" height="32"/>
		<text text="SAVE &amp; CLOSE" fontsize="10" color="browser_automix"/>
	</button>
</panel>
'''

import glob, zipfile, os

base_extracted = r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\Essentials.xml'
with open(base_extracted, 'r', encoding='utf-8') as f:
    base_xml = f.read()

new_essentials = base_xml.replace('</skin>', smartmix_xml + '\n</skin>')

skin_targets = [
    r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml',
    r'C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix\Essentials.xml',
    r'C:\Users\odhis\OneDrive\Documents\VirtualDJ\Skins\SmartMix\Essentials.xml'
]

for t in skin_targets:
    if os.path.exists(os.path.dirname(t)):
        with open(t, 'w', encoding='utf-8') as f:
            f.write(new_essentials)
        print('Updated:', t)

# Re-create SmartMix.zip in all locations
for skin_dir in [r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins', r'C:\Users\odhis\Documents\VirtualDJ\Skins', r'C:\Users\odhis\OneDrive\Documents\VirtualDJ\Skins']:
    src_dir = os.path.join(skin_dir, 'SmartMix')
    zip_path = os.path.join(skin_dir, 'SmartMix.zip')
    if os.path.exists(src_dir):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, src_dir)
                    zf.write(full_p, rel_p)
        print('Re-zipped:', zip_path)
