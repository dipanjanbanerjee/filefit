# FileFit — File Converter & Compressor

Convert documents between the formats upload portals ask for, and shrink them under a size limit (for example 2 MB or 200 KB), all offline on your own PC.

| From | To |
| --- | --- |
| JPG, JPEG, PNG, WEBP, BMP, GIF, TIFF, HEIC (iPhone photos) | JPG, JPEG, PNG, WEBP, PDF, DOCX |
| PDF | JPG / JPEG / PNG / WEBP (one picture per page), DOCX (editable), PDF (compressed) |
| DOCX | PDF, pictures, DOCX (compressed) |

Extra options: size limit with one-click presets (100 KB to 5 MB), maximum width and height in pixels, combine many files into one PDF (drag to reorder), and save next to the original or into a chosen folder. Originals are never changed.

## Install

- **Windows:** download `FileFit-Setup.exe` from the Releases page or the website and run it.
- **Android:** download `FileFit-Android.apk` from the Releases page or the website, tap it and choose Install (Google Play later).
- **Linux:** `pipx install filefit`, then `filefit-cli --install-shortcut` to add it to your app menu.
- **Command line (any OS):** `filefit-cli photo.jpg --to pdf --max-size 2MB`

**DOCX → PDF / JPG** needs Microsoft Word *or* the free [LibreOffice](https://www.libreoffice.org/download/) installed. Every other conversion works with nothing else installed.

Releases are built automatically by GitHub Actions; see [PUBLISHING.md](PUBLISHING.md). To build the single-file exe yourself on Windows, double-click `build_windows.bat`.

## How size limits work
- **JPG / WEBP**: finds the highest quality that fits, and only shrinks the pixel size if quality alone is not enough.
- **PNG**: reduces colours, then pixel size. For photos, JPG reaches small sizes with far better quality.
- **PDF**: first recompresses the pictures inside the PDF (text stays selectable). If that is still too big, pages are turned into compressed images; the result says so.
- **DOCX**: recompresses the pictures inside the document.

If a file cannot reach the limit, the result shows ⚠ with its final size.

## Contact
Made by **Dipanjan Banerjee**. Questions, bugs or ideas: dipanjanbanerjee20@gmail.com or [open an issue](https://github.com/dipanjanbanerjee/filefit/issues).

## Project layout
```
main.py                     starts the app
filefit/core/               conversion + compression engine (no GUI code)
filefit/gui/                PySide6 (Qt) desktop window and styling
tests/                      pytest suite for the engine
filefit/cli.py              command line tool (filefit-cli)
FileFit.spec                PyInstaller recipe for the .exe
installer/FileFit.iss       Windows installer (Inno Setup)
site/                       download website (GitHub Pages)
.github/workflows/          automatic builds, releases, website
build_windows.bat           local one-click Windows build
```

Run the tests: `pip install -r requirements-dev.txt` then `pytest -q tests`.

## Android app
`mobile/` holds the phone app: a Flet (Python + Flutter) screen on top of the same `filefit/core` engine, with a welcome tour, format and size-limit chips, and Share / Save buttons for the results. GitHub Actions builds `FileFit-Android.apk` with `flet build apk`.

Try it on a computer: `pip install "flet[all]==1.0.5"`, then `python mobile/main.py`. Turning DOCX into PDF or pictures is not available on the phone (it needs Word or LibreOffice).

Fonts: Outfit and DM Sans, SIL Open Font License (see `mobile/assets/fonts/`).
