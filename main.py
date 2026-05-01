from flask import Flask, request, send_file, render_template
from PIL import Image, ImageOps
from PyPDF2 import PdfMerger, PdfReader
import io
from datetime import datetime

app = Flask(__name__)

A4_WIDTH = 2480
A4_HEIGHT = 3508


def process_image(file, rotate=0):
    img = Image.open(file.stream)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    if rotate:
        img = img.rotate(-rotate, expand=True)

    return img


def fit_to_a4(img):
    page = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

    img.thumbnail((A4_WIDTH, A4_HEIGHT), Image.LANCZOS)

    x = (A4_WIDTH - img.width) // 2
    y = (A4_HEIGHT - img.height) // 2

    page.paste(img, (x, y))
    return page


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    files = request.files.getlist("files")
    rotations = request.form.getlist("rotations")

    fit_a4 = request.form.get("fit_a4") == "on"
    compress = request.form.get("compress") == "on"

    merger = PdfMerger()

    for i, f in enumerate(files):
        if not f or not f.filename:
            continue

        ext = f.filename.lower()

        rotate = 0
        if i < len(rotations):
            try:
                rotate = int(rotations[i])
            except:
                rotate = 0

        # ---------------- IMAGE ----------------
        if ext.endswith((".jpg", ".jpeg", ".png", ".webp")):
            img = process_image(f, rotate)

            if fit_a4:
                img = fit_to_a4(img)

            buf = io.BytesIO()

            # 🔥 COMPRESSION LOGIC
            if compress:
                img.save(buf, format="JPEG", quality=60, optimize=True)
            else:
                img.save(buf, format="JPEG", quality=95)

            buf.seek(0)

            # convert image -> PDF page
            temp_img = Image.open(buf)
            pdf_buf = io.BytesIO()
            temp_img.convert("RGB").save(pdf_buf, format="PDF", quality=95)
            pdf_buf.seek(0)

            merger.append(pdf_buf)

        # ---------------- PDF ----------------
        elif ext.endswith(".pdf"):
            pdf = PdfReader(f.stream)
            merger.append(pdf)

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(output, download_name=filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False, port=5613)