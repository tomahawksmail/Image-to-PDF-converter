from flask import Flask, request, send_file, render_template
from PIL import Image, ImageOps
import io

app = Flask(__name__)

# ----------------------------
# Image normalization
# ----------------------------
def process_image(file):
    img = Image.open(file.stream)

    # EXIF rotation fix
    img = ImageOps.exif_transpose(img)

    # remove alpha/palette issues
    img = img.convert("RGB")

    return img


# ----------------------------
# Fit to A4
# ----------------------------
A4_WIDTH = 2480
A4_HEIGHT = 3508

def fit_to_a4(img):
    page = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

    img.thumbnail((A4_WIDTH, A4_HEIGHT), Image.LANCZOS)

    x = (A4_WIDTH - img.width) // 2
    y = (A4_HEIGHT - img.height) // 2

    page.paste(img, (x, y))
    return page


# ----------------------------
# Route
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("images")

    compress = request.form.get("compress") == "on"
    fit_a4 = request.form.get("fit_a4") == "on"
    exif_fix = request.form.get("exif") == "on"

    images = []

    for f in files:
        img = Image.open(f.stream)

        if exif_fix:
            img = ImageOps.exif_transpose(img)

        img = img.convert("RGB")

        if fit_a4:
            img = fit_to_a4(img)

        images.append(img)

    output = io.BytesIO()

    save_kwargs = {
        "format": "PDF",
        "save_all": True,
        "append_images": images[1:],
    }

    # compression toggle
    if compress:
        save_kwargs["quality"] = 75
        save_kwargs["optimize"] = True

    images[0].save(output, **save_kwargs)
    output.seek(0)

    return send_file(output, download_name="converted.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5613)