from PIL import Image, ImageDraw, ImageFont
import os

# Ensure directory exists
os.makedirs("static/images", exist_ok=True)

# Image dimensions
width, height = 400, 100
background_color = (255, 255, 255, 0) # Transparent background

image = Image.new("RGBA", (width, height), background_color)
draw = ImageDraw.Draw(image)

# Text Settings
text_main = "SynthDetect"
text_suffix = "AI"
main_color = "#0B2C5D" # Deep Navy
suffix_color = "#F4C300" # Bright Yellow

try:
    # Try to load a nice font (Arial or similar if available on Windows)
    try:
        font = ImageFont.truetype("arialbd.ttf", 40)
    except:
        font = ImageFont.load_default()

    # Calculate text sizes
    bbox_main = draw.textbbox((0, 0), text_main, font=font)
    w_main = bbox_main[2] - bbox_main[0]
    
    bbox_suffix = draw.textbbox((0, 0), text_suffix, font=font)
    w_suffix = bbox_suffix[2] - bbox_suffix[0]
    
    total_text_width = w_main + 10 + w_suffix
    h = bbox_main[3] - bbox_main[1]
    
    # Position
    start_x = (width - total_text_width) // 2
    y = (height - h) // 2

    # Draw Text
    draw.text((start_x, y), text_main, fill=main_color, font=font)
    draw.text((start_x + w_main + 10, y), text_suffix, fill=suffix_color, font=font)
    
except Exception as e:
    print(f"Drawing error: {e}")
    # Fallback to simple rectangle
    draw.rectangle([0,0,width,height], fill="#0B2C5D")

# Save
image.save("static/images/logo.png")
print("SynthDetect AI logo created at static/images/logo.png") 
