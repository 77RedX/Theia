from PIL import Image

# Open the image
img = Image.open('assets/icon.jpg')

# Ensure it's square. If not, crop it to the center square.
width, height = img.size
if width != height:
    min_dim = min(width, height)
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    right = (width + min_dim) / 2
    bottom = (height + min_dim) / 2
    img = img.crop((left, top, right, bottom))

# Save as ICO
img.save('app_icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print("Icon created successfully.")
