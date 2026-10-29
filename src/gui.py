"""PYStem desktop: local separation and individual track preview."""
from pathlib import Path
import re
import sys

from PySide6.QtCore import QElapsedTimer, QSettings, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFormLayout, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QPlainTextEdit, QProgressBar, QPushButton,
                               QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget)

try:
    from .backends import MODELS, Options
    from .gui_worker import SeparationWorker
except ImportError:
    from backends import MODELS, Options
    from gui_worker import SeparationWorker

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".aiff", ".aif", ".opus"}
DESCRIPTIONS = {
    "htdemucs": "Voz, bateria, baixo e outros · a opção mais rápida nos nossos testes CPU.",
    "htdemucs_ft": "Quatro pistas · modelos especializados por instrumento. Mais demorado.",
    "htdemucs_6s": "Seis pistas · acrescenta guitarra e piano à separação.",
    "mdx23c": "Voz e instrumental · modelo opcional, mais lento em CPU.",
    "bs_roformer": "Voz e instrumental · modelo opcional, mais lento em CPU.",
}
TRACK_NAMES = {"vocals": "Voz", "drums": "Bateria", "bass": "Baixo", "other": "Outros",
               "instrumental": "Instrumental", "guitar": "Guitarra", "piano": "Piano"}


def label(text, name=None):
    result = QLabel(text)
    if name:
        result.setObjectName(name)
    result.setWordWrap(True)
    return result


def card(title):
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(10)
    layout.addWidget(label(title, "section"))
    return frame, layout


