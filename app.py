import textwrap
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, redirect, url_for, flash
import os
from io import BytesIO
import base64
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # จำกัดขนาดไฟล์เป็น 2 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_text(text):
    if len(text) > 10:
        flash("Watermark text is too long. Please limit to 10 characters.")
        return False
    if "<" in text or ">" in text:
        flash("Invalid characters in watermark text.")
        return False
    return True

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            if allowed_file(file.filename):
                watermark_text = request.form['watermark_text']
                position = request.form['position']
                align = request.form.get('align')
                opacity = int(request.form.get('opacity', 120))  # ค่า opacity ที่เลือกจาก dropdown list

                if not validate_text(watermark_text):
                    return redirect(request.url)

                image = Image.open(file)

                if image.mode != 'RGBA':
                    image = image.convert('RGBA')

                txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(txt_layer)
                width, height = image.size

                if position == 'tiled':  # ตรวจสอบว่าผู้ใช้เลือกการกระจายทั่วภาพหรือไม่
                    tiled_font_size = int(width * 0.05)  # ขนาดฟอนต์เฉพาะสำหรับลายน้ำกระจาย
                    try:
                        if os.name == 'nt':
                            font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", tiled_font_size)
                        else:
                            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", tiled_font_size)
                    except IOError:
                        font = ImageFont.load_default()

                    transparent_color = (255, 255, 255, opacity)

                    # คำนวณระยะห่างระหว่างลายน้ำกระจาย
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    tile_x_spacing = text_width + 30
                    tile_y_spacing = text_height + 30

                    # วาดลายน้ำกระจายทั่วภาพ
                    for y in range(0, height, tile_y_spacing):
                        for x in range(0, width, tile_x_spacing):
                            draw.text((x, y), watermark_text, fill=transparent_color, font=font)
                else:
                    # สำหรับลายน้ำปกติที่มีตำแหน่งเฉพาะ
                    font_size = int(width * 0.10)
                    try:
                        if os.name == 'nt':
                            font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", font_size)
                        else:
                            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", font_size)
                    except IOError:
                        font = ImageFont.load_default()

                    max_width = int(width * 0.9)
                    wrapped_text = textwrap.fill(watermark_text, width=max_width // font_size)

                    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    margin = 20
                    if position == 'top':
                        y = margin - 35
                        if align == 'left':
                            x = margin
                        else:
                            x = width - text_width - margin
                    elif position == 'bottom':
                        y = height - text_height - margin * 2.4
                        if align == 'left':
                            x = margin
                        else:
                            x = width - text_width - margin
                    elif position == 'center':
                        x = (width - text_width) // 2
                        y = (height - text_height) // 2
                    else:
                        x = (width - text_width) // 2
                        y = (height - text_height) // 2

                    # ตั้งค่าโปร่งแสงสำหรับลายน้ำหลักตามค่า opacity ของผู้ใช้
                    transparent_color = (255, 255, 255, opacity)
                    draw.text((x, y), wrapped_text, fill=transparent_color, font=font)

                # ตั้งค่าโปร่งแสงของข้อความลิขสิทธิ์เป็นทึบแสงเต็มที่
                source_font_size = font_size // 3
                source_text = "© 2024 MarkFlow"
                try:
                    if os.name == 'nt':
                        source_font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", source_font_size)
                    else:
                        source_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", source_font_size)
                except IOError:
                    source_font = ImageFont.load_default()

                source_bbox = draw.textbbox((0, 0), source_text, font=source_font)
                source_text_width = source_bbox[2] - source_bbox[0]
                source_text_height = source_bbox[3] - source_bbox[1]

                source_x = width - source_text_width - margin
                source_y = height - source_text_height - margin

                # ใช้สีทึบแสงสำหรับ source_text
                source_text_color = (255, 255, 255, 255)
                draw.text((source_x, source_y), source_text, fill=source_text_color, font=source_font)

                watermarked = Image.alpha_composite(image, txt_layer)
                watermarked = watermarked.convert('RGB')

                img_io = BytesIO()
                watermarked.save(img_io, 'JPEG')
                img_io.seek(0)

                img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

                return render_template('index.html', img_data=img_base64, watermark_text=watermark_text, position=position, align=align)

            else:
                flash('File type not allowed. Please upload a valid image file.')
                return redirect(request.url)

        else:
            flash('No file selected. Please upload a file.')
            return redirect(request.url)

    return render_template('index.html')

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    flash("File size exceeds 2 MB. Please upload a smaller file.")
    return redirect(url_for('upload_image'))  # กลับไปยัง route upload_image เพื่อแสดง index.html

@app.route('/remove')
def remove_watermark():
    return render_template('remove.html')

if __name__ == '__main__':
    app.run(debug=True)
