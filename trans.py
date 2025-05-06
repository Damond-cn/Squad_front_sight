from PIL import Image

def white_to_transparent(image_path):
    img = Image.open(image_path)
    img = img.convert("RGBA")

    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save("6_transparent.png", "PNG")

if __name__ == "__main__":
    image_path = "img/M1REV.png"  # Replace with your image path
    white_to_transparent(image_path)
    print("Conversion complete. Transparent image saved as '6_transparent.png'.")