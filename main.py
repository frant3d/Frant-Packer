import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QMovie, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class GifBackground(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self.movie = QMovie(str(path))
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.frameChanged.connect(self.update)

        self.offset_y = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_background)
        self.timer.start(60)

        self.movie.start()

    def move_background(self):
        frame = self.movie.currentPixmap()

        if frame.isNull():
            return

        height = frame.height()

        if height <= 0:
            return

        self.offset_y += 1

        if self.offset_y >= height:
            self.offset_y = 0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        frame = self.movie.currentPixmap()

        if frame.isNull():
            painter.fillRect(
                self.rect(),
                QColor("#0a1013")
            )
            return

        width = frame.width()
        height = frame.height()

        if width <= 0 or height <= 0:
            return

        for x in range(
            -width,
            self.width() + width,
            width
        ):
            for y in range(
                -height + self.offset_y,
                self.height() + height,
                height
            ):
                painter.drawPixmap(
                    x,
                    y,
                    frame
                )

        painter.fillRect(
            self.rect(),
            QColor(5, 11, 14, 165)
        )


class ToolTab(QWidget):
    MAX_SIZE = 1024 ** 3

    def __init__(
        self,
        program_path,
        tool_name,
        number,
        parent=None
    ):
        super().__init__(parent)

        self.program_path = Path(program_path)
        self.tool_name = tool_name
        self.number = number

        self.target = None
        self.export_target = None

        self.process = QProcess(self)

        self.build_ui()
        self.setup_process()

        self.log(
            f"{self.tool_name} system initializing..."
        )

        self.start_process()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(16)

        # =====================================================
        # HEADER
        # =====================================================

        header = QHBoxLayout()

        branding = QVBoxLayout()
        branding.setSpacing(2)

        title = QLabel(self.tool_name)
        title.setObjectName("title")

        subtitle = QLabel(
            f"{self.tool_name} INTERFACE"
        )
        subtitle.setObjectName("subtitle")

        branding.addWidget(title)
        branding.addWidget(subtitle)

        header.addLayout(branding)
        header.addStretch()

        self.status = QLabel("● OFFLINE")
        self.status.setObjectName("status")

        header.addWidget(self.status)

        layout.addLayout(header)

        # =====================================================
        # DIVIDER
        # =====================================================

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)

        layout.addWidget(divider)

        # =====================================================
        # CONTENT
        # =====================================================

        content = QHBoxLayout()
        content.setSpacing(16)

        # =====================================================
        # TARGET PANEL
        # =====================================================

        target_panel = QFrame()
        target_panel.setObjectName("panel")
        target_panel.setFixedWidth(290)

        target_layout = QVBoxLayout(target_panel)

        target_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        target_layout.setSpacing(14)

        target_header = QHBoxLayout()

        target_title = QLabel("TARGET")
        target_title.setObjectName("heading")

        target_number = QLabel(self.number)
        target_number.setObjectName("number")

        target_header.addWidget(target_title)
        target_header.addStretch()
        target_header.addWidget(target_number)

        target_layout.addLayout(target_header)

        description = QLabel(
            "Select the executable that will "
            f"be passed to the {self.tool_name.lower()}."
        )

        description.setObjectName("description")
        description.setWordWrap(True)

        target_layout.addWidget(description)

        target_layout.addSpacing(8)

        self.target_label = QLabel("NO TARGET")
        self.target_label.setObjectName("target")
        self.target_label.setWordWrap(True)

        self.target_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        target_layout.addWidget(self.target_label)

        select_button = QPushButton(
            "SELECT EXECUTABLE"
        )

        select_button.setObjectName("select")
        select_button.clicked.connect(
            self.select_exe
        )

        target_layout.addWidget(select_button)

        # =====================================================
        # EXPORT
        # =====================================================

        export_title = QLabel("EXPORT")
        export_title.setObjectName("heading")

        target_layout.addWidget(export_title)

        self.export_label = QLabel(
            "NO EXPORT LOCATION"
        )

        self.export_label.setObjectName("target")
        self.export_label.setWordWrap(True)

        self.export_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        target_layout.addWidget(
            self.export_label
        )

        export_button = QPushButton(
            "SELECT EXPORT LOCATION"
        )

        export_button.setObjectName("select")
        export_button.clicked.connect(
            self.select_export
        )

        target_layout.addWidget(
            export_button
        )

        # =====================================================
        # SIZE
        # =====================================================

        if self.tool_name == "PACKER":
            size_title = QLabel("SIZE")
            size_title.setObjectName("heading")

            target_layout.addWidget(size_title)

            size_row = QHBoxLayout()
            size_row.setSpacing(8)

            self.size_input = QSpinBox()
            self.size_input.setObjectName("size_input")
            self.size_input.setMinimum(1)

            self.size_unit = QComboBox()
            self.size_unit.setObjectName("size_unit")

            self.size_unit.addItems([
                "B",
                "KB",
                "MB",
                "GB",
            ])

            self.size_unit.setCurrentText("KB")

            size_row.addWidget(
                self.size_input,
                1
            )

            size_row.addWidget(
                self.size_unit
            )

            target_layout.addLayout(size_row)

            self.size_value = QLabel(
                "1,024 bytes"
            )

            self.size_value.setObjectName(
                "size_value"
            )

            target_layout.addWidget(
                self.size_value
            )

            self.size_input.valueChanged.connect(
                self.update_size
            )

            self.size_unit.currentTextChanged.connect(
                self.update_size
            )

            self.update_size()

        target_layout.addStretch()

        self.target_state = QLabel(
            "INPUT // WAITING"
        )

        self.target_state.setObjectName(
            "small_status"
        )

        target_layout.addWidget(
            self.target_state
        )

        content.addWidget(target_panel)

        # =====================================================
        # TERMINAL
        # =====================================================

        terminal_panel = QFrame()
        terminal_panel.setObjectName("panel")

        terminal_layout = QVBoxLayout(
            terminal_panel
        )

        terminal_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        terminal_layout.setSpacing(12)

        terminal_header = QHBoxLayout()

        terminal_title = QLabel("TERMINAL")
        terminal_title.setObjectName("heading")

        terminal_id = QLabel(
            f"LOCAL // {self.tool_name}"
        )

        terminal_id.setObjectName(
            "terminal_id"
        )

        terminal_header.addWidget(
            terminal_title
        )

        terminal_header.addStretch()

        terminal_header.addWidget(
            terminal_id
        )

        terminal_layout.addLayout(
            terminal_header
        )

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)

        self.console.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )

        terminal_layout.addWidget(
            self.console
        )

        content.addWidget(
            terminal_panel,
            1
        )

        layout.addLayout(
            content,
            1
        )

        # =====================================================
        # CONTROLS
        # =====================================================

        controls = QHBoxLayout()
        controls.setSpacing(9)

        self.connection_label = QLabel(
            f"{self.tool_name} // DISCONNECTED"
        )

        self.connection_label.setObjectName(
            "connection"
        )

        controls.addWidget(
            self.connection_label
        )

        controls.addStretch()

        clear_button = QPushButton("CLEAR")
        clear_button.setObjectName("secondary")

        clear_button.clicked.connect(
            self.clear_console
        )

        self.start_button = QPushButton(
            "START BUILD"
        )

        self.start_button.setObjectName("start")

        self.start_button.clicked.connect(
            self.start_target
        )

        self.stop_button = QPushButton("STOP")
        self.stop_button.setObjectName("stop")

        self.stop_button.clicked.connect(
            self.stop_target
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        controls.addWidget(clear_button)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)

        layout.addLayout(controls)

    # =========================================================
    # SIZE
    # =========================================================

    def update_size(self):
        if self.tool_name != "PACKER":
            return

        value = self.size_input.value()
        unit = self.size_unit.currentText()

        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
        }

        multiplier = multipliers[unit]
        maximum_value = self.MAX_SIZE // multiplier

        self.size_input.blockSignals(True)
        self.size_input.setMaximum(maximum_value)
        self.size_input.blockSignals(False)

        size = value * multiplier

        if size > self.MAX_SIZE:
            size = self.MAX_SIZE

        self.size_value.setText(
            f"{size:,} bytes"
        )

    def get_size_bytes(self):
        value = self.size_input.value()
        unit = self.size_unit.currentText()

        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
        }

        size = value * multipliers[unit]

        return min(
            size,
            self.MAX_SIZE
        )

    # =========================================================
    # PROCESS
    # =========================================================

    def setup_process(self):
        self.process.started.connect(
            self.process_started
        )

        self.process.finished.connect(
            self.process_finished
        )

        self.process.errorOccurred.connect(
            self.process_error
        )

        self.process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.process.readyReadStandardError.connect(
            self.read_error
        )

    def start_process(self):
        if not self.program_path.is_file():
            self.log("[ERR] Program not found:")
            self.log(str(self.program_path))
            return

        self.process.setProgram(
            str(self.program_path)
        )

        self.process.setWorkingDirectory(
            str(self.program_path.parent)
        )

        self.log(
            f"> Launching "
            f"{self.tool_name.lower()}: "
            f"{self.program_path}"
        )

        self.process.start()

    def process_started(self):
        self.status.setText("● ONLINE")

        self.status.setStyleSheet(
            "color: #82aaa4;"
        )

        self.connection_label.setText(
            f"{self.tool_name} // CONNECTED"
        )

        self.log(
            f"> {self.tool_name} online."
        )

        self.update_buttons()

    def process_finished(
        self,
        exit_code,
        exit_status
    ):
        self.status.setText("● OFFLINE")

        self.status.setStyleSheet(
            "color: #63777d;"
        )

        self.connection_label.setText(
            f"{self.tool_name} // DISCONNECTED"
        )

        self.log(
            f"> {self.tool_name} exited "
            f"with code {exit_code}."
        )

        self.update_buttons()

    def process_error(self, error):
        self.status.setText("● ERROR")

        self.status.setStyleSheet(
            "color: #a77b82;"
        )

        self.connection_label.setText(
            f"{self.tool_name} // ERROR"
        )

        self.log(
            f"[ERR] {self.process.errorString()}"
        )

        self.update_buttons()

    # =========================================================
    # TARGET
    # =========================================================

    def select_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Executable",
            str(Path.home()),
            "Executable (*.exe)"
        )

        if not path:
            return

        self.target = Path(path)

        self.target_label.setText(
            str(self.target)
        )

        self.target_state.setText(
            "INPUT // SELECTED"
        )

        self.log(
            f"> Target selected: {self.target}"
        )

        if self.send(
            f"exe {self.target}"
        ):
            self.log(
                f"> Target sent to "
                f"{self.tool_name.lower()}."
            )

        self.update_buttons()

    # =========================================================
    # EXPORT
    # =========================================================

    def select_export(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Export Location",
            str(Path.home())
        )

        if not path:
            return

        self.export_target = Path(path)

        self.export_label.setText(
            str(self.export_target)
        )

        self.log(
            f"> Export location selected: "
            f"{self.export_target}"
        )

        if self.process_running():
            if self.send(
                f"export {self.export_target}"
            ):
                self.log(
                    f"> Export location sent to "
                    f"{self.tool_name.lower()}."
                )

    # =========================================================
    # BUILD
    # =========================================================

    def start_target(self):
        if self.target is None:
            self.log(
                "[ERR] No target selected."
            )
            return

        if not self.process_running():
            self.log(
                f"[ERR] {self.tool_name} is offline."
            )
            return

        if self.export_target is not None:
            if not self.send(
                f"export {self.export_target}"
            ):
                return

            self.log(
                f"> Export location sent: "
                f"{self.export_target}"
            )

        if self.tool_name == "PACKER":
            size = self.get_size_bytes()

            self.log(
                f"> Selected size: "
                f"{size:,} bytes."
            )

            if not self.send(
                f"size {size}"
            ):
                return

        self.log(
            "> Sending START..."
        )

        if self.send("start"):
            self.start_button.setEnabled(False)

    def stop_target(self):
        if not self.process_running():
            self.log(
                f"[ERR] {self.tool_name} is offline."
            )
            return

        self.log(
            "> Sending STOP..."
        )

        self.send("stop")

    def send(self, command):
        if not self.process_running():
            self.log(
                f"[ERR] {self.tool_name} "
                "is not running."
            )
            return False

        data = (
            command + "\n"
        ).encode("utf-8")

        self.process.write(data)

        if not self.process.waitForBytesWritten(
            500
        ):
            self.log(
                "[ERR] Failed to send command."
            )
            return False

        return True

    # =========================================================
    # OUTPUT
    # =========================================================

    def read_output(self):
        data = bytes(
            self.process.readAllStandardOutput()
        )

        text = data.decode(
            "utf-8",
            errors="replace"
        ).rstrip()

        if text:
            self.log(text)

    def read_error(self):
        data = bytes(
            self.process.readAllStandardError()
        )

        text = data.decode(
            "utf-8",
            errors="replace"
        ).rstrip()

        if text:
            self.log(
                f"[{self.tool_name}] {text}"
            )

    def log(self, text):
        self.console.appendPlainText(text)

        scrollbar = (
            self.console.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    def clear_console(self):
        self.console.clear()

    # =========================================================
    # STATE
    # =========================================================

    def process_running(self):
        return (
            self.process.state()
            == QProcess.Running
        )

    def update_buttons(self):
        running = self.process_running()

        ready = (
            running
            and self.target is not None
        )

        self.start_button.setEnabled(
            ready
        )

        self.stop_button.setEnabled(
            ready
        )

    # =========================================================
    # CLOSE
    # =========================================================

    def close_process(self):
        if not self.process_running():
            return

        self.process.write(
            b"exit\n"
        )

        self.process.waitForBytesWritten(
            500
        )

        if not self.process.waitForFinished(
            1000
        ):
            self.process.kill()


class OPacker(QMainWindow):
    PACKER = (
        Path(__file__).parent
        / "src"
        / "packer.exe"
    )

    BACKGROUND = (
        Path(__file__).parent
        / "bckg.gif"
    )

    def __init__(self):
        super().__init__()

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):
        self.setWindowTitle("Frant-Packer")

        self.resize(
            950,
            620
        )

        self.setMinimumSize(
            780,
            520
        )

        root = QWidget()

        self.setCentralWidget(root)

        # =====================================================
        # BACKGROUND
        # =====================================================

        self.background = None

        if self.BACKGROUND.is_file():
            self.background = GifBackground(
                self.BACKGROUND,
                root
            )

            self.background.setGeometry(
                root.rect()
            )

            self.background.lower()

        # =====================================================
        # ROOT LAYOUT
        # =====================================================

        layout = QVBoxLayout(root)

        layout.setContentsMargins(
            36,
            28,
            36,
            28
        )

        layout.setSpacing(16)

        # =====================================================
        # HEADER
        # =====================================================

        header = QHBoxLayout()

        branding = QVBoxLayout()
        branding.setSpacing(2)

        title = QLabel("O-Packer")
        title.setObjectName("global_title")

        subtitle = QLabel(
            "EXECUTABLE BUILD INTERFACE"
        )

        subtitle.setObjectName(
            "global_subtitle"
        )

        branding.addWidget(title)
        branding.addWidget(subtitle)

        header.addLayout(branding)
        header.addStretch()

        credit = QLabel("Frant3d on GitHub")
        credit.setObjectName("global_credit")

        header.addWidget(credit)

        layout.addLayout(header)

        # =====================================================
        # DIVIDER
        # =====================================================

        divider = QFrame()
        divider.setObjectName(
            "global_divider"
        )

        divider.setFixedHeight(1)

        layout.addWidget(divider)

        # =====================================================
        # TABS
        # =====================================================

        self.tabs = QTabWidget()

        self.tabs.setDocumentMode(True)
        self.tabs.setObjectName("tools")

        self.packer_tab = ToolTab(
            self.PACKER,
            "PACKER",
            "01",
            self
        )

        self.tabs.addTab(
            self.packer_tab,
            "PACKER"
        )

        layout.addWidget(
            self.tabs,
            1
        )

        # =====================================================
        # STYLE
        # =====================================================

        self.setStyleSheet("""
            QWidget {
                background: transparent;
                color: #b1bdc2;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel {
                background: transparent;
            }

            QLabel#global_title {
                color: #bdc9cd;
                font-size: 32px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#global_subtitle {
                color: #52676e;
                font-family: Consolas;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#global_credit {
                color: #50666d;
                font-family: Consolas;
                font-size: 10px;
            }

            QFrame#global_divider {
                background: #294047;
                border: none;
            }

            /* TABS */

            QTabWidget::pane {
                border: none;
                background: transparent;
            }

            QTabBar {
                background: transparent;
            }

            QTabBar::tab {
                background: rgba(8, 17, 21, 220);
                color: #536970;
                border: 1px solid #253c43;
                border-bottom: none;
                padding: 10px 24px;
                margin-right: 5px;
                font-family: Consolas;
                font-size: 10px;
                font-weight: 700;
            }

            QTabBar::tab:hover {
                background: rgba(15, 29, 34, 235);
                color: #81959b;
            }

            QTabBar::tab:selected {
                background: rgba(15, 29, 34, 245);
                color: #9eb1b6;
                border-color: #36535b;
            }

            /* TOOL HEADER */

            QLabel#title {
                color: #bdc9cd;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#subtitle {
                color: #52676e;
                font-family: Consolas;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#status {
                background: rgba(10, 19, 23, 225);
                color: #63777d;
                border: 1px solid #294047;
                border-radius: 10px;
                padding: 8px 14px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: 700;
            }

            QFrame#divider {
                background: #294047;
                border: none;
            }

            /* PANELS */

            QFrame#panel {
                background: rgba(9, 18, 22, 215);
                border: 1px solid #2a4148;
                border-radius: 18px;
            }

            QLabel#heading {
                color: #7b9097;
                font-family: Consolas;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#number {
                color: #385159;
                font-family: Consolas;
                font-size: 10px;
                font-weight: 700;
            }

            QLabel#description {
                color: #60757c;
                font-family: Consolas;
                font-size: 11px;
            }

            QLabel#target {
                background: rgba(6, 13, 16, 225);
                border: 1px solid #29434b;
                border-radius: 12px;
                color: #91a3a9;
                padding: 13px;
                font-family: Consolas;
                font-size: 11px;
            }

            QLabel#small_status {
                color: #496168;
                font-family: Consolas;
                font-size: 9px;
            }

            QLabel#terminal_id {
                color: #496168;
                font-family: Consolas;
                font-size: 9px;
            }

            QLabel#connection {
                color: #536b72;
                font-family: Consolas;
                font-size: 10px;
            }

            QLabel#size_value {
                color: #496168;
                font-family: Consolas;
                font-size: 9px;
            }

            /* SIZE */

            QSpinBox#size_input {
                background: rgba(6, 13, 16, 225);
                border: 1px solid #29434b;
                border-radius: 12px;
                color: #91a3a9;
                padding: 10px 13px;
                font-family: Consolas;
                font-size: 11px;
            }

            QSpinBox#size_input:focus {
                border-color: #466b74;
            }

            QComboBox#size_unit {
                background: rgba(6, 13, 16, 225);
                border: 1px solid #29434b;
                border-radius: 12px;
                color: #91a3a9;
                padding: 10px 12px;
                font-family: Consolas;
                font-size: 11px;
            }

            QComboBox#size_unit:hover {
                border-color: #466b74;
            }

            QComboBox#size_unit::drop-down {
                border: none;
                width: 24px;
            }

            QComboBox#size_unit QAbstractItemView {
                background: #0a1519;
                color: #91a3a9;
                border: 1px solid #29434b;
                selection-background-color: #24444c;
                selection-color: #c2d0d4;
            }

            /* TERMINAL */

            QPlainTextEdit {
                background: rgba(5, 11, 14, 232);
                border: 1px solid #294149;
                border-radius: 14px;
                color: #92a5aa;
                selection-background-color: #24444c;
                selection-color: #c2d0d4;
                padding: 13px;
                font-family: Consolas;
                font-size: 11px;
            }

            /* BUTTONS */

            QPushButton {
                background: rgba(11, 22, 27, 240);
                color: #82959b;
                border: 1px solid #2a454d;
                border-radius: 11px;
                padding: 10px 17px;
                font-family: Consolas;
                font-size: 10px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: rgba(18, 34, 40, 245);
                border-color: #3b5c65;
                color: #a9b9bd;
            }

            QPushButton:pressed {
                background: #071014;
            }

            QPushButton:disabled {
                background: rgba(7, 14, 17, 225);
                color: #3a4b50;
                border-color: #1d3036;
            }

            QPushButton#select {
                background: rgba(15, 32, 38, 245);
                color: #82a1a8;
                border-color: #31515a;
            }

            QPushButton#select:hover {
                background: rgba(21, 43, 50, 250);
                color: #a7c0c5;
                border-color: #466b74;
            }

            QPushButton#start {
                background: rgba(18, 40, 39, 245);
                color: #82aaa4;
                border-color: #38615c;
            }

            QPushButton#start:hover {
                background: rgba(25, 52, 50, 250);
                color: #a1c2bc;
                border-color: #4b7770;
            }

            QPushButton#stop {
                background: rgba(34, 19, 23, 245);
                color: #a77b82;
                border-color: #55343c;
            }

            QPushButton#stop:hover {
                background: rgba(47, 25, 31, 250);
                color: #c09299;
                border-color: #704751;
            }

            QPushButton#secondary {
                background: transparent;
                color: #536a71;
                border-color: #294047;
            }

            QPushButton#secondary:hover {
                background: rgba(10, 21, 25, 230);
                color: #82979e;
            }
        """)

    # =========================================================
    # RESIZE
    # =========================================================

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.background:
            self.background.setGeometry(
                self.centralWidget().rect()
            )

    # =========================================================
    # CLOSE
    # =========================================================

    def closeEvent(self, event):
        self.packer_tab.close_process()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setFont(
        QFont(
            "Segoe UI",
            10
        )
    )

    window = OPacker()
    window.show()

    sys.exit(app.exec())