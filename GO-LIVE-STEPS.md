# FileFit: go live on GitHub and pip

You do three parts, in order. Part 1 has two options: pick **A** or **B**, not both.

---

## Part 1, option A: let Claude push the code (easiest)

Claude still can't reach your GitHub account (checked 23 Oct 2026). To fix it:

1. Sign in to <https://claude.ai> with the same account you use for this project.
2. Open <https://claude.ai/connect-github> and click through until it says **Connected**.
   If you see "Configure" or a list of repositories, make sure **filefit** is ticked.
3. Check <https://github.com/settings/installations>. **Claude** should be listed there with access to `filefit`.
4. Reply "done" in the project thread. Claude pushes the code and does Part 3 for you.

If the link page keeps failing, use option B instead.

## Part 1, option B: upload the code yourself (about 5 minutes)

1. Download **filefit-project.zip** from the project thread and unzip it. You get a folder called `filefit`.
2. Open <https://github.com/dipanjanbanerjee/filefit>.
3. Click **uploading an existing file**. If the repository already has files, use **Add file → Upload files**.
4. Open the unzipped `filefit` folder, select **everything inside it** (Ctrl + A), and drag it onto the GitHub page.
   Make sure the `.github` folder is included. It holds the automatic build instructions.
5. At the bottom, type a message such as `First version` and click **Commit changes**.

Check: on the repository page you should see the folders `.github`, `filefit`, `installer`, `site` and `tests`, plus files like `README.md` and `pyproject.toml`.

---

## Part 2: turn on the download website (one time, 1 minute)

1. On your repository, open **Settings → Pages**.
2. Under **Source**, choose **GitHub Actions**.
3. Open the **Actions** tab, click **Website** on the left, then **Run workflow → Run workflow**.
4. After 1–2 minutes your site is live at <https://dipanjanbanerjee.github.io/filefit/>.

The download buttons start working after Part 3.

---

## Part 3: publish version 1.0.0 (Windows installer, Linux download, and pip)

1. On your repository page, click **Releases** on the right side, then **Draft a new release** (or **Create a new release**).
2. Click **Choose a tag**, type `v1.0.0`, and click **Create new tag: v1.0.0 on publish**.
3. Release title: `FileFit 1.0.0`.
4. Click **Publish release**.
5. Open the **Actions** tab. You'll see **Build and release** running. It takes about 15–25 minutes.
   - Green tick: done. The release page now has `FileFit-Setup.exe`, `FileFit-Portable.exe` and the Linux file, and FileFit is on pip.
   - Red cross: click it, copy the error text, and send it to Claude in the thread.
6. Check pip: <https://pypi.org/project/filefit/> should show version 1.0.0. Anyone can now run:
   ```
   pipx install filefit
   ```

Your PyPI "pending publisher" (already set up) is what lets GitHub upload to pip without a password. The first successful release turns it into the real `filefit` project on PyPI.

---

## Later: releasing an update

1. Ask Claude for the change, or edit the code yourself.
2. Change the version number in `filefit/__init__.py`, for example `1.0.1`.
3. Draft a new release with the tag `v1.0.1`, as in Part 3. The version number and the tag must match.

Everything else (installer, website buttons, pip) updates automatically.
