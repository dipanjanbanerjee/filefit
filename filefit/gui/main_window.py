from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPointF, QSettings, QSize, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QGuiApplication, QIcon, QPainter, QPixmap,
                           QRadialGradient)
from PySide6.QtWidgets import (
    QApplication,     QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFileIconProvider, QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QDialog, QMainWindow, QMessageBox, QProgressBar, QProgressDialog, QPushButton, QRadioButton, QScrollArea, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget,
)

from .. import __app_name__, __author__, __email__, __version__
from .. import updater
from ..core import INPUT_EXTS, OUTPUT_FORMATS, Options, combine_to_pdf, convert_file, human_size, kind_of
from . import style

PRESETS = [("100 KB", 100, "KB"), ("200 KB", 200, "KB"), ("500 KB", 500, "KB"),
           ("1 MB", 1, "MB"), ("2 MB", 2, "MB"), ("5 MB", 5, "MB")]
UPI_ID = "dipanjanbanerjee@pnb"
UPI_URI = f"upi://pay?pa={UPI_ID}&pn=Dipanjan%20Banerjee&cu=INR&tn=Support%20FileFit"
FILE_FILTER = "Supported files ({});;All files (*)".format(" ".join(f"*{e}" for e in sorted(INPUT_EXTS)))


def asset(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / name


# ---------------------------------------------------------------- worker

class Worker(QThread):
    progress = Signal(int, str)
    result = Signal(object)

    def __init__(self, files: list[Path], opts: Options):
        super().__init__()
        self.files, self.opts = files, opts

    def run(self):
        try:
            self._run()
        except Exception as exc:  # never let a bad file take the window down
            from ..core.convert import JobResult
            self.result.emit(JobResult(source=self.files[0], error=f"Unexpected problem: {exc}"))
            self.progress.emit(100, "Stopped")

    def _run(self):
        if self.opts.combine and len(self.files) > 1:
            self.progress.emit(0, "Combining files into one PDF")
            self.result.emit(combine_to_pdf(self.files, self.opts, lambda m: self.progress.emit(-1, m)))
            self.progress.emit(100, "Done")
            return
        total = len(self.files)
        for i, f in enumerate(self.files):
            self.progress.emit(int(i * 100 / total), f"Working on {f.name}")
            res = convert_file(f, self.opts, lambda m: self.progress.emit(-1, f"{f.name}: {m}"))
            self.result.emit(res)
        self.progress.emit(100, "Done")


class UpdateChecker(QThread):
    found = Signal(object)
    up_to_date = Signal()
    failed = Signal(str)

    def run(self):
        try:
            rel = updater.check()
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.found.emit(rel) if rel else self.up_to_date.emit()


class UpdateDownloader(QThread):
    progress = Signal(int, int)
    ready = Signal(object)
    failed = Signal(str)

    def __init__(self, rel):
        super().__init__()
        self.rel = rel

    def run(self):
        try:
            self.ready.emit(updater.prepare(self.rel, lambda d, t: self.progress.emit(d, t)))
        except Exception as exc:
            self.failed.emit(str(exc))


# ---------------------------------------------------------------- background

class Backdrop(QWidget):
    """Deep ink background with soft colour glows and a faint dot grid."""

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(style.INK))
        for x, y, r, color, alpha in [(0.08, 0.0, 0.55, style.VIOLET, 110), (1.0, 1.0, 0.6, style.TEAL, 70),
                                      (0.62, 0.12, 0.35, style.PINK, 38)]:
            g = QRadialGradient(QPointF(x * w, y * h), r * max(w, h))
            c = QColor(color)
            c.setAlpha(alpha)
            g.setColorAt(0, c)
            c.setAlpha(0)
            g.setColorAt(1, c)
            p.fillRect(self.rect(), QBrush(g))
        dot = QColor("#FFFFFF")
        dot.setAlpha(14)
        p.setPen(Qt.NoPen)
        p.setBrush(dot)
        for gx in range(12, w, 26):
            for gy in range(12, h, 26):
                p.drawEllipse(QPointF(gx, gy), 1.1, 1.1)


