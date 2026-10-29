"""Opt-in real HTDemucs desktop smoke test and screenshots (cached weights only)."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QApplication
from src.benchmark import audio_info, synthetic, verify_stems
from src.gui import MainWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--cancel-after", type=int, default=0, metavar="MS",
                        help="Test real cancellation after this many milliseconds")
    args = parser.parse_args()
    folder = Path(args.report_dir).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    audio = folder / "teste-estereo.wav"
    synthetic(audio)
    app = QApplication([])
    if sys.platform == "win32":
        # Qt's offscreen plugin does not enumerate Windows fonts automatically.
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "consola.ttf"):
            QFontDatabase.addApplicationFont(f"C:/Windows/Fonts/{name}")
    window = MainWindow(settings=QSettings(str(folder / "settings.ini"), QSettings.IniFormat))
    window.output_edit.setText(str(folder / "stems"))
    window.audio_output.setMuted(True)
    window.load_audio(audio)
    window.show()
    result = {"heartbeat_ticks": 0, "audio_seconds": 8, "model": "htdemucs", "device": "cpu",
              "mode": "cancellation" if args.cancel_after else "separation"}
    started = time.monotonic()
    timer = QTimer()
    finishing = False

    def finish():
        timer.stop()
        result["elapsed_seconds"] = time.monotonic() - started
        result["status"] = window.status.text()
        result["track_count"] = window.tracks.count()
        result["preview_duration_ms"] = window.player.duration()
        result["stems"] = verify_stems(window.result_path, audio_info(audio)) if window.result_path else []
        result["success"] = (window.result_path is not None and window.tracks.count() == 5 and
                             result["heartbeat_ticks"] > 10 and window.player.duration() == 8000 and
                             len(result["stems"]) == 4 and all(
                                 item["finite"] and item["duration_matches"] and item["format_matches_input"]
                                 for item in result["stems"]))
        if args.cancel_after:
            result["temporary_dirs_remaining"] = [str(p) for p in (folder / "stems").rglob("pystem-*")]
            result["success"] = ("cancelada" in window.status.text() and window.worker is None and
                                 not result["temporary_dirs_remaining"])
        window.grab().save(str(folder / "completed.png"))
        (folder / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        window.close()
        app.exit(0 if result["success"] else 1)

    def tick():
        nonlocal finishing
        result["heartbeat_ticks"] += 1
        if result["heartbeat_ticks"] == 10:
            window.grab().save(str(folder / "processing.png"))
        if window.worker is None and not finishing:
            finishing = True
            QTimer.singleShot(600, finish)
        if time.monotonic() - started > 60 and window.worker:
            window.cancel_separation()

    window.start_separation()
    if args.cancel_after:
        QTimer.singleShot(args.cancel_after, window.cancel_separation)
    timer.timeout.connect(tick)
    timer.start(25)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
