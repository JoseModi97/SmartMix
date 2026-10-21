from PIL import Image

img_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\.user_uploaded\media_1792576083208_048b2449.png"
img = Image.open(img_path)

# Look at y around 80-140 across x: 250 to 600
# Let's crop y from 90 to 135 and x from 300 to 570
crop2 = img.crop((300, 95, 570, 130))
crop2.save(r"C:\Users\odhis\Downloads\SmartMix\tab_crop_exact.png")
print("Saved exact crop")
