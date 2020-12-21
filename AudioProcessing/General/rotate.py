from PIL import Image

im = Image.open("messy.jpg")
im = im.rotate(90, expand=True)
im.save("messy.jpg")
