from PIL import Image

def trim_transparency(image_path):
    try:
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get bounding box of non-zero alpha pixels
        bbox = img.getbbox()
        if bbox:
            print(f"Original size: {img.size}")
            print(f"Trimming tobbox: {bbox}")
            cropped = img.crop(bbox)
            cropped.save(image_path)
            print(f"New size: {cropped.size}")
        else:
            print("Image is fully transparent or empty.")
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    trim_transparency("static/images/logo.png")
