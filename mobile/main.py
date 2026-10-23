"""FileFit for Android: a phone-friendly front end for the FileFit engine.

Run on a computer for testing:   python mobile/main.py
Build the Android app:            see mobile/README.md
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import time
from pathlib import Path

import flet as ft

# The engine lives in ../filefit when running from the repository; the Android
# build copies it next to this file.
_here = Path(__file__).resolve().parent
if not (_here / "filefit").exists():
    sys.path.insert(0, str(_here.parent))

from filefit import __author__, __email__, __version__  # noqa: E402
from filefit.core import INPUT_EXTS, Options, combine_to_pdf, convert_file, human_size, kind_of  # noqa: E402

# ---------------------------------------------------------------- look & feel
INK = "#0D0B1E"          # night background
SURFACE = "#17152E"      # cards
SURFACE_2 = "#211E3F"    # raised / chips
LINE = "#2E2A55"
TEXT = "#F3F1FF"
MUTED = "#A39FC9"
VIOLET = "#7C5CFF"
TEAL = "#19D3B4"
PINK = "#FF5CA8"
OK = "#34D399"
WARN = "#FBBF24"
ERR = "#FB7185"

GRAD = ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[VIOLET, TEAL])
GRAD_PINK = ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[PINK, VIOLET])

DISPLAY = "Outfit"
BODY = "DMSans"

FORMATS = ["JPG", "JPEG", "PNG", "WEBP", "PDF", "DOCX"]
LIMITS = [("100 KB", 100 * 1024), ("200 KB", 200 * 1024), ("500 KB", 500 * 1024),
          ("1 MB", 1024 ** 2), ("2 MB", 2 * 1024 ** 2), ("5 MB", 5 * 1024 ** 2)]

WELCOME = [
    dict(icon=ft.Icons.UPLOAD_FILE_ROUNDED, grad=GRAD_PINK, kicker="FILE TOO BIG?",
         title="Portal said no?\nNot anymore.",
         body="FileFit makes any document fit the upload box, in one tap."),
    dict(icon=ft.Icons.SWAP_HORIZ_ROUNDED, grad=GRAD, kicker="WRONG FORMAT?",
         title="PDF, JPG, DOCX.\nYou name it.",
         body="Turn photos into PDFs, PDFs into pictures, and pages into Word files."),
    dict(icon=ft.Icons.COMPRESS_ROUNDED, grad=ft.LinearGradient(colors=[TEAL, VIOLET]), kicker="UNDER 2 MB?",
         title="Hit the limit.\nKeep the quality.",
         body="Pick 200 KB, 1 MB or any size. FileFit squeezes until it fits."),
    dict(icon=ft.Icons.LOCK_ROUNDED, grad=ft.LinearGradient(colors=[VIOLET, PINK]), kicker="PRIVATE BY DESIGN",
         title="100% offline.\n100% yours.",
         body="Your Aadhaar, marksheets and photos never leave your phone."),
]


def txt(value, size=14, weight=ft.FontWeight.NORMAL, color=TEXT, font=BODY, **kw):
    return ft.Text(value, size=size, weight=weight, color=color, font_family=font, **kw)


def badge_icon(icon, grad, size=56, icon_size=28):
    return ft.Container(
        width=size, height=size, border_radius=size * 0.32, gradient=grad,
        alignment=ft.Alignment(0, 0), content=ft.Icon(icon, color="white", size=icon_size),
        shadow=ft.BoxShadow(blur_radius=24, spread_radius=-6, color="#807C5CFF", offset=ft.Offset(0, 8)),
    )


def section(title):
    return txt(title.upper(), size=12, weight=ft.FontWeight.W_600, color=MUTED, style=ft.TextStyle(letter_spacing=1.4))


# ---------------------------------------------------------------- the app
class FileFitApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.files: list[Path] = []
        self.fmt = "PDF"
        self.limit: int | None = 2 * 1024 ** 2
        self.combine = False
        self.busy = False
        self.outputs = []

        self.picker = ft.FilePicker()
        self.share = ft.Share()
        self.prefs = ft.SharedPreferences()
        self.paths = ft.StoragePaths()
        self.haptics = ft.HapticFeedback()
        self.urls = ft.UrlLauncher()

        self.root = ft.AnimatedSwitcher(
            content=ft.Container(), duration=450, reverse_duration=250,
            transition=ft.AnimatedSwitcherTransition.FADE, expand=True,
        )
        page.add(ft.Container(content=self.root, expand=True, bgcolor=INK))

    async def start(self):
        seen = False
        try:
            seen = bool(await self.prefs.get("welcome_seen"))
        except Exception:
            pass
        self.show_home() if seen else self.show_welcome()

    async def buzz(self):
        try:
            await self.haptics.light_impact()
        except Exception:
            pass

    # ---------------------------------------------------------- welcome
    def show_welcome(self):
        dots = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        def paint_dots(i):
            dots.controls = [
                ft.Container(width=26 if j == i else 8, height=8, border_radius=4,
                             bgcolor=TEXT if j == i else LINE, animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT))
                for j in range(len(WELCOME))
            ]

        def slide(s):
            return ft.Container(
                padding=ft.Padding.symmetric(horizontal=28),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START, spacing=18,
                    controls=[
                        ft.Container(
                            height=230, alignment=ft.Alignment(0, 0),
                            content=ft.Stack(alignment=ft.Alignment(0, 0), controls=[
                                ft.Container(width=210, height=210, border_radius=105, gradient=s["grad"], opacity=0.18),
                                ft.Container(width=150, height=150, border_radius=75, gradient=s["grad"], opacity=0.28),
                                badge_icon(s["icon"], s["grad"], size=96, icon_size=48),
                            ]),
                        ),
                        txt(s["kicker"], size=12, weight=ft.FontWeight.W_700, color=TEAL,
                            style=ft.TextStyle(letter_spacing=2)),
                        txt(s["title"], size=34, weight=ft.FontWeight.W_700, font=DISPLAY,
                            style=ft.TextStyle(height=1.1)),
                        txt(s["body"], size=16, color=MUTED, style=ft.TextStyle(height=1.45)),
                    ],
                ),
            )

        pages = ft.PageView(controls=[slide(s) for s in WELCOME], expand=True)
        cta_label = txt("Next", size=16, weight=ft.FontWeight.W_700, font=DISPLAY, color="white")

        def on_change(e):
            i = int(e.data) if e.data is not None else pages.selected_index
            paint_dots(i)
            cta_label.value = "Let's make it fit" if i == len(WELCOME) - 1 else "Next"
            self.page.update()

        pages.on_change = on_change
        paint_dots(0)

        async def next_or_start(e):
            await self.buzz()
            i = pages.selected_index or 0
            if i < len(WELCOME) - 1:
                await pages.next_page(animation_duration=350, animation_curve=ft.AnimationCurve.EASE_OUT_CUBIC)
            else:
                await self.finish_welcome()

        async def skip(e):
            await self.finish_welcome()

        self.root.content = ft.SafeArea(expand=True, content=ft.Column(expand=True, spacing=0, controls=[
            ft.Container(padding=ft.Padding.only(left=24, right=12, top=8), content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=10, controls=[
                        badge_icon(ft.Icons.BOLT_ROUNDED, GRAD, size=34, icon_size=20),
                        txt("FileFit", size=20, weight=ft.FontWeight.W_700, font=DISPLAY),
                    ]),
                    ft.TextButton(content=txt("Skip", color=MUTED, weight=ft.FontWeight.W_600), on_click=skip),
                ],
            )),
            pages,
            ft.Container(padding=ft.Padding.only(left=24, right=24, bottom=24, top=8), content=ft.Column(
                spacing=22, controls=[
                    dots,
                    ft.Container(
                        height=58, border_radius=18, gradient=GRAD, alignment=ft.Alignment(0, 0), ink=True,
                        on_click=next_or_start, content=cta_label,
                        shadow=ft.BoxShadow(blur_radius=30, spread_radius=-8, color="#997C5CFF", offset=ft.Offset(0, 12)),
                    ),
                ],
            )),
        ]))
        self.page.update()

    async def finish_welcome(self):
        try:
            await self.prefs.set("welcome_seen", True)
        except Exception:
            pass
        self.show_home()

    # ---------------------------------------------------------- home
    def show_home(self):
        self.file_col = ft.Column(spacing=10)
        self.format_row = ft.Column(spacing=10)
        self.limit_row = ft.Column(spacing=10)
        self.combine_row = ft.Container()
        self.hint = txt("", size=13, color=WARN, visible=False)
        self.progress = ft.ProgressBar(value=0, color=TEAL, bgcolor=SURFACE_2, border_radius=6, height=6, visible=False)
        self.status = txt("", size=13, color=MUTED)
        self.go_label = txt("Make it fit", size=17, weight=ft.FontWeight.W_700, font=DISPLAY, color="white")
        self.go_btn = ft.Container(
            height=60, border_radius=20, gradient=GRAD, alignment=ft.Alignment(0, 0), ink=True,
            on_click=self.run, content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color="white", size=22), self.go_label]),
            shadow=ft.BoxShadow(blur_radius=30, spread_radius=-8, color="#997C5CFF", offset=ft.Offset(0, 12)),
            animate_opacity=200,
        )
        self.results_col = ft.Column(spacing=12, key=ft.ScrollKey("results"))

        header = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Row(spacing=12, controls=[
                badge_icon(ft.Icons.BOLT_ROUNDED, GRAD, size=44, icon_size=24),
                ft.Column(spacing=0, controls=[
                    txt("FileFit", size=24, weight=ft.FontWeight.W_700, font=DISPLAY),
                    txt("Make any file fit the upload box", size=13, color=MUTED),
                ]),
            ]),
            ft.Row(spacing=0, controls=[
                ft.IconButton(icon=ft.Icons.FAVORITE_ROUNDED, icon_color=PINK, tooltip="Support FileFit",
                              on_click=self.show_support),
                ft.IconButton(icon=ft.Icons.INFO_OUTLINE_ROUNDED, icon_color=MUTED, on_click=self.show_about),
            ]),
        ])

        picker_card = ft.Container(
            border_radius=24, padding=2, gradient=GRAD, ink=True, on_click=self.pick,
            content=ft.Container(
                border_radius=22, bgcolor=SURFACE, padding=ft.Padding.symmetric(vertical=26, horizontal=20),
                content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, controls=[
                    badge_icon(ft.Icons.ADD_ROUNDED, GRAD, size=56, icon_size=32),
                    txt("Choose files", size=18, weight=ft.FontWeight.W_700, font=DISPLAY),
                    txt("Photos, scans, PDF or Word", size=13, color=MUTED),
                ]),
            ),
        )

        self.body = body = ft.ListView(expand=True, padding=ft.Padding.only(left=20, right=20, top=8, bottom=28), spacing=22, controls=[
            header,
            picker_card,
            self.file_col,
            ft.Column(spacing=12, controls=[section("Convert to"), self.format_row]),
            ft.Column(spacing=12, controls=[section("Keep each file under"), self.limit_row]),
            self.combine_row,
            self.hint,
            ft.Column(spacing=10, controls=[self.go_btn, self.progress, self.status]),
            self.results_col,
        ])
        self.root.content = ft.SafeArea(expand=True, content=body)
        self.refresh()

    def chip(self, label, selected, on_click, width=None, compact=False):
        return ft.Container(
            width=width, height=44, border_radius=14, alignment=ft.Alignment(0, 0), ink=True, on_click=on_click,
            gradient=GRAD if selected else None, bgcolor=None if selected else SURFACE_2,
            border=None if selected else ft.Border.all(1, LINE),
            padding=ft.Padding.symmetric(horizontal=4 if compact else 14),
            content=txt(label, size=13 if compact else 14, max_lines=1, weight=ft.FontWeight.W_700 if selected else ft.FontWeight.W_500,
                        color="white" if selected else TEXT, font=DISPLAY),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def refresh(self):
        # files
        self.file_col.controls = []
        for p in self.files:
            kind = kind_of(p)
            icon = {"image": ft.Icons.IMAGE_ROUNDED, "pdf": ft.Icons.PICTURE_AS_PDF_ROUNDED,
                    "docx": ft.Icons.DESCRIPTION_ROUNDED}[kind]
            self.file_col.controls.append(ft.Container(
                bgcolor=SURFACE, border_radius=16, padding=ft.Padding.only(left=14, right=4, top=10, bottom=10),
                content=ft.Row(spacing=12, controls=[
                    ft.Container(width=40, height=40, border_radius=12, bgcolor=SURFACE_2, alignment=ft.Alignment(0, 0),
                                 content=ft.Icon(icon, color=TEAL, size=22)),
                    ft.Column(spacing=1, expand=True, controls=[
                        txt(p.name, size=14, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        txt(f"{human_size(p.stat().st_size)}  ·  {p.suffix.upper().lstrip('.')}", size=12, color=MUTED),
                    ]),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_color=MUTED, icon_size=20,
                                  on_click=lambda e, p=p: self.remove(p)),
                ]),
            ))

        # formats: an even 3 x 2 grid
        chips = [ft.Container(expand=1, content=self.chip(f, f == self.fmt, lambda e, f=f: self.set_fmt(f)))
                 for f in FORMATS]
        self.format_row.controls = [ft.Row(spacing=10, controls=chips[i:i + 3]) for i in range(0, len(chips), 3)]

        # limits: 2 rows of 4, the last one opens a custom size box
        custom = self.limit is not None and self.limit not in [v for _, v in LIMITS]
        items = [("No limit", self.limit is None, lambda e: self.set_limit(None))]
        items += [(lbl, self.limit == val, lambda e, v=val: self.set_limit(v)) for lbl, val in LIMITS]
        items += [(human_size(self.limit) if custom else "Custom", custom, self.ask_custom)]
        chips = [ft.Container(expand=1, content=self.chip(lbl, sel, fn, compact=True)) for lbl, sel, fn in items]
        self.limit_row.controls = [ft.Row(spacing=8, controls=chips[i:i + 4]) for i in range(0, len(chips), 4)]

        # combine switch
        if self.fmt == "PDF" and len(self.files) > 1:
            self.combine_row.content = ft.Container(
                bgcolor=SURFACE, border_radius=16, padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Column(spacing=0, expand=True, controls=[
                        txt("Combine into one PDF", size=15, weight=ft.FontWeight.W_600),
                        txt("In the order shown above", size=12, color=MUTED),
                    ]),
                    ft.Switch(value=self.combine, active_color=TEAL, on_change=self.toggle_combine),
                ]),
            )
        else:
            self.combine_row.content = None

        # warning for Word files on phones
        has_docx = any(kind_of(p) == "docx" for p in self.files)
        self.hint.visible = has_docx and self.fmt != "DOCX"
        self.hint.value = ("Word files can be compressed here, but turning them into PDF or pictures "
                           "needs a computer. Choose DOCX, or use FileFit on Windows.")

        ready = bool(self.files) and not self.busy
        self.go_btn.opacity = 1 if ready else 0.45
        self.go_btn.disabled = not ready
        if not self.files and not self.outputs:
            self.status.value = "Pick a file to begin."
        self.page.update()

    def set_fmt(self, f):
        self.fmt = f
        self.refresh()

    def set_limit(self, v):
        self.limit = v
        self.refresh()

    def ask_custom(self, e):
        field = ft.TextField(value="", hint_text="e.g. 300", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True,
                             border_radius=14, filled=True, fill_color=SURFACE_2, border_color=LINE,
                             focused_border_color=TEAL, color=TEXT, expand=True)
        unit = {"v": "KB"}
        unit_row = ft.Row(spacing=8)

        def paint():
            unit_row.controls = [self.chip(u, unit["v"] == u, lambda e, u=u: pick_unit(u), width=64) for u in ("KB", "MB")]

        def pick_unit(u):
            unit["v"] = u
            paint()
            self.page.update()

        def apply(e):
            try:
                n = float((field.value or "").replace(",", "."))
                assert n > 0
            except Exception:
                field.error = "Type a number, like 300"
                self.page.update()
                return
            self.page.pop_dialog()
            self.set_limit(int(n * (1024 if unit["v"] == "KB" else 1024 ** 2)))

        paint()
        self.page.show_dialog(ft.AlertDialog(
            bgcolor=SURFACE, title=txt("Custom size limit", size=20, weight=ft.FontWeight.W_700, font=DISPLAY),
            content=ft.Column(tight=True, spacing=14, controls=[
                txt("What does the portal allow?", color=MUTED),
                ft.Row(spacing=10, controls=[field, unit_row]),
            ]),
            actions=[ft.TextButton(content=txt("Cancel", color=MUTED), on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton(content=txt("Set limit", color=TEAL, weight=ft.FontWeight.W_700), on_click=apply)],
        ))

    def toggle_combine(self, e):
        self.combine = bool(e.control.value)

    def remove(self, p):
        self.files = [f for f in self.files if f != p]
        self.refresh()

    async def pick(self, e):
        await self.buzz()
        try:
            picked = await self.picker.pick_files(
                dialog_title="Choose files", allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=sorted(x.lstrip(".") for x in INPUT_EXTS),
            )
        except Exception as exc:
            self.toast(f"Could not open the file picker: {exc}", ERR)
            return
        added = 0
        for f in picked or []:
            if not f.path:
                continue
            p = Path(f.path)
            try:
                kind_of(p)
            except ValueError:
                continue
            if p not in self.files:
                self.files.append(p)
                added += 1
        if added:
            self.outputs = []
            self.results_col.controls = []
            self.status.value = f"{len(self.files)} file{'s' if len(self.files) != 1 else ''} ready."
        self.refresh()

    # ---------------------------------------------------------- converting
    async def out_dir(self) -> Path:
        try:
            base = Path(await self.paths.get_application_documents_directory())
        except Exception:
            base = Path.home() / "Documents"
        d = base / "FileFit" / time.strftime("%Y-%m-%d_%H%M%S")
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def run(self, e):
        if self.busy or not self.files:
            return
        await self.buzz()
        self.busy = True
        self.go_label.value = "Working…"
        self.progress.visible = True
        self.progress.value = None
        self.results_col.controls = []
        self.refresh()

        folder = await self.out_dir()
        opts = Options(out_format=self.fmt, out_dir=folder, target_bytes=self.limit,
                       combine=self.combine and self.fmt == "PDF" and len(self.files) > 1)
        results = []
        if opts.combine:
            self.status.value = "Combining your files…"
            self.page.update()
            results.append(await asyncio.to_thread(combine_to_pdf, list(self.files), opts))
        else:
            for i, f in enumerate(self.files, 1):
                self.status.value = f"Fitting {f.name}  ({i}/{len(self.files)})"
                self.progress.value = (i - 1) / len(self.files)
                self.page.update()
                results.append(await asyncio.to_thread(convert_file, f, opts))

        self.outputs = [o for r in results for o in r.outputs]
        errors = [r for r in results if r.error]
        self.busy = False
        self.go_label.value = "Make it fit"
        self.progress.visible = False
        made = len(self.outputs)
        self.status.value = f"Done! {made} file{'s' if made != 1 else ''} ready to share or save." if made else ""
        self.show_results(errors)
        self.refresh()
        try:
            await self.body.scroll_to(scroll_key="results", duration=600)
        except Exception:
            pass
        try:
            await self.haptics.medium_impact()
        except Exception:
            pass

    def show_results(self, errors):
        cards = [section("Your files")] if self.outputs or errors else []
        for o in self.outputs:
            src_size = o.source.stat().st_size if o.source and o.source.exists() else None
            saved = ""
            if src_size and src_size > o.size:
                saved = f"  ·  {round(100 - o.size * 100 / src_size)}% smaller"
            ok = o.fits
            cards.append(ft.Container(
                bgcolor=SURFACE, border_radius=20, padding=16,
                border=ft.Border.all(1, LINE),
                content=ft.Column(spacing=12, controls=[
                    ft.Row(spacing=12, controls=[
                        ft.Container(width=40, height=40, border_radius=12, alignment=ft.Alignment(0, 0),
                                     bgcolor="#1A34D399" if ok else "#1AFBBF24",
                                     content=ft.Icon(ft.Icons.CHECK_ROUNDED if ok else ft.Icons.WARNING_AMBER_ROUNDED,
                                                     color=OK if ok else WARN, size=22)),
                        ft.Column(spacing=1, expand=True, controls=[
                            txt(o.path.name, size=14, weight=ft.FontWeight.W_600, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                            txt(f"{human_size(o.size)}{saved}" + ("" if ok else "  ·  still above the limit"),
                                size=12, color=OK if ok else WARN),
                        ]),
                    ]),
                    *( [txt(o.note, size=12, color=MUTED)] if o.note else [] ),
                    ft.Row(spacing=10, controls=[
                        self.action_btn("Share", ft.Icons.IOS_SHARE_ROUNDED, lambda e, o=o: self.share_file(o), True),
                        self.action_btn("Save", ft.Icons.DOWNLOAD_ROUNDED, lambda e, o=o: self.save_file(o), False),
                    ]),
                ]),
            ))
        for r in errors:
            cards.append(ft.Container(
                bgcolor=SURFACE, border_radius=20, padding=16, border=ft.Border.all(1, "#55FB7185"),
                content=ft.Row(spacing=12, controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ERR),
                    ft.Column(spacing=2, expand=True, controls=[
                        txt(r.source.name, size=14, weight=ft.FontWeight.W_600),
                        txt(friendly_error(r.error), size=12, color=MUTED),
                    ]),
                ]),
            ))
        self.results_col.controls = cards

    def action_btn(self, label, icon, handler, primary):
        return ft.Container(
            expand=1, height=46, border_radius=14, ink=True, on_click=handler, alignment=ft.Alignment(0, 0),
            gradient=GRAD if primary else None, bgcolor=None if primary else SURFACE_2,
            border=None if primary else ft.Border.all(1, LINE),
            content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=8, controls=[
                ft.Icon(icon, size=18, color="white" if primary else TEXT),
                txt(label, size=14, weight=ft.FontWeight.W_700, font=DISPLAY, color="white" if primary else TEXT),
            ]),
        )

    async def share_file(self, o):
        await self.buzz()
        try:
            await self.share.share_files([ft.ShareFile.from_path(str(o.path), name=o.path.name)],
                                         text=f"{o.path.name} ({human_size(o.size)}) made with FileFit")
        except Exception as exc:
            self.toast(f"Sharing failed: {exc}", ERR)

    async def save_file(self, o):
        await self.buzz()
        try:
            where = await self.picker.save_file(dialog_title="Save file", file_name=o.path.name,
                                                src_bytes=o.path.read_bytes())
            if where and self.page.platform not in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS) \
                    and not Path(where).exists():
                shutil.copy(o.path, where)  # desktop pickers only return a path
            if where:
                self.toast("Saved", OK)
        except Exception as exc:
            self.toast(f"Saving failed: {exc}", ERR)

    # ---------------------------------------------------------- bits
    def toast(self, message, color=TEXT):
        self.page.show_dialog(ft.SnackBar(content=txt(message, color=INK, weight=ft.FontWeight.W_600),
                                          bgcolor=color, behavior=ft.SnackBarBehavior.FLOATING))

    def show_support(self, e=None):
        async def pay(e):
            try:
                ok = await self.urls.launch_url(UPI_URI)
            except Exception:
                ok = False
            if ok is False:
                self.toast("No UPI app found. Scan the QR code instead.", WARN)

        async def copy(e):
            try:
                await ft.Clipboard().set(UPI_ID)
            except Exception:
                pass
            self.toast("UPI ID copied", OK)

        self.page.show_dialog(ft.AlertDialog(
            bgcolor=SURFACE,
            title=txt("Enjoying FileFit?", size=20, weight=ft.FontWeight.W_700, font=DISPLAY),
            content=ft.Column(tight=True, spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                txt("FileFit is free, has no ads and never tracks you. If it saved your form, a small UPI tip "
                    "helps keep it that way.", color=MUTED, size=14),
                ft.Container(bgcolor="white", border_radius=18, padding=10,
                             content=ft.Image(src="upi_qr.png", width=190, height=190)),
                txt(UPI_ID, size=15, weight=ft.FontWeight.W_600, selectable=True),
                ft.Container(
                    height=50, border_radius=16, gradient=GRAD, ink=True, on_click=pay, alignment=ft.Alignment(0, 0),
                    content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=8, controls=[
                        ft.Icon(ft.Icons.CURRENCY_RUPEE_ROUNDED, color="white", size=20),
                        txt("Pay with any UPI app", size=15, weight=ft.FontWeight.W_700, font=DISPLAY, color="white"),
                    ]),
                ),
            ]),
            actions=[
                ft.TextButton(content=txt("Copy UPI ID", color=TEAL), on_click=copy),
                ft.TextButton(content=txt("Close", color=MUTED), on_click=lambda e: self.page.pop_dialog()),
            ],
        ))

    def show_about(self, e):
        async def open_site(e):
            await self.urls.launch_url("https://dipanjanbanerjee.github.io/filefit/")

        async def email(e):
            await self.urls.launch_url(f"mailto:{__email__}?subject=FileFit")

        def replay(e):
            self.page.pop_dialog()
            self.show_welcome()

        self.page.show_dialog(ft.AlertDialog(
            bgcolor=SURFACE,
            title=ft.Row(spacing=12, controls=[badge_icon(ft.Icons.BOLT_ROUNDED, GRAD, size=40, icon_size=22),
                                               txt(f"FileFit {__version__}", size=20, weight=ft.FontWeight.W_700,
                                                   font=DISPLAY)]),
            content=ft.Column(tight=True, spacing=10, controls=[
                txt("Convert and shrink files for any upload portal. Works fully offline; your files never "
                    "leave your phone.", color=MUTED, size=14),
                txt(f"Made by {__author__}", size=14, weight=ft.FontWeight.W_600),
                txt(__email__, size=14, color=TEAL, selectable=True),
            ]),
            actions=[
                ft.TextButton(content=txt("Support", color=PINK), on_click=lambda e: (self.page.pop_dialog(),
                                                                                    self.show_support())),
                ft.TextButton(content=txt("Welcome tour", color=MUTED), on_click=replay),
                ft.TextButton(content=txt("Email", color=TEAL), on_click=email),
                ft.TextButton(content=txt("Website", color=TEAL), on_click=open_site),
            ],
        ))


UPI_ID = "dipanjanbanerjee@pnb"
UPI_URI = f"upi://pay?pa={UPI_ID}&pn=Dipanjan%20Banerjee&cu=INR&tn=Support%20FileFit"


def friendly_error(msg: str | None) -> str:
    if not msg:
        return "Something went wrong."
    if "Word" in msg or "LibreOffice" in msg:
        return "Turning Word files into PDF or pictures needs a computer. Use FileFit on Windows for this one."
    if "password" in msg.lower():
        return "This PDF is password protected. Remove the password first."
    return msg


async def main(page: ft.Page):
    page.title = "FileFit"
    page.fonts = {"Outfit": "fonts/Outfit.ttf", "DMSans": "fonts/DMSans.ttf"}
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = page.dark_theme = ft.Theme(color_scheme_seed=VIOLET, font_family=BODY)
    page.padding = 0
    page.spacing = 0
    page.bgcolor = INK
    app = FileFitApp(page)
    demo = os.environ.get("FILEFIT_DEMO_FILES")  # for screenshots and tests on a computer
    if demo:
        app.files = [Path(x) for x in demo.split(os.pathsep) if Path(x).exists()]
    await app.start()
    if os.environ.get("FILEFIT_DEMO_SUPPORT"):
        app.show_home()
        app.show_support()
    if os.environ.get("FILEFIT_DEMO_FORMAT"):  # test hook: convert the demo files straight away
        app.fmt = os.environ["FILEFIT_DEMO_FORMAT"]
        app.limit = int(os.environ.get("FILEFIT_DEMO_LIMIT", "0")) or None
        app.show_home()
        await app.run(None)


if __name__ == "__main__":
    view = ft.AppView.WEB_BROWSER if os.environ.get("FILEFIT_WEB") else ft.AppView.FLET_APP
    ft.run(main, assets_dir="assets", view=view, port=int(os.environ.get("FILEFIT_PORT", "0")),
           no_cdn=bool(os.environ.get("FILEFIT_WEB")))
