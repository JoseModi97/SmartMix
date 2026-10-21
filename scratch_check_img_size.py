from PIL import Image

img_path = r"C:\Users\odhis\.gemini\antigravity\brain\71a76d99-7a1d-4839-9b89-4e53eb8e4af8\.user_uploaded\media_1792576083208_048b2449.png"
img = Image.open(img_path)
print("Image size:", img.size)
