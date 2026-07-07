from flask import Flask, request, send_file, render_template
from PIL import Image, ImageOps
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from werkzeug.utils import secure_filename

import io
import os
import zipfile
import tempfile
import subprocess

from datetime import datetime

app = Flask(__name__)

A4_WIDTH = 2480
A4_HEIGHT = 3508

files_converted_count = 0
app_start_time = datetime.now()


# =========================================================
# IMAGE PROCESSING
# =========================================================
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


def image_to_pdf_buffer(file, rotate, fit_a4, compress, compress_quality):
    img = process_image(file, rotate)

    if fit_a4:
        img = fit_to_a4(img)

    img_buf = io.BytesIO()

    if compress:
        img.save(
            img_buf,
            format="JPEG",
            quality=compress_quality,
            optimize=True
        )
    else:
        img.save(
            img_buf,
            format="JPEG",
            quality=95
        )

    img_buf.seek(0)

    temp_img = Image.open(img_buf)

    pdf_buf = io.BytesIO()

    temp_img.convert("RGB").save(
        pdf_buf,
        format="PDF"
    )

    pdf_buf.seek(0)

    return pdf_buf


# =========================================================
# PDF PROCESSING
# =========================================================
def rotate_pdf(file_stream, rotate=0):
    reader = PdfReader(file_stream)
    writer = PdfWriter()

    for page in reader.pages:
        if rotate:
            try:
                page.rotate(rotate)
            except AttributeError:
                page.rotateClockwise(rotate)

        writer.add_page(page)

    pdf_buf = io.BytesIO()
    writer.write(pdf_buf)
    pdf_buf.seek(0)

    return pdf_buf


def get_ghostscript_settings(compress_quality):
    if compress_quality <= 40:
        pdf_settings = "/screen"
    elif compress_quality <= 75:
        pdf_settings = "/ebook"
    else:
        pdf_settings = "/printer"

    image_dpi = int(
        72 + (compress_quality - 10) * (300 - 72) / 85
    )

    return pdf_settings, image_dpi


def compress_pdf_buffer(pdf_buffer, compress_quality):
    pdf_buffer.seek(0)

    input_path = None
    output_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_input:
            temp_input.write(pdf_buffer.read())
            input_path = temp_input.name

        output_fd, output_path = tempfile.mkstemp(
            suffix="_compressed.pdf"
        )
        os.close(output_fd)

        if os.name == "nt":
            gs_command = "gswin64c"
        else:
            gs_command = "gs"

        pdf_settings, image_dpi = get_ghostscript_settings(
            compress_quality
        )

        subprocess.run([
            gs_command,

            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",

            f"-dPDFSETTINGS={pdf_settings}",

            "-dAutoFilterColorImages=false",
            "-dAutoFilterGrayImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dGrayImageFilter=/DCTEncode",

            f"-dJPEGQ={compress_quality}",

            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",

            f"-dColorImageResolution={image_dpi}",
            f"-dGrayImageResolution={image_dpi}",

            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",

            f"-sOutputFile={output_path}",
            input_path

        ], check=True)

        with open(output_path, "rb") as f:
            compressed_data = f.read()

        output = io.BytesIO(compressed_data)
        output.seek(0)

        return output

    except Exception as e:
        print("Ghostscript compression error:", e)

        pdf_buffer.seek(0)
        return pdf_buffer

    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)

        if output_path and os.path.exists(output_path):
            os.remove(output_path)


# =========================================================
# FILE HELPERS
# =========================================================
def get_rotation(rotations, index):
    rotate = 0

    if index < len(rotations):
        try:
            rotate = int(rotations[index])
        except ValueError:
            rotate = 0

    return rotate % 360


def convert_single_file_to_pdf(
    file,
    rotate,
    fit_a4,
    compress,
    compress_quality
):
    filename = file.filename.lower()

    if filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return image_to_pdf_buffer(
            file=file,
            rotate=rotate,
            fit_a4=fit_a4,
            compress=compress,
            compress_quality=compress_quality
        )

    if filename.endswith(".pdf"):
        return rotate_pdf(file.stream, rotate)

    return None


def make_safe_pdf_name(original_filename, index):
    safe_name = secure_filename(original_filename)

    if not safe_name:
        safe_name = f"file_{index + 1}"

    base_name = os.path.splitext(safe_name)[0]

    if not base_name:
        base_name = f"file_{index + 1}"

    return f"{base_name}.pdf"


def make_unique_name(filename, used_names):
    if filename not in used_names:
        used_names.add(filename)
        return filename

    base, ext = os.path.splitext(filename)
    counter = 2

    while True:
        new_name = f"{base}_{counter}{ext}"

        if new_name not in used_names:
            used_names.add(new_name)
            return new_name

        counter += 1


# =========================================================
# ROUTES
# =========================================================
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
    single_result = request.form.get("single_result") == "on"

    try:
        compress_quality = int(
            request.form.get("compress_quality", 35)
        )
    except ValueError:
        compress_quality = 35

    compress_quality = max(10, min(95, compress_quality))

    processed_count = 0

    # =========================================================
    # OPTION 1: ONE MERGED PDF RESULT
    # =========================================================
    if single_result:
        merger = PdfMerger()

        for i, f in enumerate(files):
            if not f or not f.filename:
                continue

            rotate = get_rotation(rotations, i)

            pdf_buf = convert_single_file_to_pdf(
                file=f,
                rotate=rotate,
                fit_a4=fit_a4,
                compress=compress,
                compress_quality=compress_quality
            )

            if pdf_buf is None:
                continue

            merger.append(pdf_buf)
            processed_count += 1

        if processed_count == 0:
            merger.close()
            return "No valid files uploaded", 400

        output = io.BytesIO()

        merger.write(output)
        merger.close()

        output.seek(0)

        if compress:
            output = compress_pdf_buffer(
                output,
                compress_quality
            )

        filename = (
            f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        mimetype = "application/pdf"

    # =========================================================
    # OPTION 2: SEPARATE PDF FOR EACH FILE INSIDE ZIP
    # =========================================================
    else:
        output = io.BytesIO()
        used_names = set()

        with zipfile.ZipFile(
            output,
            "w",
            compression=zipfile.ZIP_DEFLATED
        ) as zip_file:

            for i, f in enumerate(files):
                if not f or not f.filename:
                    continue

                rotate = get_rotation(rotations, i)

                pdf_buf = convert_single_file_to_pdf(
                    file=f,
                    rotate=rotate,
                    fit_a4=fit_a4,
                    compress=compress,
                    compress_quality=compress_quality
                )

                if pdf_buf is None:
                    continue

                if compress:
                    pdf_buf = compress_pdf_buffer(
                        pdf_buf,
                        compress_quality
                    )

                pdf_name = make_safe_pdf_name(
                    f.filename,
                    i
                )

                pdf_name = make_unique_name(
                    pdf_name,
                    used_names
                )

                pdf_buf.seek(0)

                zip_file.writestr(
                    pdf_name,
                    pdf_buf.read()
                )

                processed_count += 1

        if processed_count == 0:
            return "No valid files uploaded", 400

        output.seek(0)

        filename = (
            f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )

        mimetype = "application/zip"

    # =========================================================
    # UPDATE COUNTERS
    # =========================================================
    files_converted_count += processed_count

    # =========================================================
    # SEND FILE
    # =========================================================
    response = send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype=mimetype
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
        "X-App-Start-Time, "
        "Content-Disposition"
    )

    return response


if __name__ == "__main__":
    app.run(debug=False, port=5613)