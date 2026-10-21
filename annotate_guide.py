from PIL import Image, ImageDraw, ImageFont
import os

img_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\.user_uploaded\media_1792575737628_dfe13039.png"
out_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\smartmix_location_guide.png"

img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

# In the screenshot:
# Center mixer tab "SMARTMIX" is around:
# x: ~1075 to 1150
# y: ~175 to 215
draw.rectangle([1070, 175, 1155, 215], outline="red", width=4)

# Draw an arrow or callout text pointing to SMARTMIX tab
draw.rectangle([1000, 120, 1230, 165], fill=(255, 0, 0, 220), outline="white", width=2)

draw.text((1010, 130), "CLICK HERE: SMARTMIX", fill="white")

img.save(out_path)
print("Saved annotated image to:", out_path)
