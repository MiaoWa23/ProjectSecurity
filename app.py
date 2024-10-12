import textwrap
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, redirect, url_for, flash
import os
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "supersecretkey"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        # แก้ไขจาก 'file' เป็น 'image' ให้ตรงกับ HTML
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']

            if allowed_file(file.filename):
                watermark_text = request.form['watermark_text']
                position = request.form['position']
                align = request.form.get('align')

                image = Image.open(file)

                if image.mode != 'RGBA':
                    image = image.convert('RGBA')

                txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))

                draw = ImageDraw.Draw(txt_layer)
                width, height = image.size

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
                    y = margin
                    if align == 'left':
                        x = margin
                    else:
                        x = width - text_width - margin
                elif position == 'bottom':
                    y = height - text_height - margin * 2.5
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

                transparent_color = (255, 255, 255, 120)
                draw.text((x, y), wrapped_text, fill=transparent_color, font=font)

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

@app.route('/remove')
def remove_watermark():
    return render_template('remove.html')

if __name__ == '__main__':
    app.run(debug=True)
