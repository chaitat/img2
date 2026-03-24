import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon


class ConvertWorker(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, paths, fmt, mode, size, quality):
        super().__init__()
        self.paths = paths
        self.fmt = fmt
        self.mode = mode
        self.size = size
        self.quality = quality
        self.files = []

    def run(self):
        for path in self.paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        full = os.path.join(root, f)
                        if self.is_valid(full):
                            self.files.append(full)
            else:
                if self.is_valid(path):
                    self.files.append(path)

        total = len(self.files)
        if total == 0:
            return

        for i, file_path in enumerate(self.files, start=1):
            self.process_file(file_path)
            percent = int((i / total) * 100)
            self.progress_signal.emit(percent)

    def is_valid(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return ext in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".avif",
            ".tiff",
            ".bmp",
            ".gif",
            ".ico",
            ".cur",
            ".svg",
        ]

    def build_resize(self):
        if self.mode == "no resize":
            return None
        if not self.size.isdigit():
            return None
        if self.mode == "fix width":
            return self.size
        if self.mode == "fix height":
            return f"x{self.size}"
        return None

    def process_file(self, file_path):
        base_dir = os.path.dirname(file_path)
        output_dir = os.path.join(base_dir, f"img2{self.fmt}")
        os.makedirs(output_dir, exist_ok=True)

        filename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{filename}.{self.fmt}")

        cmd = ["magick", file_path]
        resize_arg = self.build_resize()

        if resize_arg:
            cmd += ["-resize", resize_arg]

        cmd += ["-quality", str(self.quality), output_path]

        try:
            subprocess.run(cmd, check=True)
        except:
            pass


class Img2App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("img2")
        self.setFixedSize(480, 400)
        self.setAcceptDrops(True)

        icon_path = os.path.join(os.path.dirname(__file__), "app-icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        top_layout = QHBoxLayout()

        self.format_box = QComboBox()
        self.format_box.addItems(["jpg", "png", "gif", "webp", "avif", "ico"])
        self.format_box.setFixedWidth(100)

        self.quality_input = QLineEdit("75")
        self.quality_input.setFixedWidth(50)
        self.quality_input.setStyleSheet("padding: 2px 10px;")

        self.resize_mode = QComboBox()
        self.resize_mode.addItems(["no resize", "fix width", "fix height"])
        self.resize_mode.setFixedWidth(100)

        self.size_input = QLineEdit("1280")
        self.size_input.setFixedWidth(80)
        self.size_input.setStyleSheet("padding: 2px 10px;")

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

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]

        fmt = self.format_box.currentText()
        quality = int(self.quality_input.text())
        mode = self.resize_mode.currentText()
        size = self.size_input.text().strip()

        self.worker = ConvertWorker(paths, fmt, mode, size, quality)
        self.worker.progress_signal.connect(self.update_progress)

        self.progress.setValue(0)
        self.worker.start()

    def update_progress(self, value):
        self.progress.setValue(value)

    def on_resize_mode_change(self):
        self.size_input.setEnabled(self.resize_mode.currentText() != "no resize")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Img2App()
    window.show()
    sys.exit(app.exec())