def time_text(milliseconds):
    seconds = max(0, milliseconds // 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"


class AudioDrop(QFrame):
    selected = Signal(str)
    browse = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Importar ficheiro de áudio")
        self.setMinimumHeight(128)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        self.title = label("Arrasta uma música para aqui", "dropTitle")
        self.detail = label("ou clica para escolher um ficheiro", "muted")
        layout.addWidget(label("↑   IMPORTAR ÁUDIO", "eyebrow"))
        layout.addWidget(self.title)
        layout.addWidget(self.detail)
        layout.addWidget(label("WAV · FLAC · MP3 · M4A · OGG", "muted"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.browse.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            if Path(urls[0].toLocalFile()).suffix.lower() in EXTENSIONS:
                event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.browse.emit()
        else:
            super().keyPressEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            self.selected.emit(urls[0].toLocalFile())
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self, *, settings=None, worker_class=SeparationWorker):
        super().__init__()
        self.settings = settings if settings is not None else QSettings("PYStem", "Desktop")
        self.worker_class = worker_class
        self.worker = None
        self.audio_path = None
        self.result_path = None
        self.close_when_finished = False
        self.setWindowTitle("PYStem — Separação de áudio")
        self.resize(1220, 840)
        self.setMinimumSize(940, 700)
        stylesheet = Path(__file__).with_name("gui.qss").read_text(encoding="utf-8")
        self.setStyleSheet(stylesheet.replace("@ASSETS@", Path(__file__).with_name("assets").as_posix()))
        self.import_shortcut = QShortcut(QKeySequence.Open, self)
        self.import_shortcut.activated.connect(self.browse_audio)
        container = QWidget()
        shell = QHBoxLayout(container)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        self.setCentralWidget(container)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(22, 30, 18, 24)
        side.setSpacing(16)
        side.addWidget(label("PYStem", "brand"))
        side.addWidget(label("O teu estúdio de pistas.", "muted"))
        side.addSpacing(30)
        nav = QPushButton("Separar áudio")
        nav.setObjectName("nav")
        nav.clicked.connect(lambda: self.drop.setFocus())
        side.addWidget(nav)
        self.library = QPushButton("Abrir pistas…")
        self.library.setObjectName("subtle")
        self.library.clicked.connect(self.browse_results)
        side.addWidget(self.library)
        side.addStretch()
        side.addWidget(label("NO TEU COMPUTADOR", "eyebrow"))
        side.addWidget(label("O áudio fica contigo.\nSem envios para a cloud.", "muted"))
        shell.addWidget(sidebar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 20)
        layout.setSpacing(16)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("SEPARAÇÃO DE ÁUDIO", "eyebrow"))
        titles.addWidget(label("Da música às suas partes.", "heading"))
        titles.addWidget(label("Separa, ouve e encontra os detalhes de cada pista.", "muted"))
        header.addLayout(titles, 1)
        header.addWidget(label("●  Local · CPU", "badge"), 0, Qt.AlignTop)
        layout.addLayout(header)
        columns = QHBoxLayout()
        columns.setSpacing(20)
        left = QVBoxLayout()
        left.setSpacing(14)
        source_card, source_layout = card("01   A tua música")
        self.drop = AudioDrop()
        self.drop.selected.connect(self.load_audio)
        self.drop.browse.connect(self.browse_audio)
        source_layout.addWidget(self.drop)
        self.file_info = label("Escolhe um ficheiro para começar.", "muted")
        source_layout.addWidget(self.file_info)
        left.addWidget(source_card)
        model_card, model_layout = card("02   Escolhe a separação")
        self.model_combo = QComboBox()
        for key, spec in MODELS.items():
            self.model_combo.addItem(spec.label.split(" (")[0], key)
        model_layout.addWidget(self.model_combo)
        self.model_description = label("", "muted")
        model_layout.addWidget(self.model_description)
        self.advanced_toggle = QPushButton("Definições do modelo ▾")
        self.advanced_toggle.setObjectName("subtle")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.toggled.connect(lambda shown: self.advanced.setVisible(shown))
        model_layout.addWidget(self.advanced_toggle)
        self.advanced = QWidget()
        self.advanced.setObjectName("transparent")
        form = QFormLayout(self.advanced)
        form.setContentsMargins(0, 0, 0, 0)
        self.threads = QSpinBox()
        self.threads.setRange(1, 32)
        self.threads.setValue(int(self.settings.value("threads", 4)))
        form.addRow("Threads CPU", self.threads)
        self.model_fields = {}
        self.optional_rows = []
        for key, title in (("msst_dir", "Pasta MSST"), ("python", "Python do modelo"),
                           ("config", "Configuração YAML"), ("checkpoint", "Checkpoint")):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            field = QLineEdit()
            field.setAccessibleName(title)
            button = QPushButton("…")
            button.setFixedWidth(36)
            button.clicked.connect(lambda checked=False, k=key: self.browse_model_file(k))
            row_layout.addWidget(field, 1)
            row_layout.addWidget(button)
            title_widget = label(title)
            form.addRow(title_widget, row)
            self.model_fields[key] = field
            self.optional_rows.append((title_widget, row))
        model_layout.addWidget(self.advanced)
        self.advanced.hide()
        left.addWidget(model_card)
        export_card, export_layout = card("03   Guarda as pistas")
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit(str(self.settings.value("output", str(ROOT / "output"))))
        self.output_edit.setAccessibleName("Pasta de saída")
        self.output_browse = QPushButton("Escolher…")
        self.output_browse.clicked.connect(self.browse_output)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_browse)
        export_layout.addLayout(output_row)
        export_layout.addWidget(label("Cada música fica numa pasta com as suas pistas WAV.", "muted"))
        left.addWidget(export_card)
        columns.addLayout(left, 3)
        preview_card, preview = card("Ouvir as pistas")
        preview_card.setMinimumWidth(250)
        preview.addWidget(label("Seleciona uma pista para a ouvir individualmente.", "muted"))
        self.tracks = QListWidget()
        self.tracks.setMinimumHeight(180)
        self.tracks.currentItemChanged.connect(self.select_track)
        preview.addWidget(self.tracks, 1)
        self.preview_name = label("Ainda sem áudio", "section")
        preview.addWidget(self.preview_name)
        self.seek = QSlider(Qt.Horizontal)
        self.seek.setEnabled(False)
        self.seek.setAccessibleName("Posição da reprodução")
        self.seek.sliderReleased.connect(lambda: self.player.setPosition(self.seek.value()))
        preview.addWidget(self.seek)
        self.playback_time = label("00:00 / 00:00", "muted")
        preview.addWidget(self.playback_time)
        controls = QHBoxLayout()
        self.play = QPushButton("Reproduzir")
        self.play.clicked.connect(self.toggle_playback)
        self.play.setEnabled(False)
        self.stop = QPushButton("Parar")
        self.stop.clicked.connect(lambda: self.player.stop())
        self.stop.setEnabled(False)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.stop)
        preview.addLayout(controls)
        preview.addWidget(label("Volume", "muted"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(65)
        self.volume.setAccessibleName("Volume")
        preview.addWidget(self.volume)
        self.open_folder = QPushButton("Abrir pasta de resultados")
        self.open_folder.setEnabled(False)
        self.open_folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result_path))))
        preview.addWidget(self.open_folder)
        columns.addWidget(preview_card, 2)
        layout.addLayout(columns)
        action_row = QHBoxLayout()
        self.status = label("Pronto para importar áudio.", "muted")
        action_row.addWidget(self.status, 1)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_separation)
        action_row.addWidget(self.cancel_button)
        self.start_button = QPushButton("Separar áudio  →")
        self.start_button.setObjectName("primary")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_separation)
        action_row.addWidget(self.start_button)
        layout.addLayout(action_row)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.log_toggle = QPushButton("Mostrar detalhes ▾")
        self.log_toggle.setObjectName("subtle")
        self.log_toggle.setCheckable(True)
        self.log_toggle.toggled.connect(lambda shown: self.logs.setVisible(shown))
        layout.addWidget(self.log_toggle)
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMaximumBlockCount(800)
        self.logs.setMaximumHeight(150)
        self.logs.hide()
        layout.addWidget(self.logs)
        layout.addStretch()
        scroll.setWidget(content)
        shell.addWidget(scroll, 1)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.65)
        self.player.setAudioOutput(self.audio_output)
        self.volume.valueChanged.connect(lambda value: self.audio_output.setVolume(value / 100))
        self.player.durationChanged.connect(self.duration_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.playbackStateChanged.connect(lambda state: self.play.setText(
            "Pausa" if state == QMediaPlayer.PlayingState else "Reproduzir"))
        self.player.errorOccurred.connect(self.playback_error)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_elapsed)
        self.elapsed = QElapsedTimer()
        self.stage = ""
        self.model_combo.currentIndexChanged.connect(self.model_changed)
        self.model_changed()

    def model_changed(self):
        model = self.model_combo.currentData()
        self.model_description.setText(DESCRIPTIONS[model])
        optional = MODELS[model].engine == "msst"
        for title, row in self.optional_rows:
            title.setVisible(optional)
            row.setVisible(optional)
        defaults = {"msst_dir": ROOT / ".tools/msst", "python": ROOT / ".venv-models/Scripts/python.exe",
                    "config": ROOT / "models" / model / "config.yaml",
                    "checkpoint": ROOT / "models" / model / "model.ckpt"}
        for key, field in self.model_fields.items():
            field.setText(str(self.settings.value(f"{model}/{key}", str(defaults[key]))))

    def browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher áudio", "", "Áudio (*.wav *.flac *.mp3 *.ogg *.m4a *.aac *.aiff *.aif *.opus)")
        if path:
            self.load_audio(path)

    def load_audio(self, path):
        if self.worker and self.worker.isRunning():
            return
        file = Path(path)
        if not file.is_file() or file.suffix.lower() not in EXTENSIONS:
            self.status.setText("Escolhe um ficheiro de áudio existente e suportado.")
            return
        self.audio_path = file.resolve()
        self.result_path = None
        self.open_folder.setEnabled(False)
        self.drop.title.setText(file.name)
        self.drop.detail.setText("Clica para trocar de música")
        self.file_info.setText(f"{file.suffix[1:].upper()}  ·  {file.stat().st_size / 1024**2:.1f} MB")
        self.tracks.clear()
        self.add_track("Original", self.audio_path)
        self.tracks.setCurrentRow(0)
        self.start_button.setEnabled(True)
        self.status.setText("Áudio pronto. Escolhe o modelo e inicia a separação.")

    def add_track(self, name, path):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, str(path))
        item.setToolTip(str(path))
        self.tracks.addItem(item)

    def select_track(self, current, previous):
        self.player.stop()
        if current is None:
            self.player.setSource(QUrl())
            self.preview_name.setText("Ainda sem áudio")
        else:
            self.player.setSource(QUrl.fromLocalFile(current.data(Qt.UserRole)))
            self.preview_name.setText(current.text())
        self.play.setEnabled(current is not None)
        self.stop.setEnabled(current is not None)

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def duration_changed(self, duration):
        self.seek.setRange(0, max(0, duration))
        self.seek.setEnabled(duration > 0)
        self.position_changed(self.player.position())

    def position_changed(self, position):
        if not self.seek.isSliderDown():
            self.seek.setValue(position)
        self.playback_time.setText(f"{time_text(position)} / {time_text(self.player.duration())}")

    def playback_error(self, error, message):
        if error != QMediaPlayer.NoError:
            self.logs.appendPlainText(f"Reprodução: {message}")
            self.preview_name.setText("Não foi possível reproduzir esta pista")

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Guardar pistas em", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def browse_model_file(self, key):
        field = self.model_fields[key]
        if key == "msst_dir":
            path = QFileDialog.getExistingDirectory(self, "Pasta MSST", field.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Escolher ficheiro local", field.text())
        if path:
            field.setText(path)

    def browse_results(self):
        path = QFileDialog.getExistingDirectory(self, "Abrir pasta de pistas WAV", self.output_edit.text())
        if path:
            if not list(Path(path).glob("*.wav")):
                self.status.setText("Esta pasta não contém pistas WAV. Escolhe a pasta de uma música.")
                return
            self.load_results(path)

    def load_results(self, path, *, include_original=False):
        self.result_path = Path(path)
        self.tracks.clear()
        original = include_original and self.audio_path is not None
        if original:
            self.add_track("Original", self.audio_path)
        for file in sorted(self.result_path.glob("*.wav")):
            self.add_track(TRACK_NAMES.get(file.stem, file.stem), file)
        self.tracks.setCurrentRow(1 if original and self.tracks.count() > 1 else 0)
        self.open_folder.setEnabled(True)

    def set_busy(self, busy):
        for widget in (self.drop, self.model_combo, self.advanced, self.output_edit, self.output_browse, self.library):
            widget.setEnabled(not busy)
        self.tracks.setEnabled(not busy)
        self.play.setEnabled(not busy and self.tracks.count() > 0)
        self.stop.setEnabled(not busy and self.tracks.count() > 0)
        self.seek.setEnabled(not busy and self.player.duration() > 0)
        self.open_folder.setEnabled(not busy and self.result_path is not None)
        self.start_button.setEnabled(not busy and self.audio_path is not None)
        self.cancel_button.setEnabled(busy)
        self.progress.setVisible(busy)
        self.progress.setRange(0, 0 if busy else 100)

    def start_separation(self):
        if not self.audio_path or (self.worker and self.worker.isRunning()):
            return
        if not self.output_edit.text().strip():
            self.status.setText("Escolhe uma pasta para guardar as pistas.")
            return
        model = self.model_combo.currentData()
        kwargs = {"threads": self.threads.value()}
        if MODELS[model].engine == "msst":
            for key, field in self.model_fields.items():
                path = Path(field.text())
                valid = (path / "inference.py").is_file() if key == "msst_dir" else path.is_file()
                if not valid:
                    self.advanced_toggle.setChecked(True)
                    self.status.setText("Faltam ficheiros locais do modelo. Verifica as definições; não serão descarregados automaticamente.")
                    return
                kwargs[key] = str(path.resolve())
                self.settings.setValue(f"{model}/{key}", field.text())
        self.settings.setValue("output", self.output_edit.text())
        self.settings.setValue("threads", self.threads.value())
        self.player.stop()
        self.player.setSource(QUrl())
        self.logs.clear()
        self.set_busy(True)
        self.stage = "A carregar o modelo"
        self.elapsed.start()
        self.timer.start()
        self.update_elapsed()
        self.worker = self.worker_class(str(self.audio_path), self.output_edit.text(), Options(model=model, **kwargs), self)
        self.worker.log.connect(self.receive_log)
        self.worker.succeeded.connect(self.separation_succeeded)
        self.worker.failed.connect(self.separation_failed)
        self.worker.cancelled.connect(lambda: self.status.setText("Separação cancelada. Podes voltar a tentar."))
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def receive_log(self, text):
        text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
        self.logs.appendPlainText(text)
        if any(token in text for token in ("Separating track", "Processing audio chunks", "Total files found")):
            self.stage = "A separar as pistas"
        self.update_elapsed()

    def update_elapsed(self):
        self.status.setText(f"{self.stage} · {time_text(self.elapsed.elapsed())}")

    def separation_succeeded(self, path):
        self.timer.stop()
        self.load_results(path, include_original=True)
        self.status.setText(f"Pistas prontas · {time_text(self.elapsed.elapsed())}. Seleciona uma pista para ouvir.")

    def separation_failed(self, message):
        self.timer.stop()
        self.logs.appendPlainText(message)
        self.log_toggle.setChecked(True)
        self.status.setText("Não foi possível concluir. Consulta os detalhes e verifica os ficheiros locais do modelo.")

    def cancel_separation(self):
        if self.worker and self.worker.isRunning():
            self.timer.stop()
            self.stage = "A cancelar"
            self.status.setText("A cancelar e a limpar os ficheiros temporários…")
            self.cancel_button.setEnabled(False)
            self.worker.cancel()

    def worker_finished(self):
        self.timer.stop()
        self.set_busy(False)
        if self.player.source().isEmpty() and self.tracks.currentItem():
            self.select_track(self.tracks.currentItem(), None)
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        if self.close_when_finished:
            self.close()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.close_when_finished = True
            self.cancel_separation()
            event.ignore()
            return
        self.player.stop()
        self.settings.setValue("output", self.output_edit.text())
        self.settings.setValue("threads", self.threads.value())
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PYStem")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