# ---------------------------------------------------------------- drop zone

class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(150)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        icon = QLabel("+")
        icon.setObjectName("dropIcon")
        icon.setFixedSize(58, 58)
        title = QLabel("Drop files here")
        title.setObjectName("dropTitle")
        hint = QLabel("or click to browse  ·  JPG, JPEG, PNG, WEBP, HEIC, PDF, DOCX")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        for w in (icon, title, hint):
            w.setAlignment(Qt.AlignCenter)
            lay.addWidget(w, 0, Qt.AlignHCenter)

    def _set_hover(self, on: bool):
        self.setProperty("hover", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files", "", FILE_FILTER)
        if paths:
            self.files_dropped.emit([Path(p) for p in paths])

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._set_hover(True)

    def dragLeaveEvent(self, e):
        self._set_hover(False)

    def dropEvent(self, e):
        self._set_hover(False)
        paths = []
        for url in e.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                paths += [c for c in sorted(p.iterdir()) if c.suffix.lower() in INPUT_EXTS]
            elif p.is_file():
                paths.append(p)
        self.files_dropped.emit(paths)


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 16, 18, 18)
    lay.setSpacing(10)
    return frame, lay


def label(text: str, name: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName(name)
    lab.setWordWrap(True)
    return lab


# ---------------------------------------------------------------- window

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} — File Converter & Compressor")
        if asset("icon.png").exists():
            self.setWindowIcon(QIcon(str(asset("icon.png"))))
        self.resize(1120, 760)
        self.setMinimumSize(940, 640)
        self.icons = QFileIconProvider()
        self.worker: Worker | None = None
        self.out_dir: Path | None = None
        self.last_folder: Path | None = None

        root = Backdrop(objectName="root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(24, 22, 24, 22)
        outer.setSpacing(20)
        outer.addLayout(self._build_left(), 1)
        outer.addWidget(self._build_right())
        self._refresh()

        self.settings = QSettings("FileFit", "FileFit")
        self.release = None
        self.checker: UpdateChecker | None = None
        updater.cleanup_after_update()
        if self.settings.value("auto_update_check", True, type=bool):
            QTimer.singleShot(1500, lambda: self.check_updates(manual=False))

    # ---- left: files and results
    def _build_left(self):
        col = QVBoxLayout()
        col.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(14)
        badge = QLabel()
        badge.setFixedSize(52, 52)
        if asset("icon.png").exists():
            dpr = self.devicePixelRatioF() or 1
            pm = QPixmap(str(asset("icon.png"))).scaled(int(52 * dpr), int(52 * dpr), Qt.KeepAspectRatio,
                                                         Qt.SmoothTransformation)
            pm.setDevicePixelRatio(dpr)
            badge.setPixmap(pm)
        head.addWidget(badge)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(label(__app_name__, "title"))
        titles.addWidget(label("Make any file fit the upload box.", "subtitle"))
        head.addLayout(titles, 1)
        upd = QPushButton("⟳  Updates", objectName="ghost")
        upd.setCursor(Qt.PointingHandCursor)
        upd.setToolTip("Check for a newer version of FileFit")
        upd.clicked.connect(lambda: self.check_updates(manual=True))
        head.addWidget(upd, 0, Qt.AlignVCenter)
        support = QPushButton("♥  Support FileFit", objectName="support")
        support.setCursor(Qt.PointingHandCursor)
        support.clicked.connect(self.show_support)
        head.addWidget(support, 0, Qt.AlignVCenter)
        col.addLayout(head)
        col.addSpacing(4)

        self.banner = QFrame(objectName="banner")
        b = QHBoxLayout(self.banner)
        b.setContentsMargins(16, 10, 10, 10)
        self.banner_text = label("", "bannerText")
        b.addWidget(self.banner_text, 1)
        self.banner_btn = QPushButton("Update now", objectName="bannerBtn")
        self.banner_btn.setCursor(Qt.PointingHandCursor)
        self.banner_btn.clicked.connect(self.install_update)
        b.addWidget(self.banner_btn)
        later = QPushButton("Later", objectName="ghost")
        later.setCursor(Qt.PointingHandCursor)
        later.clicked.connect(self.banner.hide)
        b.addWidget(later)
        self.banner.hide()
        col.addWidget(self.banner)

        self.drop = DropZone()
        self.drop.files_dropped.connect(self.add_files)
        col.addWidget(self.drop)

        head = QHBoxLayout()
        self.files_label = label("FILES", "section")
        head.addWidget(self.files_label)
        head.addStretch()
        self.btn_remove = QPushButton("Remove")
        self.btn_clear = QPushButton("Clear all")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_files)
        head.addWidget(self.btn_remove)
        head.addWidget(self.btn_clear)
        col.addLayout(head)

        self.file_list = QListWidget()
        self.file_list.setIconSize(QSize(28, 28))
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setDragDropMode(QAbstractItemView.InternalMove)  # reorder for combining
        self.file_list.itemSelectionChanged.connect(self._refresh)
        col.addWidget(self.file_list, 3)

        rhead = QHBoxLayout()
        rhead.addWidget(label("RESULTS", "section"))
        rhead.addStretch()
        self.btn_open = QPushButton("Open output folder")
        self.btn_open.clicked.connect(self.open_output_folder)
        rhead.addWidget(self.btn_open)
        col.addLayout(rhead)

        self.results = QListWidget()
        self.results.setIconSize(QSize(24, 24))
        self.results.itemDoubleClicked.connect(self._open_result)
        self.results.setToolTip("Double-click a result to open it")
        col.addWidget(self.results, 2)
        credit = label(f"{__app_name__} {__version__}  ·  Made by {__author__}  ·  "
                       f"<a href='mailto:{__email__}'>{__email__}</a>", "muted")
        credit.setOpenExternalLinks(True)
        col.addWidget(credit)
        return col

    # ---- right: settings
    def _build_right(self):
        frame, outer = card()
        frame.setFixedWidth(400)
        outer.setContentsMargins(6, 8, 6, 18)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(14, 10, 14, 6)
        lay.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

        lay.addWidget(label("CONVERT TO", "section"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.format_group = QButtonGroup(self)
        for i, name in enumerate(OUTPUT_FORMATS):
            b = QPushButton(name, objectName="format", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            self.format_group.addButton(b)
            grid.addWidget(b, i // 3, i % 3)
            if name == "PDF":
                b.setChecked(True)
        self.format_group.buttonClicked.connect(lambda _: self._refresh())
        lay.addLayout(grid)
        self.format_hint = label("", "hint")
        lay.addWidget(self.format_hint)

        lay.addSpacing(4)
        lay.addWidget(label("FILE SIZE LIMIT", "section"))
        self.chk_limit = QCheckBox("Keep each file under")
        self.chk_limit.toggled.connect(self._refresh)
        row = QHBoxLayout()
        self.spin_size = QDoubleSpinBox(decimals=1, minimum=0.1, maximum=99999, value=2.0)
        self.spin_size.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.chip_group = None
        self.unit = QComboBox()
        self.unit.addItems(["KB", "MB"])
        self.unit.setCurrentText("MB")
        self.spin_size.valueChanged.connect(lambda _: self._refresh())
        self.unit.currentTextChanged.connect(lambda _: self._refresh())
        self.spin_size.setAlignment(Qt.AlignCenter)
        self.unit.setEditable(True)
        self.unit.lineEdit().setReadOnly(True)
        self.unit.lineEdit().setAlignment(Qt.AlignCenter)
        self.unit.lineEdit().installEventFilter(self)  # click anywhere opens the list
        self.spin_size.setFixedWidth(90)
        self.unit.setFixedWidth(72)
        row.addWidget(self.chk_limit)
        row.addStretch()
        row.addWidget(self.spin_size)
        row.addWidget(self.unit)
        lay.addLayout(row)
        chips = QGridLayout()
        chips.setSpacing(6)
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(False)  # checked state just mirrors the size box
        for i, (text, val, unit) in enumerate(PRESETS):
            c = QPushButton(text, objectName="chip", checkable=True)
            c.setCursor(Qt.PointingHandCursor)
            self.chip_group.addButton(c)
            c.clicked.connect(lambda _=False, v=val, u=unit: self._preset(v, u))
            chips.addWidget(c, i // 3, i % 3)
        lay.addLayout(chips)

        lay.addSpacing(4)
        lay.addWidget(label("RESIZE PICTURES", "section"))
        self.chk_resize = QCheckBox("Limit width and height (keeps proportions)")
        self.chk_resize.toggled.connect(self._refresh)
        lay.addWidget(self.chk_resize)
        row = QHBoxLayout()
        self.spin_w = QSpinBox(minimum=16, maximum=20000, value=1200, suffix=" px")
        self.spin_h = QSpinBox(minimum=16, maximum=20000, value=1200, suffix=" px")
        for sp in (self.spin_w, self.spin_h):
            sp.setButtonSymbols(QSpinBox.NoButtons)
            sp.setAlignment(Qt.AlignCenter)
        row.addWidget(QLabel("Max width"))
        row.addWidget(self.spin_w, 1)
        row.addWidget(QLabel("Max height"))
        row.addWidget(self.spin_h, 1)
        lay.addLayout(row)

        lay.addSpacing(4)
        lay.addWidget(label("OPTIONS", "section"))
        self.chk_combine = QCheckBox("Combine all files into one PDF")
        self.chk_combine.setToolTip("Drag files in the list to change their order")
        lay.addWidget(self.chk_combine)

        lay.addWidget(label("SAVE TO", "section"))
        self.rad_same = QRadioButton("Same folder as the original", checked=True)
        self.rad_choose = QRadioButton("Choose a folder…")
        self.rad_choose.clicked.connect(self.choose_folder)
        self.rad_same.toggled.connect(self._refresh)
        lay.addWidget(self.rad_same)
        lay.addWidget(self.rad_choose)
        self.folder_label = label("", "muted")
        lay.addWidget(self.folder_label)

        lay.addStretch()

        foot = QVBoxLayout()
        foot.setContentsMargins(14, 6, 14, 0)
        foot.setSpacing(10)
        self.status = label("Add some files to get started.", "muted")
        foot.addWidget(self.status)
        self.progress = QProgressBar(maximum=100, value=0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)  # only while working
        foot.addWidget(self.progress)
        self.btn_go = QPushButton("✦  Make it fit", objectName="primary")
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.clicked.connect(self.start)
        foot.addWidget(self.btn_go)
        outer.addLayout(foot)
        return frame

    # ---- state
    def files(self) -> list[Path]:
        return [Path(self.file_list.item(i).data(Qt.UserRole)) for i in range(self.file_list.count())]

    def out_format(self) -> str:
        return self.format_group.checkedButton().text()

    def _refresh(self):
        busy = self.worker is not None and self.worker.isRunning()
        n = self.file_list.count()
        fmt = self.out_format()
        self.files_label.setText(f"FILES ({n})" if n else "FILES")
        self.spin_size.setEnabled(self.chk_limit.isChecked())
        cur = (self.spin_size.value(), self.unit.currentText())
        for b, (_t, v, u) in zip(self.chip_group.buttons() if self.chip_group else [], PRESETS):
            b.setChecked(self.chk_limit.isChecked() and cur == (v, u))
        self.unit.setEnabled(self.chk_limit.isChecked())
        self.spin_w.setEnabled(self.chk_resize.isChecked())
        self.spin_h.setEnabled(self.chk_resize.isChecked())
        self.chk_combine.setEnabled(fmt == "PDF" and n > 1)
        self.btn_remove.setEnabled(bool(self.file_list.selectedItems()) and not busy)
        self.btn_clear.setEnabled(n > 0 and not busy)
        self.btn_go.setEnabled(n > 0 and not busy)
        self.btn_open.setEnabled(self.last_folder is not None)
        hints = {
            "JPG": "Best for photos and scanned pages. Each PDF page becomes its own picture.",
            "JPEG": "Same as JPG, saved with the .jpeg ending some portals ask for.",
            "PNG": "Sharp text and logos, but larger files than JPG.",
            "WEBP": "Modern format with small files. Not every portal accepts it.",
            "PDF": "One PDF per file, or tick Combine to merge them.",
            "DOCX": "Word document. PDFs are rebuilt as editable text where possible.",
        }
        self.format_hint.setText(hints[fmt])
        if self.rad_choose.isChecked() and self.out_dir:
            self.folder_label.setText(str(self.out_dir))
        else:
            self.folder_label.setText("New files get a new name; originals are never changed.")

    def _preset(self, val, unit):
        self.chk_limit.setChecked(True)
        self.unit.setCurrentText(unit)
        self.spin_size.setValue(val)
        self._refresh()

    def add_files(self, paths: list[Path]):
        existing = set(map(str, self.files()))
        skipped = []
        for p in paths:
            try:
                kind_of(p)
            except ValueError:
                skipped.append(p.name)
                continue
            if str(p) in existing:
                continue
            existing.add(str(p))
            item = QListWidgetItem(self.icons.icon(QFileInfo(str(p))),
                                   f"{p.name}\n{human_size(p.stat().st_size)}  ·  {p.suffix.upper().lstrip('.')}")
            item.setData(Qt.UserRole, str(p))
            item.setToolTip(str(p))
            self.file_list.addItem(item)
        if skipped:
            self.status.setText("Skipped unsupported: " + ", ".join(skipped[:4]) + ("…" if len(skipped) > 4 else ""))
        elif paths:
            self.status.setText("Ready. Pick a format and press Make it fit.")
        self._refresh()

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self._refresh()

    def clear_files(self):
        self.file_list.clear()
        self._refresh()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Save converted files to")
        if folder:
            self.out_dir = Path(folder)
        elif not self.out_dir:
            self.rad_same.setChecked(True)
        self._refresh()

    # ---- run
    def options(self) -> Options:
        target = None
        if self.chk_limit.isChecked():
            mult = 1024 * 1024 if self.unit.currentText() == "MB" else 1024
            target = int(self.spin_size.value() * mult)
        resize = self.chk_resize.isChecked()
        return Options(
            out_format=self.out_format(),
            out_dir=self.out_dir if self.rad_choose.isChecked() else None,
            target_bytes=target,
            max_width=self.spin_w.value() if resize else None,
            max_height=self.spin_h.value() if resize else None,
            combine=self.chk_combine.isEnabled() and self.chk_combine.isChecked(),
        )

    def start(self):
        files = self.files()
        if not files:
            return
        self.results.clear()
        self.progress.setValue(0)
        self.worker = Worker(files, self.options())
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.btn_go.setText("Working…")
        self.progress.setVisible(True)
        self.worker.start()
        self._refresh()

    def _on_progress(self, pct: int, msg: str):
        if pct >= 0:
            self.progress.setValue(pct)
        self.status.setText(msg)

    def _on_result(self, res):
        if res.error:
            item = QListWidgetItem(f"✗  {res.source.name}\n{res.error}")
            item.setForeground(QColor(style.ERR))
            self.results.addItem(item)
            return
        for out in res.outputs:
            mark = "✓" if out.fits else "⚠"
            detail = human_size(out.size)
            if not out.fits:
                detail += "  ·  still above the limit"
            if out.note:
                detail += f"  ·  {out.note}"
            item = QListWidgetItem(self.icons.icon(QFileInfo(str(out.path))), f"{mark}  {out.path.name}\n{detail}")
            item.setData(Qt.UserRole, str(out.path))
            item.setToolTip(str(out.path))
            item.setForeground(QColor(style.OK if out.fits else style.WARN))
            self.results.addItem(item)
            self.last_folder = out.path.parent

    def _on_finished(self):
        self.btn_go.setText("✦  Make it fit")
        self.progress.setVisible(False)
        made = sum(1 for i in range(self.results.count()) if self.results.item(i).data(Qt.UserRole))
        self.status.setText(f"Finished. {made} file{'s' if made != 1 else ''} created.")
        self.worker = None
        self._refresh()

    def _open_result(self, item):
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_output_folder(self):
        if self.last_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_folder)))

    # ---- updates
    def check_updates(self, manual: bool):
        if self.checker and self.checker.isRunning():
            return
        self.checker = UpdateChecker()
        self.checker.found.connect(lambda rel: self._update_found(rel, manual))
        if manual:
            self.checker.up_to_date.connect(self._up_to_date)
            self.checker.failed.connect(lambda err: self._ask_auto(
                QMessageBox.Warning, "Could not check for updates",
                "FileFit could not reach GitHub. Check the internet connection and try again."))
        self.checker.start()

    def _ask_auto(self, icon, title, text):
        box = QMessageBox(icon, title, text, QMessageBox.Ok, self)
        auto = QCheckBox("Check for updates automatically when FileFit starts")
        auto.setChecked(self.settings.value("auto_update_check", True, type=bool))
        box.setCheckBox(auto)
        box.exec()
        self.settings.setValue("auto_update_check", auto.isChecked())

    def _up_to_date(self):
        self._ask_auto(QMessageBox.Information, "FileFit is up to date",
                       f"You have the latest version, FileFit {__version__}.")

    def _update_found(self, rel, manual: bool):
        self.release = rel
        kind = updater.install_kind()
        self.banner_text.setText(f"<b>FileFit {rel.version} is available.</b>  You have {__version__}.")
        self.banner_btn.setText("Update now" if updater.can_self_install() else "How to update")
        self.banner.show()
        if manual:
            self.install_update()

    def install_update(self):
        rel = self.release
        if not rel:
            return
        kind = updater.install_kind()
        if kind == "pip":
            box = QMessageBox(QMessageBox.Information, "Update FileFit",
                              f"FileFit {rel.version} is available. Close FileFit, then run this in a terminal:"
                              "\n\n    pipx upgrade filefit\n\n(If you installed with pip: pip install -U filefit)",
                              QMessageBox.Ok, self)
            copy = box.addButton("Copy command", QMessageBox.ActionRole)
            box.exec()
            if box.clickedButton() is copy:
                QGuiApplication.clipboard().setText("pipx upgrade filefit")
            return
        if kind == "linux-app":
            QDesktopServices.openUrl(QUrl(rel.page))
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Update FileFit", "Please wait until the current conversion finishes.")
            return
        if QMessageBox.question(self, "Update FileFit",
                                f"Download and install FileFit {rel.version} now?\n\n"
                                "FileFit will close for a moment and open again by itself.") != QMessageBox.Yes:
            return
        dlg = QProgressDialog("Downloading the update…", "Cancel", 0, 100, self)
        dlg.setWindowTitle("Updating FileFit")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dl = UpdateDownloader(rel)
        self._downloader = dl
        dl.progress.connect(lambda d, t: (dlg.setMaximum(100), dlg.setValue(int(d * 100 / t)) if t else
                                          dlg.setMaximum(0)))

        def ready(start_install):
            if dlg.wasCanceled():
                return
            dlg.setLabelText("Installing…")
            try:
                start_install()
            except Exception as exc:
                dlg.close()
                self._update_failed(str(exc))
                return
            QApplication.instance().quit()

        dl.ready.connect(ready)
        dl.failed.connect(lambda err: (dlg.close(), self._update_failed(err)))
        dl.start()
        dlg.show()

    def _update_failed(self, err: str):
        box = QMessageBox(QMessageBox.Warning, "Update did not finish",
                          f"{err}\n\nYou can download the new version from the FileFit website instead.",
                          QMessageBox.Ok, self)
        site = box.addButton("Open website", QMessageBox.ActionRole)
        box.exec()
        if box.clickedButton() is site:
            QDesktopServices.openUrl(QUrl(updater.WEBSITE))

    def show_support(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Support FileFit")
        dlg.setStyleSheet(f"QDialog {{ background: {style.SURFACE}; }}")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(10)
        head = label("Enjoying FileFit? ♥", "title")
        head.setStyleSheet("font-size: 17pt;")
        lay.addWidget(head)
        lay.addWidget(label("FileFit is free, has no ads and never tracks you. If it saved your form, a small "
                            "UPI tip helps keep it that way.", "subtitle"))
        qr = QLabel(alignment=Qt.AlignCenter)
        if asset("upi_qr.png").exists():
            qr.setPixmap(QPixmap(str(asset("upi_qr.png"))).scaled(220, 220, Qt.KeepAspectRatio,
                                                                    Qt.SmoothTransformation))
        qr.setStyleSheet("background: white; border-radius: 18px; padding: 10px;")
        qr.setFixedSize(244, 244)
        lay.addWidget(qr, 0, Qt.AlignHCenter)
        scan = label("Scan with GPay, PhonePe, Paytm or any UPI app", "subtitle")
        scan.setAlignment(Qt.AlignCenter)
        scan.setStyleSheet(f"color: {style.TEXT}; font-size: 10.5pt;")
        lay.addWidget(scan)
        row = QHBoxLayout()
        upi = label(UPI_ID, "dropTitle")
        upi.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(upi, 1)
        copy = QPushButton("Copy UPI ID")
        copy.setCursor(Qt.PointingHandCursor)

        def do_copy():
            QGuiApplication.clipboard().setText(UPI_ID)
            copy.setText("Copied ✓")

        copy.clicked.connect(do_copy)
        row.addWidget(copy)
        lay.addLayout(row)
        close = QPushButton("Close", objectName="primary")
        close.clicked.connect(dlg.accept)
        lay.addWidget(close)
        dlg.setFixedWidth(440)
        dlg.exec()

    def eventFilter(self, obj, ev):
        from PySide6.QtCore import QEvent
        try:
            if ev.type() == QEvent.MouseButtonPress and obj is self.unit.lineEdit() and self.unit.isEnabled():
                self.unit.showPopup()
                return True
        except RuntimeError:  # window is closing
            return False
        return super().eventFilter(obj, ev)

    def closeEvent(self, e):
        if self.worker and self.worker.isRunning():
            if QMessageBox.question(self, __app_name__, "A conversion is still running. Quit anyway?") \
                    != QMessageBox.Yes:
                e.ignore()
                return
        e.accept()


def log_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else None
    d = Path(base) / "FileFit" if base else Path.home() / ".local" / "state" / "filefit"
    d.mkdir(parents=True, exist_ok=True)
    return d


def install_crash_handler():
    """Show a friendly message and keep a log instead of vanishing on an unexpected error."""
    def handler(kind, exc, tb):
        import traceback
        text = "".join(traceback.format_exception(kind, exc, tb))
        log = None
        try:
            log = log_dir() / "error.log"
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"--- FileFit {__version__} ---\n{text}\n")
        except Exception:
            pass
        sys.__stderr__ and sys.__stderr__.write(text)
        QMessageBox.warning(None, "FileFit hit a problem",
                            "Something went wrong, but your original files are safe. You can keep working.\n\n"
                            f"If it happens again, please email {__email__}"
                            + (f" and attach this file:\n{log}" if log else "."))
    sys.excepthook = handler


def main():
    if sys.platform == "win32":  # own taskbar icon instead of Python's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"FileFit.{__version__}")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setDesktopFileName("filefit")  # lets Linux docks find FileFit's icon
    install_crash_handler()
    if sys.platform.startswith("linux"):
        try:
            from ..cli import install_shortcut
            install_shortcut(quiet=True)  # keep the app menu entry and dock icon in place
        except Exception:
            pass
    app.setStyle("Fusion")
    app.setPalette(style.dark_palette())
    app.setStyleSheet(style.STYLESHEET)
    win = MainWindow()
    files = [Path(a) for a in sys.argv[1:] if Path(a).is_file()]
    if files:  # "Open with FileFit" / drag onto the .exe
        win.add_files(files)
    win.show()
    sys.exit(app.exec())
