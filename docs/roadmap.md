# PYStem — Development Roadmap

> An AI-powered music source separation application built with Python.

## Project Overview

PYStem is a Python application designed to separate audio tracks into individual stems using machine learning.

The project uses Demucs as its initial separation engine and aims to provide an accessible environment for extracting, listening to, managing, and exporting audio stems.

The project is also a learning journey focused on Python development, digital signal processing, audio programming, software architecture, and graphical user interface development.

**Development status:** Early prototype (v0.1)

---

## v0.1 — Foundation & Audio Separation

**Status: Functional prototype**

### Project Setup

- [x] Create GitHub repository.
- [x] Initialize Git and connect the remote repository.
- [x] Install Python 3.11.
- [x] Create a virtual environment.
- [x] Configure `.gitignore`.
- [x] Create the initial project structure.
- [x] Create `requirements.txt`.
- [ ] Document installation and usage in `README.md`.

### Audio Separation

- [x] Install Demucs and its dependencies.
- [x] Implement audio separation using Python.
- [x] Use the pretrained HTDemucs model.
- [x] Separate audio into four stems:
  - Vocals
  - Drums
  - Bass
  - Other
- [x] Save separated stems as WAV files.
- [x] Test separation using a FLAC audio file.
- [x] Validate whether the input file exists.
- [x] Handle Demucs process failures.
- [x] Display the output directory.

### Command-Line Interface

- [x] Create the application entry point.
- [x] Implement an interactive menu.
- [x] Add an audio separation option.
- [x] Add an exit option.
- [x] Handle invalid menu selections.

### Initial Testing

- [x] Successfully separate VIANOVA — Squier Talk.
- [x] Confirm generation of all four stems.
- [x] Test invalid file paths.
- [x] Test menu navigation and exit behavior.

---

## v0.2 — Audio Playback

**Goal:** Play and control separated audio directly inside PYStem.

### Audio Loading

- [ ] Research Python audio playback libraries.
- [ ] Select a suitable playback backend.
- [ ] Load WAV files.
- [ ] Read sample rate, channel count, and duration.
- [ ] Validate audio format compatibility.
- [ ] Handle missing or corrupted audio files.

### Playback Controls

- [ ] Implement Play.
- [ ] Implement Pause.
- [ ] Implement Resume.
- [ ] Implement Stop.
- [ ] Display current playback time.
- [ ] Display total audio duration.
- [ ] Implement seeking.

### Stem Playback

- [ ] Load multiple stems from the same track.
- [ ] Play stems simultaneously.
- [ ] Keep all stems synchronized.
- [ ] Allow individual stem playback.
- [ ] Implement stem selection.
- [ ] Handle playback errors.

### Testing

- [ ] Test playback with the VIANOVA stems.
- [ ] Test playback synchronization.
- [ ] Test pause and resume behavior.
- [ ] Test different sample rates and channel configurations.

---

## v0.3 — Graphical User Interface

**Goal:** Replace the command-line workflow with a desktop interface.

### Framework

- [ ] Research PySide6 and PyQt6.
- [ ] Select a GUI framework.
- [ ] Create the main application window.
- [ ] Organize GUI components into separate modules.
- [ ] Connect the GUI to the separation engine.

### File Management

- [ ] Implement a file selection dialog.
- [ ] Display the selected filename.
- [ ] Display audio metadata.
- [ ] Allow users to select an output directory.
- [ ] Add drag-and-drop audio importing.

### Separation Interface

- [ ] Add a Start Separation button.
- [ ] Display separation status.
- [ ] Implement a progress indicator.
- [ ] Keep the interface responsive during processing.
- [ ] Display success and error messages.
- [ ] Allow users to open the output directory.

### Playback Interface

- [ ] Add Play, Pause, and Stop buttons.
- [ ] Add a playback timeline.
- [ ] Display elapsed and total time.
- [ ] Display loaded stems.
- [ ] Allow users to switch between tracks.

