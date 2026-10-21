import os

xml_path = r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml'
with open(xml_path, 'r', encoding='utf-8') as f:
    content = f.read()

smartmix_xml = '''
<!-- ===================================================================== -->
<!-- SMARTMIX NATIVE VIRTUALDJ EXTENSION - TAB BAR & BROWSER INTEGRATION  -->
<!-- ===================================================================== -->

<!-- SmartMix Navigation Tab Bar across the bottom of the SideView -->
<group name="smartmix_sideview_tabs">
	<panel name="smartmix_tab_bar" x="1245" y="1070-34" width="665" height="34">
		<square x="0" y="0" width="665" height="34" color="browserback" border="bordercolor" border_size="1"/>

		<!-- Tab 1: Sidelist -->
		<button class="button_main" x="0" y="2" width="108" height="30" text="Sidelist" textsize="12"
			action="sideview 'sidelist' &amp; set '@$smartmix_active' 0"
			query="sideview 'sidelist' &amp;&amp; var_equal '@$smartmix_active' 0"/>

		<!-- Tab 2: Remixes -->
		<button class="button_main" x="110" y="2" width="108" height="30" text="Remixes" textsize="12"
			action="sideview 'remixes' &amp; set '@$smartmix_active' 0"
			query="sideview 'remixes' &amp;&amp; var_equal '@$smartmix_active' 0"/>

		<!-- Tab 3: Sampler -->
		<button class="button_main" x="220" y="2" width="108" height="30" text="Sampler" textsize="12"
			action="sideview 'sampler' &amp; set '@$smartmix_active' 0"
			query="sideview 'sampler' &amp;&amp; var_equal '@$smartmix_active' 0"/>

		<!-- Tab 4: Automix -->
		<button class="button_main" x="330" y="2" width="108" height="30" text="Automix" textsize="12"
			action="sideview 'automix' &amp; set '@$smartmix_active' 0"
			query="sideview 'automix' &amp;&amp; var_equal '@$smartmix_active' 0"/>

		<!-- Tab 5: SmartMix (Placed IMMEDIATELY AFTER Automix) -->
		<button class="button_main" x="440" y="2" width="112" height="30" text="SmartMix" textsize="12" textcolor="browser_automix"
			action="set '@$smartmix_active' 1"
			query="var_equal '@$smartmix_active' 1"/>

		<!-- Tab 6: Karaoke -->
		<button class="button_main" x="554" y="2" width="109" height="30" text="Karaoke" textsize="12"
			action="sideview 'karaoke' &amp; set '@$smartmix_active' 0"
			query="sideview 'karaoke' &amp;&amp; var_equal '@$smartmix_active' 0"/>
	</panel>
</group>

<!-- SmartMix Main Browser Panel (Active when SmartMix tab is selected) -->
<panel name="smartmix_panel" x="1245" y="1080-500-10" width="665" height="466" visibility="var_equal '@$smartmix_active' 1">
	<square x="0" y="0" width="665" height="466" color="browserback" border="bordercolor" border_size="1"/>

	<!-- Top Toolbar -->
	<panel name="sm_toolbar" x="0" y="0" width="665" height="44">
		<square x="0" y="0" width="665" height="44" color="browser_button" border="bordercolor" border_size="1"/>
		<text x="14" y="13" fontsize="14" weight="bold" color="texton" text="SMARTMIX ARRANGER"/>
		<text x="180" y="15" fontsize="10" color="browser_automix" text="EXACT CUE TRANSITIONS"/>

		<!-- Start / Stop SmartMix Button -->
		<button class="button_main" x="380" y="7" width="140" height="30"
			text="START SMARTMIX" textsize="11" textcolor="textbright"
			action="var_equal '@$smartmix_running' 1 ? (set '@$smartmix_running' 0 &amp; automix off) : (set '@$smartmix_running' 1 &amp; automix on)"
			query="var_equal '@$smartmix_running' 1 ? on : off"/>

		<!-- Pause Button -->
		<button class="button_main" x="525" y="7" width="60" height="30" text="PAUSE" textsize="11"
			action="pause" query="pause"/>

		<!-- Options Menu Button -->
		<button class="button_main" x="590" y="7" width="65" height="30" text="PRESET" textsize="11"
			action="skin_panel 'smartmix_editor' toggle"/>
	</panel>

	<!-- Table Column Headers -->
	<panel name="sm_table_headers" x="0" y="44" width="665" height="26">
		<square x="0" y="0" width="665" height="26" color="browserback" border="bordercolor" border_size="1"/>
		<text x="10" y="7" fontsize="10" weight="bold" color="textdark" text="#"/>
		<text x="32" y="7" fontsize="10" weight="bold" color="textdark" text="TRACK TITLE / ARTIST"/>
		<text x="240" y="7" fontsize="10" weight="bold" color="textdark" text="BPM"/>
		<text x="290" y="7" fontsize="10" weight="bold" color="textdark" text="TRIGGER CUE"/>
		<text x="395" y="7" fontsize="10" weight="bold" color="textdark" text="START CUE"/>
		<text x="485" y="7" fontsize="10" weight="bold" color="textdark" text="CUTOFF CUE"/>
		<text x="585" y="7" fontsize="10" weight="bold" color="textdark" text="STATUS"/>
	</panel>

	<!-- Row 1 (Now Playing Track A) -->
	<panel name="sm_row_1" x="0" y="70" width="665" height="48">
		<square x="0" y="0" width="665" height="48" color="browserstripe" border="bordercolor" border_size="1"/>
		<!-- Status Accent Line -->
		<square x="0" y="0" width="4" height="48" color="browser_automix"/>

		<text x="10" y="16" fontsize="12" weight="bold" color="browser_automix" text="1"/>
		<text x="32" y="8" fontsize="12" weight="bold" color="textbright" text="J Cole - The Blow Up (Instrumental)"/>
		<text x="32" y="26" fontsize="10" color="textdark" text="03:58 • Key: 8A • Rap/Hip-Hop"/>

		<text x="240" y="16" fontsize="12" weight="bold" color="texton" text="91.0"/>

		<!-- Trigger Cue Selector Button -->
		<button class="button_main" x="290" y="10" width="95" height="28" text="Cue 5 (02:30)" textsize="10"
			action="skin_panel 'smartmix_editor' on"/>

		<!-- Incoming Start Cue Button (N/A for track 1) -->
		<button class="button_main" x="395" y="10" width="80" height="28" text="Start (0:00)" textsize="10"
			action="skin_panel 'smartmix_editor' on"/>

		<!-- Cutoff Cue Selector Button -->
		<button class="button_main" x="485" y="10" width="90" height="28" text="Cue 7 (02:45)" textsize="10" textcolor="colormasterover"
			action="skin_panel 'smartmix_editor' on"/>

		<text x="585" y="16" fontsize="11" weight="bold" color="browser_automix" text="PLAYING"/>
	</panel>

	<!-- Row 2 (Next Track B) -->
	<panel name="sm_row_2" x="0" y="118" width="665" height="48">
		<square x="0" y="0" width="665" height="48" color="browserback" border="bordercolor" border_size="1"/>
		<text x="10" y="16" fontsize="12" weight="bold" color="textdark" text="2"/>
		<text x="32" y="8" fontsize="12" weight="bold" color="textbright" text="Kendrick Lamar - The Spiteful Chant"/>
		<text x="32" y="26" fontsize="10" color="textdark" text="04:22 • Key: 8A • Instrumental"/>

		<text x="240" y="16" fontsize="12" weight="bold" color="texton" text="91.0"/>

		<!-- Trigger Cue Selector Button -->
		<button class="button_main" x="290" y="10" width="95" height="28" text="Cue 4 (03:10)" textsize="10"
			action="skin_panel 'smartmix_editor' on"/>

		<!-- Incoming Start Cue Selector Button -->
		<button class="button_main" x="395" y="10" width="80" height="28" text="Cue 3 (00:15)" textsize="10" textcolor="browser_scan"
			action="skin_panel 'smartmix_editor' on"/>

		<!-- Cutoff Cue Selector Button -->
		<button class="button_main" x="485" y="10" width="90" height="28" text="Cue 6 (03:30)" textsize="10" textcolor="colormasterover"
			action="skin_panel 'smartmix_editor' on"/>

		<text x="585" y="16" fontsize="11" weight="bold" color="textbright" text="NEXT"/>
	</panel>

	<!-- Row 3 (Queued Track C) -->
	<panel name="sm_row_3" x="0" y="166" width="665" height="48">
		<square x="0" y="0" width="665" height="48" color="browserstripe" border="bordercolor" border_size="1"/>
		<text x="10" y="16" fontsize="12" weight="bold" color="textdark" text="3"/>
		<text x="32" y="8" fontsize="12" weight="bold" color="textbright" text="PHY ft. King Kaka &amp; Khaligraph - RUKA"/>
		<text x="32" y="26" fontsize="10" color="textdark" text="03:45 • Key: 9A • Afro Hip-Hop"/>

		<text x="240" y="16" fontsize="12" weight="bold" color="texton" text="95.0"/>

		<button class="button_main" x="290" y="10" width="95" height="28" text="Cue 6 (02:50)" textsize="10"
			action="skin_panel 'smartmix_editor' on"/>

		<button class="button_main" x="395" y="10" width="80" height="28" text="Cue 1 (00:20)" textsize="10" textcolor="browser_scan"
			action="skin_panel 'smartmix_editor' on"/>

		<button class="button_main" x="485" y="10" width="90" height="28" text="Cue 8 (03:15)" textsize="10" textcolor="colormasterover"
			action="skin_panel 'smartmix_editor' on"/>

		<text x="585" y="16" fontsize="11" color="textdark" text="QUEUED"/>
	</panel>

	<!-- Row 4 (Queued Track D) -->
	<panel name="sm_row_4" x="0" y="214" width="665" height="48">
		<square x="0" y="0" width="665" height="48" color="browserback" border="bordercolor" border_size="1"/>
		<text x="10" y="16" fontsize="12" weight="bold" color="textdark" text="4"/>
		<text x="32" y="8" fontsize="12" weight="bold" color="textbright" text="Drake - 0 to 100 (Instrumental)"/>
		<text x="32" y="26" fontsize="10" color="textdark" text="04:35 • Key: 8A • Instrumental"/>

		<text x="240" y="16" fontsize="12" weight="bold" color="texton" text="90.0"/>

		<button class="button_main" x="290" y="10" width="95" height="28" text="Cue 5 (03:00)" textsize="10"
			action="skin_panel 'smartmix_editor' on"/>

		<button class="button_main" x="395" y="10" width="80" height="28" text="Cue 2 (00:00)" textsize="10" textcolor="browser_scan"
			action="skin_panel 'smartmix_editor' on"/>

		<button class="button_main" x="485" y="10" width="90" height="28" text="Cue 7 (03:20)" textsize="10" textcolor="colormasterover"
			action="skin_panel 'smartmix_editor' on"/>

		<text x="585" y="16" fontsize="11" color="textdark" text="QUEUED"/>
	</panel>

	<!-- Bottom Transition Status & Safety Notice -->
	<panel name="sm_bottom_status" x="0" y="420" width="665" height="46">
		<square x="0" y="0" width="665" height="46" color="browser_button" border="bordercolor" border_size="1"/>
		<text x="14" y="10" fontsize="11" weight="bold" color="texton" text="Active Transition: Song A (Cue 5: 02:30) → Song B (Cue 3: 00:15)"/>
		<text x="14" y="26" fontsize="10" color="browser_scan" text="Audio past Cutoff (Cue 7: 02:45) is 100% excluded. Smooth 4-beat Equal Power crossfade."/>

		<button class="button_main" x="535" y="8" width="120" height="30" text="EDIT TRANSITION" textsize="10"
			action="skin_panel 'smartmix_editor' toggle"/>
	</panel>
</panel>

<!-- SmartMix Transition Automation Editor Modal -->
<panel name="smartmix_editor" x="1245" y="1080-500-10" width="665" height="466" visible="no">
	<square x="0" y="0" width="665" height="466" color="browserback" border="bordercolor" border_size="2"/>

	<!-- Editor Header -->
	<square x="0" y="0" width="665" height="44" color="browser_button" border="bordercolor" border_size="1"/>
	<text x="14" y="14" fontsize="13" weight="bold" color="textbright" text="TRANSITION EDITOR — EXACT CUE AUTOMATION"/>
	<button class="button_main" x="625" y="8" width="30" height="28" text="X" textsize="12"
		action="skin_panel 'smartmix_editor' off"/>

	<!-- Transition Details Box -->
	<square x="14" y="55" width="637" height="110" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="25" y="65" fontsize="11" weight="bold" color="texton" text="OUTGOING TRACK (Song A): J Cole - The Blow Up"/>
	<text x="25" y="85" fontsize="10" color="textdark" text="Trigger Cue: Song A reaches this cue -> Song B immediately starts."/>
	<button class="button_main" x="25" y="105" width="180" height="30" text="Trigger: Cue 5 (02:30)" textsize="11" textcolor="browser_automix"/>

	<text x="230" y="85" fontsize="10" color="textdark" text="Cutoff Cue: Song A stops immediately here. Audio past this is cut."/>
	<button class="button_main" x="230" y="105" width="180" height="30" text="Cutoff: Cue 7 (02:45)" textsize="11" textcolor="colormasterover"/>

	<!-- Incoming Details Box -->
	<square x="14" y="175" width="637" height="95" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="25" y="185" fontsize="11" weight="bold" color="texton" text="INCOMING TRACK (Song B): Kendrick Lamar - The Spiteful Chant"/>
	<text x="25" y="205" fontsize="10" color="textdark" text="Start Cue: Song B instantly plays from this cue without beat waiting."/>
	<button class="button_main" x="25" y="225" width="180" height="30" text="Start: Cue 3 (00:15)" textsize="11" textcolor="browser_scan"/>
	<button class="button_main" x="230" y="225" width="180" height="30" text="BPM Sync: Instant Locked" textsize="11" textcolor="textbright"/>

	<!-- Curve & EQ Automation Box -->
	<square x="14" y="280" width="637" height="120" color="browserstripe" radius="6" border="bordercolor" border_size="1"/>
	<text x="25" y="290" fontsize="11" weight="bold" color="texton" text="AUTOMATION PROFILE &amp; EQ CROSSOVER"/>

	<text x="25" y="315" fontsize="10" color="textdark" text="Volume Fade Curve:"/>
	<button class="button_main" x="25" y="335" width="120" height="28" text="Smooth Fade" textsize="10" textcolor="textbright"/>
	<button class="button_main" x="150" y="335" width="90" height="28" text="Linear" textsize="10"/>
	<button class="button_main" x="245" y="335" width="100" height="28" text="Equal Power" textsize="10"/>
	<button class="button_main" x="350" y="335" width="90" height="28" text="Sharp Cut" textsize="10"/>

	<text x="25" y="375" fontsize="10" color="textdark" text="EQ Automation: Bass Swap at midpoint • Mid/High Equal Blend • Cutoff stops Deck 1."/>

	<!-- Save / Cancel Buttons -->
	<button class="button_main" x="395" y="415" width="125" height="35" text="CANCEL" textsize="11"
		action="skin_panel 'smartmix_editor' off"/>
	<button class="button_main" x="526" y="415" width="125" height="35" text="SAVE CHANGES" textsize="11" textcolor="browser_automix"
		action="skin_panel 'smartmix_editor' off"/>
</panel>
'''

target = '</skin>'
if target in content:
    new_content = content.replace(target, smartmix_xml + '\n' + target)
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Successfully inserted SmartMix elements into Essentials.xml')
else:
    print('Target </skin> not found')
