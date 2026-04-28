from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("images")
    images = []

    for file in files:
        if file and allowed_file(file.filename):
            try:
                img = Image.open(file.stream)

                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                images.append(img)
            except:
                continue

    if not images:
        return jsonify({"error": "No valid images"}), 400

    pdf_bytes = io.BytesIO()

    images[0].save(
        pdf_bytes,
        format="PDF",
        save_all=True,
        append_images=images[1:]
    )

    pdf_bytes.seek(0)

    return send_file(
        pdf_bytes,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="images.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5613)