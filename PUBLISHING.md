# Publishing FileFit

Everything is automated. You set up three free accounts once, and from then on publishing a new version is one command. Nobody, including you, has to run the long build again: GitHub's computers do it.

```
you push a version tag (v1.0.0)
        │
        ▼
GitHub Actions (.github/workflows/release.yml)
  ├─ runs the tests
  ├─ Windows machine → FileFit-Setup.exe (installer) + FileFit-Portable.exe
  ├─ Linux machine   → FileFit-linux-x86_64.tar.gz + pip package
  ├─ GitHub Release  ← all files above (what the website links to)
  └─ PyPI            ← pip package (so `pipx install filefit` works)

site/ folder → GitHub Pages (.github/workflows/website.yml) = your download website
```

## One-time setup

### 1. GitHub (free): code, builds, downloads and website
1. Create an account at <https://github.com> if you don't have one.
2. Create a new **public** repository named `filefit` (public repos get free unlimited build minutes).
3. Upload this whole `file-converter` folder's contents to it (or ask Claude to push it for you).
4. Turn on the website: repository **Settings → Pages → Source: GitHub Actions**. Your site appears at `https://dipanjanbanerjee.github.io/filefit/`.

### 2. PyPI (free): `pip install filefit`
1. Create an account at <https://pypi.org> and turn on two-factor login.
2. Go to **Your account → Publishing → Add a new pending publisher** and fill in:
   - PyPI project name: `filefit`
   - Owner: your GitHub username · Repository: `filefit`
   - Workflow name: `release.yml` · Environment: `pypi`
3. No password or token is stored anywhere; GitHub proves who it is to PyPI automatically.

The name `filefit` was free on PyPI on 18 Oct 2026. Claim it soon with your first release.

### 3. Google Play (one-time US$25 fee): Android
See "Android" below. Start this early because Google makes new developers wait.

## Releasing a new version
1. Change the version in `filefit/__init__.py` (for example `1.0.1`).
2. Commit, then create and push a tag with the same number:
   ```
   git tag v1.0.1
   git push origin v1.0.1
   ```
3. About 15 minutes later the GitHub Release has the installer, portable exe and Linux files, PyPI has the new version, and the download buttons on your website point to it automatically.

To test a build without publishing, open **Actions → Build and release → Run workflow**. The files appear at the bottom of that run's page.

## What your users do
- **Windows:** download `FileFit-Setup.exe`, double-click, Next, Next, Finish. They get a Start menu entry, an optional desktop icon, an uninstaller, and "Open with FileFit" on pictures, PDFs and DOCX files.
- **Linux:** `pipx install filefit`, then `filefit-cli --install-shortcut` to add it to the app menu. Plain `pip install filefit` works inside a virtual environment; most current Linux systems block pip installs into the system Python, which is why pipx is recommended.
- **Android:** install from Google Play once the app is approved.

## Android and Google Play
The conversion engine (`filefit/core`) can run on Android unchanged. Flet, the tool planned for the phone version, ships Android builds of every library it uses (PyMuPDF, Pillow, lxml, NumPy, OpenCV). What is still needed is a phone-sized screen, built with Flet, plus an Android build job added to the release workflow.

Google Play steps for you:
1. Register at <https://play.google.com/console> (one-time US$25, identity verification).
2. New personal accounts must run a **closed test with at least 12 testers who stay opted in for 14 days in a row** before the app can go public. Line up 12 friends with Android phones early.
3. The store listing needs: app icon (512×512), feature graphic (1024×500), at least 2 phone screenshots, short and full description, a privacy policy URL (`https://dipanjanbanerjee.github.io/filefit/privacy.html` is already written), and the Data safety form (answer: no data collected).
4. Upload the `.aab` file that the build produces, first to the closed test track, then to production after the 14 days.

## Optional, later
- **Code signing certificate** for Windows (about US$100–300 per year) removes the "Windows protected your PC" warning. Free alternative: the warning fades as more people download the same file.
- **Smaller download:** most of the installer size comes from the PDF→Word converter's image library. Replacing it with a lighter converter would roughly halve the download.
