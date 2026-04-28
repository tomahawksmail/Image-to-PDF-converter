# 📄 Image to PDF Converter

A simple and modern Flask web app that lets you upload one or multiple images and instantly download them as a single PDF — one image per page.

---

## ✨ Features

- 📤 Drag & drop or click to upload images  
- ⚡ Instant conversion (no submit button)  
- 📊 Circular progress indicator during upload  
- 🖼 Supports multiple formats:
  - PNG
  - JPG / JPEG
  - GIF  
- 📑 Automatically generates multi-page PDF  
- ⬇️ Auto-download after conversion  
- 🎨 Clean, responsive UI  

---

## 🧱 Tech Stack

- **Backend:** Flask (Python)
- **Image Processing:** Pillow (PIL)
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Transport:** AJAX (XMLHttpRequest)

---

## 📁 Project Structure
project/
│
├── app.py
├── templates/
│ └── index.html
├── static/
│ └── style.css
└── README.md


---

## 🚀 How It Works

1. User selects or drags images into the upload box  
2. Files are automatically sent to the backend via AJAX  
3. Flask processes images using Pillow  
4. Images are converted to RGB and combined into a PDF  
5. PDF is returned as a binary response  
6. Browser triggers automatic download  

---

## ⚠️ Notes

- Maximum upload size is limited (default: 20MB)
- GIFs are processed as single-frame images
- Invalid or corrupted files are skipped silently
- PDF is generated in memory (no temporary files)

---

## 🔧 Configuration

You can change upload size in `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

📜 License

MIT License — feel free to use and modify.