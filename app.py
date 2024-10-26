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

#ตั้งค่า route สำหรับหน้าแรกเพื่อแสดงเทมเพลต home.html
@app.route('/')
def home():
    return render_template('home.html')

#กำหนด route สำหรับการอัปโหลดภาพ ฟังก์ชันนี้จะตรวจสอบหากวิธีการร้องขอเป็น POST และไฟล์ภาพมีอยู่
#นำค่าจากฟอร์ม เช่น watermark_text, position, และ align มาจาก request ของผู้ใช้
@app.route('/add', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']

            if allowed_file(file.filename):
                watermark_text = request.form['watermark_text']
                position = request.form['position']
                align = request.form.get('align')

#เปิดไฟล์ภาพที่อัปโหลดและตรวจสอบว่าอยู่ในโหมด RGBA หรือไม่เพื่อให้รองรับความโปร่งใส หากไม่ใช่ จะทำการแปลงโหมดเป็น RGBA
                image = Image.open(file)

                if image.mode != 'RGBA':
                    image = image.convert('RGBA')

#สร้างเลเยอร์โปร่งใสในขนาดเดียวกับภาพต้นฉบับเพื่อให้รองรับการเพิ่มข้อความลายน้ำ ใช้ draw ในการวาดข้อความลงบนเลเยอร์
                txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(txt_layer)
                width, height = image.size

#กำหนดขนาดฟอนต์ของลายน้ำ
                font_size = int(width * 0.10)
                try:
                    if os.name == 'nt':
                        font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", font_size)
                    else:
                        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

#กำหนดขนาดความกว้างสูงสุดของลายน้ำเพื่อให้ลายน้ำไม่เกินขอบเขตของภาพ ใช้ textwrap เพื่อจัดข้อความตามขนาดที่กำหนด
                max_width = int(width * 0.9)
                wrapped_text = textwrap.fill(watermark_text, width=max_width // font_size)

#คำนวณขนาดของข้อความลายน้ำด้วยการใช้ textbbox เพื่อจัดตำแหน่งข้อความลายน้ำให้เหมาะสม
                bbox = draw.textbbox((0, 0), wrapped_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

#กำหนดตำแหน่ง x และ y ของข้อความลายน้ำตามการเลือกตำแหน่งของผู้ใช้ (top, bottom, หรือ center) 
# (ต่อ)รวมถึงจัดแนว (align) ด้านซ้ายหรือขวาสำหรับตำแหน่งบนและล่าง
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

#เพิ่มข้อความลายน้ำลงบนเลเยอร์ที่สร้างไว้ ใช้สีโปร่งแสงเพื่อไม่ให้ข้อความลายน้ำกลบรอยภาพต้นฉบับ
                transparent_color = (255, 255, 255, 120)
                draw.text((x, y), wrapped_text, fill=transparent_color, font=font)

#เพิ่มข้อความลิขสิทธิ์ด้านล่างของภาพ
                source_font_size = font_size // 3
                source_text = "© 2024 MarkFlow"
                try:
                    if os.name == 'nt':
                        source_font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", source_font_size)
                    else:
                        source_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", source_font_size)
                except IOError:
                    source_font = ImageFont.load_default()

#คำนวณขนาดข้อความลิขสิทธิ์และตำแหน่งที่เหมาะสมเพื่อแสดงลิขสิทธิ์ที่มุมล่างขวาของภาพ
                source_bbox = draw.textbbox((0, 0), source_text, font=source_font)
                source_text_width = source_bbox[2] - source_bbox[0]
                source_text_height = source_bbox[3] - source_bbox[1]

                source_x = width - source_text_width - margin
                source_y = height - source_text_height - margin

                draw.text((source_x, source_y), source_text, fill=transparent_color, font=source_font)

#ผสมเลเยอร์ของข้อความลายน้ำเข้ากับภาพต้นฉบับและแปลงกลับเป็น RGB เพื่อแสดงผล
                watermarked = Image.alpha_composite(image, txt_layer)
                watermarked = watermarked.convert('RGB')

#แปลงภาพที่มีลายน้ำให้เป็นฟอร์แมตไบต์ (BytesIO) และเข้ารหัสเป็น Base64 เพื่อใช้แสดงใน HTML
                img_io = BytesIO()
                watermarked.save(img_io, 'JPEG')
                img_io.seek(0)

                img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

#ส่งภาพที่มีลายน้ำกลับไปยังเทมเพลต index.html พร้อมกับข้อมูลการตั้งค่าลายน้ำ
                return render_template('index.html', img_data=img_base64, watermark_text=watermark_text, position=position, align=align)

#แสดงข้อความแจ้งเตือนหากไฟล์ที่อัปโหลดไม่ถูกต้อง หรือไม่ได้เลือกไฟล์ก่อนกดอัปโหลด
            else:
                flash('File type not allowed. Please upload a valid image file.')
                return redirect(request.url)

        else:
            flash('No file selected. Please upload a file.')
            return redirect(request.url)

#เมื่อใช้ GET จะโหลดเทมเพลต index.html
    return render_template('index.html')

@app.route('/remove')
def remove_watermark():
    return render_template('remove.html')

if __name__ == '__main__':
    app.run(debug=True)
