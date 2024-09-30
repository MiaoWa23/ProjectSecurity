from flask import Flask, render_template, request
from PIL import Image, ImageDraw, ImageFont
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_watermark(image_path, watermark_text, position, align):
    image = Image.open(image_path)
    drawable = ImageDraw.Draw(image)

    # เลือกฟอนต์
    font = ImageFont.load_default()

    # กำหนดขนาดของลายน้ำโดยใช้ textbbox()
    bbox = drawable.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]  # คำนวณความกว้างของข้อความ
    text_height = bbox[3] - bbox[1]  # คำนวณความสูงของข้อความ

    # คำนวณตำแหน่งของลายน้ำ
    if position == 'top':
        y = 10
    elif position == 'bottom':
        y = image.height - text_height - 10
    elif position == 'diagonal':
        y = (image.height - text_height) // 2

    if align == 'left':
        x = 10
    elif align == 'right':
        x = image.width - text_width - 10
    else:
        x = (image.width - text_width) // 2

    if position == 'diagonal':
        drawable.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
    else:
        drawable.text((x, y), watermark_text, font=font, fill=(255, 255, 255))

    # บันทึกไฟล์ภาพใหม่ที่มีลายน้ำ
    watermark_path = os.path.join(app.config['UPLOAD_FOLDER'], 'watermarked_' + os.path.basename(image_path))
    image.save(watermark_path)

    return watermark_path


@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files or 'watermark_text' not in request.form:
        return render_template('index.html', message="Please select a file and provide watermark text")

    file = request.files['file']
    watermark_text = request.form['watermark_text']
    position = request.form.get('position')
    align = request.form.get('align', 'center')  # เลือกซ้ายหรือขวา

    if file.filename == '':
        return render_template('index.html', message="No file selected")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # ใส่ลายน้ำ
        watermarked_path = add_watermark(filepath, watermark_text, position, align)
        return render_template('index.html', filename='watermarked_' + filename)

    return render_template('index.html', message="File type not allowed")

if __name__ == "__main__":
    app.run(debug=True)