---

## v0.4 — Stem Mixer

**Goal:** Turn PYStem into a basic multitrack audio mixer.

### Mixing Controls

- [ ] Implement individual stem volume controls.
- [ ] Implement Mute for each stem.
- [ ] Implement Solo for each stem.
- [ ] Implement a master volume control.
- [ ] Implement stereo panning.
- [ ] Prevent audio clipping where possible.

### Mixer Interface

- [ ] Create separate channels for each stem.
- [ ] Add volume sliders.
- [ ] Add Mute and Solo buttons.
- [ ] Display channel names.
- [ ] Add a master output section.
- [ ] Display audio levels.

### Audio Visualization

- [ ] Generate waveform previews.
- [ ] Display individual stem waveforms.
- [ ] Implement a playback cursor.
- [ ] Add basic peak meters.
- [ ] Explore frequency spectrum visualization.

### Testing

- [ ] Test synchronization while adjusting volumes.
- [ ] Test Mute and Solo combinations.
- [ ] Test stereo panning.
- [ ] Test master volume behavior.

---

## v0.5 — Advanced Separation

**Goal:** Give users more control over the separation process.

### Model Selection

- [ ] Support multiple compatible Demucs models.
- [ ] Display available models.
- [ ] Allow users to select a model.
- [ ] Document model differences.
- [ ] Manage model downloads and caching.

### Processing Options

- [ ] Add CPU/GPU device selection where supported.
- [ ] Add configurable processing options.
- [ ] Support two-stem separation.
- [ ] Allow users to choose the output directory.
- [ ] Improve processing progress reporting.
- [ ] Explore cancellation of ongoing processing.

### Audio Formats

- [ ] Improve WAV support.
- [ ] Test MP3 input.
- [ ] Test FLAC input.
- [ ] Explore additional supported formats.
- [ ] Implement output format selection.
- [ ] Support appropriate bit-depth and quality options.

### Batch Processing

- [ ] Allow multiple audio files to be selected.
- [ ] Create a processing queue.
- [ ] Display individual track progress.
- [ ] Handle errors without stopping the entire queue.
- [ ] Organize results by track.

---

## v0.6 — Export & Project Management

**Goal:** Allow users to save their work and export custom audio mixes.

### Audio Export

- [ ] Export individual stems.
- [ ] Export selected combinations of stems.
- [ ] Export a complete custom mix.
- [ ] Support WAV export.
- [ ] Explore FLAC and MP3 export.
- [ ] Preserve appropriate sample rates and channel formats.
- [ ] Handle clipping and output levels.

### Project Management

- [ ] Create a PYStem project format.
- [ ] Save imported audio references.
- [ ] Save mixer settings.
- [ ] Save stem volume and pan settings.
- [ ] Reopen previous projects.
- [ ] Handle missing project files.
- [ ] Add a recent projects list.

---

## v0.7 — Digital Signal Processing

**Goal:** Introduce audio processing tools developed with Python.

### DSP Fundamentals

- [ ] Study digital audio sampling.
- [ ] Study amplitude and decibels.
- [ ] Explore time-domain signals.
- [ ] Explore frequency-domain signals.
- [ ] Study the Fourier Transform.
- [ ] Implement basic signal visualization.

### Audio Processing

- [ ] Implement gain adjustment.
- [ ] Explore normalization.
- [ ] Implement basic filtering.
- [ ] Explore equalization.
- [ ] Explore simple delay and echo effects.
- [ ] Investigate real-time processing constraints.

### Visualization

- [ ] Display frequency spectra.
- [ ] Explore spectrograms.
- [ ] Visualize audio before and after processing.

---

## v0.8 — Performance & Reliability

**Goal:** Improve speed, stability, and usability.

### Performance

