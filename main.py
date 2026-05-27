from flask import Flask, request, send_file, render_template
from PIL import Image, ImageOps
from PyPDF2 import PdfMerger, PdfReader
import io
from datetime import datetime

import subprocess
import tempfile
import os

app = Flask(__name__)

A4_WIDTH = 2480
A4_HEIGHT = 3508

files_converted_count = 0
app_start_time = datetime.now()

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
    global files_converted_count

    files = request.files.getlist("files")
    rotations = request.form.getlist("rotations")

    fit_a4 = request.form.get("fit_a4") == "on"
    compress = request.form.get("compress") == "on"

    merger = PdfMerger()
    processed_count = 0

    for i, f in enumerate(files):

        if not f or not f.filename:
            continue

        ext = f.filename.lower()

        # ---------------- ROTATION ----------------
        rotate = 0
        if i < len(rotations):
            try:
                rotate = int(rotations[i])
            except:
                rotate = 0

        # =========================================================
        # IMAGE FILES
        # =========================================================
        if ext.endswith((".jpg", ".jpeg", ".png", ".webp")):

            img = process_image(f, rotate)

            if fit_a4:
                img = fit_to_a4(img)

            img_buf = io.BytesIO()

            # 🔥 IMAGE COMPRESSION
            if compress:
                img.save(
                    img_buf,
                    format="JPEG",
                    quality=35,
                    optimize=True
                )
            else:
                img.save(
                    img_buf,
                    format="JPEG",
                    quality=95
                )

            img_buf.seek(0)

            # image -> pdf
            temp_img = Image.open(img_buf)

            pdf_buf = io.BytesIO()

            temp_img.convert("RGB").save(
                pdf_buf,
                format="PDF"
            )

            pdf_buf.seek(0)

            merger.append(pdf_buf)

            processed_count += 1

        # =========================================================
        # PDF FILES
        # =========================================================
        elif ext.endswith(".pdf"):

            merger.append(PdfReader(f.stream))

            processed_count += 1

    # =========================================================
    # CREATE FINAL PDF
    # =========================================================
    output = io.BytesIO()

    merger.write(output)
    merger.close()

    output.seek(0)

    # =========================================================
    # 🔥 REAL PDF COMPRESSION USING GHOSTSCRIPT
    # =========================================================
    if compress:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_input:

            temp_input.write(output.read())

            input_path = temp_input.name

        output_path = input_path.replace(
            ".pdf",
            "_compressed.pdf"
        )

        try:

            # WINDOWS:
            # gs_command = "gswin64c"

            # LINUX / MAC:
            gs_command = "gs"

            subprocess.run([
                gs_command,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",

                # Compression level:
                # /screen  = strongest compression
                # /ebook   = balanced
                # /printer = better quality
                "-dPDFSETTINGS=/screen",

                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",

                f"-sOutputFile={output_path}",
                input_path

            ], check=True)

            # load compressed pdf
            with open(output_path, "rb") as f:
                compressed_data = f.read()

            output = io.BytesIO(compressed_data)

        except Exception as e:
            print("Ghostscript compression error:", e)

        finally:

            if os.path.exists(input_path):
                os.remove(input_path)

            if os.path.exists(output_path):
                os.remove(output_path)

    output.seek(0)

    # =========================================================
    # UPDATE COUNTERS
    # =========================================================
    files_converted_count += processed_count

    filename = (
        f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    # =========================================================
    # SEND FILE
    # =========================================================
    response = send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype="application/pdf"
    )

    # =========================================================
    # HEADERS
    # =========================================================
    response.headers["X-Files-Processed"] = str(
        processed_count
    )

    response.headers["X-Total-Files"] = str(
        files_converted_count
    )

    response.headers["X-App-Start-Time"] = (
        app_start_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    response.headers["Access-Control-Expose-Headers"] = (
        "X-Files-Processed, "
        "X-Total-Files, "
        "X-App-Start-Time"
    )

    return response

if __name__ == "__main__":
    app.run(debug=False, port=5613)