# USKO PDF Converter — UI Refresh

A visual and usability refresh for version 3.1.0.

## Installation

In the existing GitHub repo, **replace**:

- `templates/index.html`
- `static/style.css`

Keep `main.py`, `requirements.txt`, `Dockerfile`, and your existing images/favicon unchanged. Restart the Flask service / redeploy the container.

## What's changed

- Responsive two-column desktop workspace; stacks on mobile.
- Content-height layout so controls never overlap the Convert button/footer.
- Clear upload zone, preview cards with filenames and sizes, PDF previews, rotation, deletion, manual sort, and Clear all.
- Distinct output-settings section, quality control shown only when compression is enabled.
- Stronger accessibility, live conversion messages, errors, and success feedback.
- Preserves `/convert` endpoint and form names `files`, `rotations`, `fit_a4`, `compress`, `compress_quality`, `single_result`.
- The HTML still depends on SortableJS and pdf.js CDN scripts for drag reordering/PDF previews.

## Important

The `ui-preview.html` file is a local visual preview; conversion only works with the Flask backend running. No source code has been changed on GitHub by this package.