- [ ] Profile CPU and memory usage.
- [ ] Reduce unnecessary memory allocations.
- [ ] Improve loading of large audio files.
- [ ] Investigate efficient audio buffering.
- [ ] Optimize playback and mixing.
- [ ] Evaluate supported GPU acceleration.

### Reliability

- [ ] Expand automated tests.
- [ ] Add integration tests.
- [ ] Improve exception handling.
- [ ] Implement application logging.
- [ ] Test long audio files.
- [ ] Test unusual filenames and paths.
- [ ] Test different Windows environments.

### Code Quality

- [ ] Refactor duplicated code.
- [ ] Improve module organization.
- [ ] Add type hints.
- [ ] Add docstrings.
- [ ] Configure Ruff.
- [ ] Document major architectural decisions.

---

## v0.9 — Release Preparation

**Goal:** Prepare PYStem for distribution.

### User Experience

- [ ] Review the application layout.
- [ ] Improve navigation.
- [ ] Add keyboard shortcuts.
- [ ] Add tooltips and help messages.
- [ ] Create an application icon.
- [ ] Improve error notifications.

### Documentation

- [ ] Complete the main README.
- [ ] Write installation instructions.
- [ ] Write a user guide.
- [ ] Document supported audio formats.
- [ ] Document known limitations.
- [ ] Document troubleshooting steps.
- [ ] Review third-party licenses and model usage conditions.

### Distribution

- [ ] Investigate PyInstaller or similar tools.
- [ ] Build a Windows executable.
- [ ] Test the executable on a clean Windows environment.
- [ ] Ensure required audio dependencies are included.
- [ ] Document model download requirements.
- [ ] Prepare release notes.

---

## v1.0 — First Stable Release

**Goal:** Deliver a complete and usable desktop audio separation application.

### Release Requirements

- [ ] Reliable audio importing.
- [ ] Functional AI stem separation.
- [ ] Stable synchronized playback.
- [ ] Individual stem volume controls.
- [ ] Mute and Solo functionality.
- [ ] Audio visualization.
- [ ] Custom mix export.
- [ ] Functional desktop GUI.
- [ ] Clear error handling.
- [ ] User documentation.
- [ ] Windows distribution package.
- [ ] Final regression testing.

---

## Future Ideas — Beyond v1.0

These features are experimental possibilities and are not guaranteed to be implemented.

### Advanced Audio Tools

- [ ] Explore alternative source separation models.
- [ ] Investigate finer instrument separation.
- [ ] Explore vocal enhancement.
- [ ] Investigate audio denoising.
- [ ] Explore advanced equalization.
- [ ] Investigate audio effects and plugins.

### User Experience

- [ ] Add keyboard-customizable shortcuts.
- [ ] Add application themes.
- [ ] Explore audio device selection.
- [ ] Add customizable mixer layouts.

### PYSpatial Integration

- [ ] Establish a standard WAV-based workflow with PYSpatial.
- [ ] Export stems in a PYSpatial-compatible format.
- [ ] Explore opening exported stems in PYSpatial.
- [ ] Document the workflow between both applications.

**Note:** PYStem and PYSpatial will remain independent applications and repositories.

---

## Development Journal

Development sessions, experiments, problems, and solutions will be recorded in:

`docs/diario.md`

Each entry should include:

- Date
- Session objectives
- Implemented features
- Problems encountered
- Solutions
- Concepts learned
- Next steps

---

## Development Principles

1. **Learn by building.** Understand the code instead of simply copying solutions.
2. **Keep the architecture modular.** Separate audio processing, playback, and GUI logic.
3. **Build incrementally.** Implement and test one feature at a time.
4. **Document progress.** Record meaningful development milestones.
5. **Prioritize stability.** Working features come before unnecessary complexity.
6. **Respect dependencies and licenses.** Track third-party libraries, models, and their requirements.
7. **Keep projects independent.** PYStem should function without PYSpatial.

---

_This roadmap is a living document and will evolve as PYStem develops._
