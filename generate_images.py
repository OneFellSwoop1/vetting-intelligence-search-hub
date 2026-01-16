#!/usr/bin/env python3
"""
Generate placeholder social media and favicon images for POISSON AI®
This creates functional placeholder images that can be replaced later with custom designs.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

# Configuration
LOGO_PATH = "frontend/public/images/poissonai_logo.png"
OUTPUT_DIR = "frontend/public/images"

# Brand colors (from your theme)
BRAND_PURPLE = (99, 102, 241)  # #6366f1
BRAND_DARK = (15, 23, 42)      # #0f172a
BRAND_BLUE = (59, 130, 246)    # #3b82f6

def create_gradient_background(width, height, color1, color2):
    """Create a gradient background"""
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def add_text_to_image(image, text, font_size=60, y_position=None):
    """Add text overlay to image"""
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # Try to use a nice font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (width - text_width) // 2
    if y_position is None:
        y = (height - text_height) // 2
    else:
        y = y_position
    
    # Draw text with shadow for better visibility
    shadow_offset = 3
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    return image

def create_social_image(output_path, title, subtitle=None):
    """Create social media preview image (1200×630)"""
    width, height = 1200, 630
    
    # Create gradient background
    img = create_gradient_background(width, height, BRAND_DARK, BRAND_PURPLE)
    
    # Try to load and add logo
    try:
        logo = Image.open(LOGO_PATH)
        # Resize logo to fit nicely
        logo_size = 250
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Add logo with rounded corners and glow effect
        logo_pos = ((width - logo_size) // 2, 80)
        
        # Create glow effect
        glow = Image.new('RGBA', (logo_size + 40, logo_size + 40), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse([0, 0, logo_size + 40, logo_size + 40], fill=(*BRAND_PURPLE, 80))
        glow = glow.filter(ImageFilter.GaussianBlur(20))
        img.paste(glow, (logo_pos[0] - 20, logo_pos[1] - 20), glow)
        
        # Paste logo
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        img.paste(logo, logo_pos, logo)
        
    except Exception as e:
        print(f"Warning: Could not load logo: {e}")
    
    # Add text
    img = add_text_to_image(img, title, font_size=72, y_position=370)
    
    if subtitle:
        img = add_text_to_image(img, subtitle, font_size=36, y_position=460)
    
    # Add subtle pattern overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(0, width, 100):
        for j in range(0, height, 100):
            draw.ellipse([i, j, i+10, j+10], fill=(*BRAND_BLUE, 20))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    # Save
    img.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"✅ Created: {output_path}")

def create_favicon(size, output_path):
    """Create favicon at specified size"""
    try:
        logo = Image.open(LOGO_PATH)
        
        # Create a square canvas with gradient background
        canvas = create_gradient_background(size, size, BRAND_DARK, BRAND_PURPLE)
        
        # Resize logo to fit (with some padding)
        logo_size = int(size * 0.8)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Center logo on canvas
        pos = ((size - logo_size) // 2, (size - logo_size) // 2)
        
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        canvas.paste(logo, pos, logo)
        
        # Save
        canvas.save(output_path, 'PNG', quality=95)
        print(f"✅ Created: {output_path} ({size}×{size})")
        
    except Exception as e:
        print(f"❌ Error creating {output_path}: {e}")

def create_ico_favicon():
    """Create multi-size favicon.ico"""
    try:
        sizes = [16, 32, 48]
        images = []
        
        for size in sizes:
            logo = Image.open(LOGO_PATH)
            canvas = create_gradient_background(size, size, BRAND_DARK, BRAND_PURPLE)
            logo_size = int(size * 0.8)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            pos = ((size - logo_size) // 2, (size - logo_size) // 2)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            canvas.paste(logo, pos, logo)
            images.append(canvas)
        
        output_path = os.path.join(OUTPUT_DIR, 'favicon.ico')
        images[0].save(output_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
        print(f"✅ Created: {output_path} (multi-size)")
        
    except Exception as e:
        print(f"❌ Error creating favicon.ico: {e}")

def main():
    """Generate all required images"""
    print("🎨 Generating placeholder images for POISSON AI®...\n")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check if logo exists
    if not os.path.exists(LOGO_PATH):
        print(f"❌ Logo not found at {LOGO_PATH}")
        print("Please make sure the logo file exists and try again.")
        return
    
    # 1. Create social media images
    print("📱 Creating social media preview images...")
    create_social_image(
        os.path.join(OUTPUT_DIR, 'og-image.png'),
        'POISSON AI®',
        'Vetting Intelligence Search Hub'
    )
    
    create_social_image(
        os.path.join(OUTPUT_DIR, 'twitter-image.png'),
        'POISSON AI®',
        'Government Transparency Platform'
    )
    
    # 2. Create favicon files
    print("\n🎯 Creating favicon files...")
    
    # Standard favicons
    create_favicon(16, os.path.join(OUTPUT_DIR, 'favicon-16x16.png'))
    create_favicon(32, os.path.join(OUTPUT_DIR, 'favicon-32x32.png'))
    
    # Apple touch icon
    create_favicon(180, os.path.join(OUTPUT_DIR, 'apple-touch-icon.png'))
    
    # Android icons
    create_favicon(192, os.path.join(OUTPUT_DIR, 'android-chrome-192x192.png'))
    create_favicon(512, os.path.join(OUTPUT_DIR, 'android-chrome-512x512.png'))
    
    # Multi-size ICO
    create_ico_favicon()
    
    print("\n✨ All placeholder images created successfully!")
    print("\n📝 Note: These are functional placeholders. Consider creating")
    print("   custom designs with AI tools (Canva, DALL-E) for launch.")
    print("\n📁 Images saved to: frontend/public/images/")

if __name__ == "__main__":
    main()
