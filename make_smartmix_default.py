import os
import zipfile
from PIL import Image, ImageDraw, ImageFont

# 1. Update Essentials.xml to make smartmix_panel visible="yes" by default
skin_files = [
    r"C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml",
    r"C:\Users\odhis\Documents\VirtualDJ\Skins\SmartMix\Essentials.xml"
]

for sf in skin_files:
    if os.path.exists(sf):
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()

        # Set smartmix_panel to visible="yes"
        content = content.replace('<panel name="smartmix_panel" group="mixer" visible="no">', '<panel name="smartmix_panel" group="mixer" visible="yes">')
        
        # Set audiomixer to visible="no"
        content = content.replace('<panel name="audiomixer" group="mixer" visible="yes" >', '<panel name="audiomixer" group="mixer" visible="no" >')
        content = content.replace('<panel name="audiomixer" group="mixer" visible="yes">', '<panel name="audiomixer" group="mixer" visible="no">')

        with open(sf, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated panel visibility in:", sf)

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

# 2. Annotate the user's latest uploaded image
img_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\.user_uploaded\media_1792576083208_048b2449.png"
out_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\start_smartmix_exact_location.png"

img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

# The user's image is 1024x591.
# The "SMARTMIX" tab is at x: 505 to 555, y: 100 to 125.
# Draw bright neon yellow/green rectangle around the SMARTMIX tab
draw.rectangle([505, 98, 555, 126], outline=(255, 230, 0, 255), width=4)

# Draw an arrow pointing down to the SMARTMIX tab
# Arrow shaft
draw.line([(530, 20), (530, 95)], fill=(255, 230, 0, 255), width=6)
# Arrow head
draw.polygon([(515, 75), (545, 75), (530, 98)], fill=(255, 230, 0, 255))

# Draw callout banner above
draw.rectangle([340, 15, 720, 65], fill=(220, 20, 60, 230), outline="white", width=2)
draw.text((355, 22), "CLICK HERE: 'SMARTMIX' TAB", fill="white")
draw.text((355, 42), "Then 'START SMARTMIX' button will open below!", fill="yellow")

# Also draw a dashed box around the center mixer area indicating where the panel opens
draw.rectangle([315, 130, 560, 430], outline=(0, 255, 200, 200), width=3)
draw.text((325, 260), "SMARTMIX PANEL\n(Opens right here!)", fill=(0, 255, 200, 255))

img.save(out_path)
print("Saved annotated image to:", out_path)
