import textwrap
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # สำหรับใช้กับฟังก์ชัน flash
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # กำหนดไฟล์นามสกุลที่อนุญาต

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def upload_image():
    filename = request.form.get('filename')  # รับค่าชื่อไฟล์หากถูกส่งกลับมาหลังจากเกิดข้อผิดพลาด
    file_path = None

    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']

            # ตรวจสอบว่านามสกุลไฟล์ถูกต้องหรือไม่
            if allowed_file(file.filename):
                filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)  # บันทึกไฟล์ที่อัปโหลด

            else:
                flash('File type not allowed. Please upload a PNG, JPG, or JPEG file.')
                return redirect(request.url)
        else:
            # ถ้าไม่มีไฟล์ใหม่ถูกอัปโหลด ให้ใช้ไฟล์ที่ถูกอัปโหลดแล้ว
            if filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if not os.path.exists(file_path):
                    flash('No file found, please upload a file.')
                    return redirect(request.url)
            else:
                flash('No file selected. Please upload a file.')
                return redirect(request.url)

        watermark_text = request.form['watermark_text']
        position = request.form['position']
        align = request.form.get('align')  # รับค่าซ้ายหรือขวา

        # ตรวจสอบว่าถ้าเลือกตำแหน่งบนหรือล่าง ต้องเลือกซ้ายหรือขวาด้วย
        if position in ['top', 'bottom'] and not align:
            flash('Please select left or right alignment when position is top or bottom.')
            return render_template('index.html', watermark_text=watermark_text, position=position, align=align, filename=filename)

        if file_path and watermark_text:
            image = Image.open(file_path)

            # แปลงภาพเป็นโหมด RGBA เพื่อรองรับความโปร่งใส
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # สร้างเลเยอร์ใหม่เพื่อเพิ่มลายน้ำ
            txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))

            draw = ImageDraw.Draw(txt_layer)
            width, height = image.size

            # คำนวณขนาดฟอนต์ใหม่
            font_size = int(width * 0.10)  # ลดขนาดฟอนต์จาก 10% ของความกว้างเป็น 7%
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

            # ตัดบรรทัดอัตโนมัติหากข้อความยาวเกินไป
            max_width = int(width * 0.9)
            wrapped_text = textwrap.fill(watermark_text, width=max_width // font_size)

            # คำนวณขนาดของข้อความลายน้ำหลังจากตัดบรรทัด
            bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # ตั้งค่าตำแหน่งของลายน้ำพร้อมเว้นระยะขอบ
            margin = 20  # เว้นระยะขอบ 20 พิกเซล
            if position == 'top':
                y = margin
                if align == 'left':
                    x = margin
                else:
                    x = width - text_width - margin
            elif position == 'bottom':
                y = height - text_height - margin
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

            # เพิ่มข้อความลายน้ำที่มีความโปร่งใส (RGBA)
            transparent_color = (255, 255, 255, 120)  # สีขาวกึ่งโปร่งใส
            draw.text((x, y), wrapped_text, fill=transparent_color, font=font)

            # รวมเลเยอร์ข้อความเข้ากับภาพต้นฉบับ
            watermarked = Image.alpha_composite(image, txt_layer)

            # แปลงกลับเป็นโหมด RGB เพื่อบันทึกเป็น JPEG
            watermarked = watermarked.convert('RGB')

            # บันทึกรูปภาพที่มีลายน้ำ
            watermarked.save(file_path, 'JPEG')

            # แสดงภาพหลังจากใส่ลายน้ำเสร็จแล้ว
            return render_template('index.html', filename=filename, watermark_text=watermark_text, position=position, align=align)

    return render_template('index.html', filename=filename)


@app.route('/remove')
def remove_watermark():
    return render_template('remove.html')


if __name__ == '__main__':
    app.run(debug=True)
