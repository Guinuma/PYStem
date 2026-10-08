# PYStem — TODO List

> Active development tasks and priorities.

**Current version:** v0.1  
**Current focus:** Project documentation and audio playback  
**Last updated:** 08/10/2026

---

## Priority 1 — Finish v0.1

### Documentation
- [x] Create the development roadmap.
- [ ] Create the development journal (`docs/diario.md`).
- [ ] Update the main `README.md`.
- [ ] Document project installation.
- [ ] Document basic CLI usage.

### Project Organization
- [x] Create the initial project structure.
- [x] Configure the Python virtual environment.
- [x] Configure `.gitignore` for Python.
- [x] Implement the audio separation engine.
- [x] Implement the interactive CLI menu.
- [x] Test audio separation with VIANOVA — Squier Talk.
- [ ] Confirm `output/` is ignored by Git.
- [ ] Review `requirements.txt`.
- [ ] Commit and push the first functional version.

---

## Priority 2 — Audio Playback (v0.2)

### Research
- [ ] Compare Python audio playback libraries.
- [ ] Choose an audio playback backend.
- [ ] Understand sample rate, channels, and audio buffers.

### Implementation
- [ ] Create `src/audio_player.py`.
- [ ] Implement WAV file loading.
- [ ] Implement basic audio playback.
- [ ] Implement Play and Stop.
- [ ] Implement Pause and Resume.
- [ ] Display track duration.
- [ ] Display current playback position.

### Stem Playback
- [ ] Load all four stems from a separation folder.
- [ ] Implement synchronized playback.
- [ ] Implement individual stem selection.
- [ ] Test playback using the VIANOVA stems.

### Testing
- [ ] Test invalid audio paths.
- [ ] Test missing stem files.
- [ ] Test playback completion.
- [ ] Test Pause/Resume behavior.
- [ ] Verify that stems remain synchronized.

---

## Priority 3 — Prepare the GUI (v0.3)

### Research
- [ ] Compare PySide6 and PyQt6.
- [ ] Choose a GUI framework.
- [ ] Sketch the application layout.

### Initial Interface
- [ ] Create a GUI module.
- [ ] Create the main application window.
- [ ] Add an Import Audio button.
- [ ] Add a Separate Audio button.
- [ ] Add a processing status display.
- [ ] Add basic playback controls.

---

## Priority 4 — Stem Mixer (v0.4)

- [ ] Create four mixer channels.
- [ ] Add individual volume sliders.
- [ ] Add Mute buttons.
- [ ] Add Solo buttons.
- [ ] Add master volume.
- [ ] Implement stereo panning.
- [ ] Add basic audio level meters.
- [ ] Test synchronized mixing.

---

## Maintenance

### Code Quality
- [ ] Add type hints to existing functions.
- [ ] Add docstrings.
- [ ] Configure Ruff.
- [ ] Review error handling.
- [ ] Create automated tests for the separation module.

### Git & Documentation
- [ ] Keep the roadmap updated.
- [ ] Update the TODO list after each session.
- [ ] Record completed work in the development journal.
- [ ] Make meaningful Git commits.

---

## Completed Milestones

- [x] Create the PYStem GitHub repository.
- [x] Install Python 3.11.9.
- [x] Create and activate `.venv`.
- [x] Install Demucs, PyTorch, and NumPy.
- [x] Implement the separation engine.
- [x] Successfully separate a FLAC file into four WAV stems.
- [x] Implement input validation.
- [x] Implement basic error handling.
- [x] Implement an interactive CLI menu.
- [x] Test invalid menu options.
- [x] Test nonexistent audio files.
- [x] Test application exit.

---

## Next Development Session

**Main objective:** Finish the v0.1 documentation and begin implementing audio playback.

1. Complete `docs/diario.md`.
2. Update `README.md`.
3. Review Git changes and create a commit.
4. Research audio playback libraries.
5. Create the initial audio player module.

---

*Keep this document focused on actionable tasks. Long-term goals belong in `roadmap.md`.*