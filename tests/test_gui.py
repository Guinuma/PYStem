import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

HAS_GUI = importlib.util.find_spec("PySide6") is not None and importlib.util.find_spec("psutil") is not None
if HAS_GUI:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings, QTimer, QUrl
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtMultimedia import QMediaPlayer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from src.backends import Options
    from src.benchmark import synthetic
    from src.gui import MainWindow
    from src.gui_worker import Cancelled, SeparationWorker

    class FakeWorker(SeparationWorker):
        def run(self):
            for _ in range(5):
                if self.stop_event.wait(0.02):
                    self.cancelled.emit()
                    return
                self.log.emit("Processing audio chunks")
            output = Path(self.output) / self.options.model / Path(self.audio).stem
            output.mkdir(parents=True)
            for stem in ("vocals", "bass", "drums", "other"):
                synthetic(output / f"{stem}.wav", seconds=1)
            self.succeeded.emit(str(output))


@unittest.skipUnless(HAS_GUI, "Install requirements-gui.txt for desktop tests")
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if sys.platform == "win32":
            for name in ("segoeui.ttf", "segoeuib.ttf"):
                QFontDatabase.addApplicationFont(f"C:/Windows/Fonts/{name}")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        settings = QSettings(str(self.root / "settings.ini"), QSettings.IniFormat)
        self.window = MainWindow(settings=settings, worker_class=FakeWorker)
        self.window.output_edit.setText(str(self.root / "output"))
        self.audio = self.root / "test audio.wav"
        synthetic(self.audio, seconds=1)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window.worker:
            self.window.worker.cancel()
            self.window.worker.wait(5000)
            self.app.processEvents()
        self.window.player.setSource(QUrl())
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def until(self, condition, seconds=5):
        deadline = time.monotonic() + seconds
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(20)
        self.assertTrue(condition(), "Desktop operation did not finish")

    def test_import_enables_separation_and_rejects_missing_file(self):
        self.assertFalse(self.window.start_button.isEnabled())
        self.window.load_audio(self.root / "missing.wav")
        self.assertFalse(self.window.start_button.isEnabled())
        self.window.load_audio(self.audio)
        self.assertTrue(self.window.start_button.isEnabled())
        self.assertEqual(self.window.tracks.count(), 1)
        self.assertEqual(self.window.audio_path, self.audio)

    def test_missing_optional_model_does_not_start_or_download(self):
        self.window.load_audio(self.audio)
        self.window.model_combo.setCurrentIndex(3)
        self.window.model_fields["checkpoint"].setText(str(self.root / "missing.ckpt"))
        self.window.start_separation()
        self.assertIsNone(self.window.worker)
        self.assertIn("Faltam ficheiros", self.window.status.text())
        self.assertTrue(self.window.advanced.isVisible())

    def test_async_job_keeps_event_loop_responsive_and_loads_results(self):
        ticks = []
        timer = QTimer()
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start(10)
        self.window.load_audio(self.audio)
        self.window.start_separation()
        self.assertFalse(self.window.start_button.isEnabled())
        self.until(lambda: self.window.worker is None)
        timer.stop()
        self.assertGreater(len(ticks), 2)
        self.assertIn("Pistas prontas", self.window.status.text())
        self.assertEqual(self.window.tracks.count(), 5)
        self.assertTrue(self.window.open_folder.isEnabled())
        self.assertTrue(self.window.start_button.isEnabled())

    def test_cancellation_restores_controls(self):
        self.window.load_audio(self.audio)
        self.window.start_separation()
        self.window.cancel_separation()
        self.until(lambda: self.window.worker is None)
        self.assertIn("cancelada", self.window.status.text())
        self.assertTrue(self.window.start_button.isEnabled())
        self.assertFalse(self.window.cancel_button.isEnabled())

    def test_library_does_not_attach_unrelated_original(self):
        self.window.load_audio(self.audio)
        folder = self.root / "different song"
        folder.mkdir()
        synthetic(folder / "vocals.wav", seconds=1)
        self.window.load_results(folder)
        self.assertEqual(self.window.tracks.count(), 1)
        self.assertEqual(self.window.tracks.item(0).text(), "Voz")

    def test_muted_playback_pause_seek_and_stop(self):
        self.window.load_audio(self.audio)
        self.window.audio_output.setMuted(True)
        self.until(lambda: self.window.player.duration() == 1000)
        self.window.toggle_playback()
        self.until(lambda: self.window.player.position() > 0)
        self.window.toggle_playback()
        self.assertEqual(self.window.player.playbackState(), QMediaPlayer.PausedState)
        self.window.seek.setValue(500)
        self.window.seek.sliderReleased.emit()
        self.until(lambda: self.window.player.position() == 500)
        self.window.stop.click()
        self.assertEqual(self.window.player.playbackState(), QMediaPlayer.StoppedState)

    def test_failed_job_restores_controls_and_shows_details(self):
        class FailingWorker(SeparationWorker):
            def run(self):
                self.failed.emit("Test engine failure")

        self.window.worker_class = FailingWorker
        self.window.load_audio(self.audio)
        self.window.start_separation()
        self.until(lambda: self.window.worker is None)
        self.assertTrue(self.window.start_button.isEnabled())
        self.assertIn("Não foi possível", self.window.status.text())
        self.assertIn("Test engine failure", self.window.logs.toPlainText())

    def test_worker_cancels_running_process_and_descendant(self):
        import psutil
        worker = SeparationWorker(str(self.audio), str(self.root), Options())
        marker = self.root / "child.pid"
        code = ("import subprocess,sys,time,pathlib; "
                "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
                f"pathlib.Path({str(marker)!r}).write_text(str(child.pid)); "
                "time.sleep(60)")
        errors = []
        import threading

        def launch():
            try:
                worker.run_command([sys.executable, "-c", code], check=True, env=os.environ.copy(), timeout=10)
            except Cancelled:
                errors.append("cancelled")

        thread = threading.Thread(target=launch)
        thread.start()
        self.until(marker.exists)
        child_pid = int(marker.read_text())
        worker.cancel()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["cancelled"])
        self.assertFalse(psutil.pid_exists(child_pid))


if __name__ == "__main__":
    unittest.main()
