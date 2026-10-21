from PIL import Image, ImageDraw, ImageFont

img_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\.user_uploaded\media_1792575737628_dfe13039.png"
out_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\smartmix_location_guide.png"

img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

# 1. Box around SMARTMIX mixer tab (Center top of mixer)
draw.rectangle([1070, 175, 1155, 215], outline=(0, 255, 0, 255), width=4)
draw.rectangle([1000, 125, 1280, 165], fill=(0, 180, 0, 230), outline="white", width=2)
draw.text((1010, 135), "1. CLICK 'SMARTMIX' TAB HERE", fill="white")

# 2. Box around Top Header Bar
draw.rectangle([600, 5, 755, 36], outline=(255, 215, 0, 255), width=3)
draw.rectangle([540, 45, 820, 85], fill=(218, 165, 32, 230), outline="white", width=2)
draw.text((550, 55), "2. OR CLICK 'START SMARTMIX' HERE", fill="black")

img.save(out_path)
print("Updated guide image saved successfully.")
