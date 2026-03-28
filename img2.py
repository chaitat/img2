import sys
import os
import subprocess
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QProgressBar,
    QMenuBar,
    QMenu,
    QDialog,
    QTextEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtGui import QDesktopServices, QIcon, QPixmap


__version__ = "1.0.4"

debug_logs: List[str] = []
debug_lock = __import__('threading').Lock()

VALID_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".tiff", ".tif",
    ".bmp", ".gif", ".ico", ".cur", ".svg", ".ppm"
})

OUTPUT_FORMATS = ["jpg", "png", "gif", "webp", "avif", "ico"]

RESIZE_MODES = ["no resize", "fix width", "fix height", "crop by ratio"]

DEFAULT_QUALITY = 75
DEFAULT_WIDTH = "1920"
DEFAULT_HEIGHT = "1080"
DEFAULT_RATIO = "1:1"

MAGICK_PATHS = [
    "/opt/homebrew/bin/magick",
    "/usr/local/bin/magick",
    str(os.path.expanduser("~/.local/bin/magick")),
]


def resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


class ConvertWorker(QThread):
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, paths: List[str], fmt: str, mode: str, size: str, quality: int):
        super().__init__()
        self.paths = paths
        self.fmt = fmt
        self.mode = mode
        self.size = size
        self.quality = quality
        self.files: List[str] = []

    def is_valid(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in VALID_EXTENSIONS

    def build_resize(self) -> Optional[str]:
        if self.mode == "no resize":
            return None
        if self.mode == "crop by ratio":
            return self.size
        if not self.size.isdigit():
            return None
        if self.mode == "fix width":
            return self.size
        if self.mode == "fix height":
            return f"x{self.size}"
        return None

    def find_magick(self) -> Optional[str]:
        import shutil
        magick_path = shutil.which("magick")
        if magick_path:
            return magick_path
        for path in MAGICK_PATHS:
            if os.path.exists(path):
                return path
        return None

    def run(self) -> None:
        magick = self.find_magick()
        if not magick:
            self.error_signal.emit("ImageMagick not found. Please install: brew install imagemagick")
            return

        self.file_origins = {}
        for path in self.paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        full = os.path.join(root, f)
                        if self.is_valid(full):
                            self.files.append(full)
                            self.file_origins[full] = path
            else:
                if self.is_valid(path):
                    self.files.append(path)
                    self.file_origins[path] = path

        total = len(self.files)
        if total == 0:
            return

        for i, file_path in enumerate(self.files, start=1):
            original_path = self.file_origins.get(file_path, file_path)
            self.process_file(file_path, magick, original_path)
            percent = int((i / total) * 100)
            self.progress_signal.emit(percent)

    def process_file(self, file_path: str, magick: str, original_path: str) -> None:
        base_dir = os.path.dirname(file_path)
        
        if os.path.isdir(original_path):
            output_dir = f"{base_dir}-img2{self.fmt}"
        else:
            output_dir = os.path.join(base_dir, f"img2{self.fmt}")
            
        os.makedirs(output_dir, exist_ok=True)

        filename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{filename}.{self.fmt}")

        cmd = [magick, file_path]
        resize_arg = self.build_resize()

        if resize_arg:
            if self.mode == "crop by ratio":
                cmd += ["-gravity", "Center", "-extent", resize_arg]
            else:
                cmd += ["-resize", resize_arg]

        cmd += ["-quality", str(self.quality), output_path]

        cmd_str = f"magick {file_path}"
        if resize_arg:
            if self.mode == "crop by ratio":
                cmd_str += f" -gravity Center -extent {resize_arg}"
            else:
                cmd_str += f" -resize {resize_arg}"
        cmd_str += f" -quality {self.quality} {output_path}"
        
        with debug_lock:
            debug_logs.append(cmd_str)

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            error_msg = result.stderr.decode()
            self.error_signal.emit(f"Error processing {file_path}: {error_msg}")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About img2")
        self.setFixedSize(300, 350)

        icon_path = resource_path(os.path.join("images", "icon-128.png"))
        
        layout = QVBoxLayout()
        
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        title = QLabel("img2")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(title)

        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        desc = QLabel("Simple images converter")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(desc)

        bmc_path = resource_path(os.path.join("images", "bmc-s.png"))
        if os.path.exists(bmc_path):
            self.bmc_label = QLabel()
            self.bmc_label.setPixmap(QPixmap(bmc_path).scaled(250, 70, Qt.AspectRatioMode.KeepAspectRatio))
            self.bmc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.bmc_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self.bmc_label.mousePressEvent = self.open_bmc
            layout.addWidget(self.bmc_label)

        layout.addStretch()
        self.setLayout(layout)

    def open_bmc(self, event):
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/chaitat"))


class DebugDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug - Magick Commands")
        self.resize(480, 200)

        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_log)
        btn_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_log)
        self.timer.start(500)
        self.refresh_log()

    def refresh_log(self):
        with debug_lock:
            log_content = "\n".join(debug_logs)
        if self.log_text.toPlainText() != log_content:
            scrollbar = self.log_text.verticalScrollBar()
            at_bottom = scrollbar.value() == scrollbar.maximum()
            self.log_text.setPlainText(log_content)
            if at_bottom:
                scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        with debug_lock:
            debug_logs.clear()
        self.log_text.clear()


class UpdateWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def run(self) -> None:
        try:
            subprocess.run(["brew", "update"], capture_output=True, text=True)
            result = subprocess.run(["brew", "outdated", "img2"], capture_output=True, text=True)
            
            if "img2" in result.stdout or result.returncode != 0:
                self.finished_signal.emit(True, "Update available! Run: brew upgrade img2")
            else:
                self.finished_signal.emit(False, "img2 is up to date")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class Img2App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("img2")
        self.setFixedSize(480, 400)
        self.setAcceptDrops(True)

        icon_path = os.path.join(os.path.dirname(__file__), "images", "icon-128.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_menu()

        top_layout = QHBoxLayout()

        self.format_box = QComboBox()
        self.format_box.addItems(OUTPUT_FORMATS)
        self.format_box.setFixedWidth(100)

        self.quality_input = QLineEdit(str(DEFAULT_QUALITY))
        self.quality_input.setFixedWidth(50)
        self.quality_input.setStyleSheet("padding: 2px 10px;")

        self.resize_mode = QComboBox()
        self.resize_mode.addItems(RESIZE_MODES)
        self.resize_mode.setFixedWidth(120)

        self.size_input = QLineEdit(DEFAULT_WIDTH)
        self.size_input.setFixedWidth(80)
        self.size_input.setStyleSheet("padding: 2px 10px;")

        self.int_validator = QRegularExpressionValidator(QRegularExpression(r"^\d+$"))
        self.ratio_validator = QRegularExpressionValidator(QRegularExpression(r"^\d+:\d+$"))
        self.size_input.setValidator(self.int_validator)

        top_layout.addWidget(self.format_box)
        top_layout.addWidget(QLabel("Quality"))
        top_layout.addWidget(self.quality_input)
        top_layout.addWidget(QLabel("size"))
        top_layout.addWidget(self.resize_mode)
        top_layout.addWidget(self.size_input)

        self.resize_mode.currentTextChanged.connect(self.on_resize_mode_change)
        self.on_resize_mode_change()
        top_layout.addStretch()

        self.drop_area = QLabel("drop image or folder here")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setStyleSheet("""
            background-color: rgba(255,255,255,0);
            color: #666;
            border-radius: 10px;
            border: 2px dashed rgba(128,128,128,0.3);
            font-size: 12px;
        """)
        self.drop_area.setMinimumHeight(250)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.drop_area)
        layout.addWidget(self.progress)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        help_menu = QMenu("img2", self)
        menubar.addMenu(help_menu)

        help_menu.addAction("About img2", self.show_about)
        help_menu.addAction("Update App", self.update_app)
        help_menu.addAction("Debug magick command", self.show_debug)

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def show_debug(self):
        dialog = DebugDialog(self)
        dialog.refresh_log()
        dialog.show()

    def update_app(self):
        result = QMessageBox.question(
            self, 
            "Update App", 
            "Check for updates via Homebrew?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            self.progress.setValue(0)
            self.update_worker = UpdateWorker()
            self.update_worker.finished_signal.connect(self.on_update_finished)
            self.update_worker.start()

    def on_update_finished(self, has_update: bool, message: str):
        self.progress.setValue(100)
        if has_update:
            QMessageBox.information(self, "Update", message)
        else:
            QMessageBox.information(self, "Update", message)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]

        fmt = self.format_box.currentText()
        
        try:
            quality = int(self.quality_input.text())
            if not 1 <= quality <= 100:
                raise ValueError("Quality must be between 1 and 100")
        except ValueError:
            QMessageBox.warning(self, "Error", "Quality must be a number between 1 and 100")
            return
            
        mode = self.resize_mode.currentText()
        size = self.size_input.text().strip()

        self.worker = ConvertWorker(paths, fmt, mode, size, quality)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.error_signal.connect(self.show_error)

        self.progress.setValue(0)
        self.worker.start()

    def show_error(self, message: str):
        QMessageBox.warning(self, "Error", message)

    def update_progress(self, value: int):
        self.progress.setValue(value)

    def on_resize_mode_change(self):
        mode = self.resize_mode.currentText()
        self.size_input.setEnabled(mode != "no resize")
        
        if mode == "crop by ratio":
            self.size_input.setText(DEFAULT_RATIO)
            self.size_input.setValidator(self.ratio_validator)
        elif mode == "fix width":
            self.size_input.setText(DEFAULT_WIDTH)
            self.size_input.setValidator(self.int_validator)
        elif mode == "fix height":
            self.size_input.setText(DEFAULT_HEIGHT)
            self.size_input.setValidator(self.int_validator)
        else:
            self.size_input.setText("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Img2App()
    window.show()
    sys.exit(app.exec())
