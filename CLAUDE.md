# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research application for studying infant agency through IMU sensors and mobile stimuli. It integrates MetaWear motion sensors with audio/visual feedback controlled by infant movements, built on the ScopeFoundry framework.

## Environment Setup

### Conda Environment
```bash
# Create environment from file (takes 5+ minutes)
conda env create --file environment.yml

# Activate environment
conda activate lital
```

### Required External Dependencies
- Miniconda 64-bit
- Visual Studio Code
- GitHub Desktop
- Git for Windows
- ffmpeg

## Running the Application

### Primary Entry Point
```bash
# Default run
python Agency_Sensor_MAIN.py

# With specific hardware configuration
python Agency_Sensor_MAIN.py shiba    # Uses config_shiba.yaml hardware
python Agency_Sensor_MAIN.py hebrew   # Uses config.yaml hardware_hebrew

# Or use batch files
hebrew.bat   # Runs with hebrew configuration
shiba.bat    # Runs with shiba configuration
```

### VS Code Debugging
Launch configurations are available in `.vscode/launch.json`:
- "Python Debugger: Current File" - runs Agency_Sensor_MAIN.py
- "Agency_Sensor_MAIN: hebrew" - runs with hebrew argument
- "Agency_Sensor_MAIN: with argument..." - prompts for argument

## Architecture

### ScopeFoundry Framework Structure

The application follows ScopeFoundry's hardware/measurement separation pattern:

**Main Application** (`Agency_Sensor_MAIN.py`):
- `AgencySensor` class extends `BaseMicroscopeApp`
- Loads hardware configurations from `config.yaml` based on command-line argument
- Initializes 4 MetaWear sensors (left/right hand, left/right leg)
- Sets up three UI measurement panels

**Hardware Components** (inherit from `HardwareComponent`):
- `MetaMotionRLHW` (`HW_MetaMotionRL.py`) - manages individual MetaWear sensor connection, data streaming, and acceleration data fusion

**Measurement/UI Components** (inherit from `Measurement`):
- `MetaWearUI` (`UI_MetaMotionRL.py`) - controls sensor data collection and visualization
- `MobileControllerUI` (`UI_Mobile_Control.py`) - controls mobile movement models and ZMQ communication with stimuli subprocess
- `ExperimentControllerUI` (`UI_Experiment_Control.py`) - manages experimental protocol steps defined in config.yaml

### Multi-Process Architecture

The application uses a multi-process design:

**Main Process**: PyQt5 GUI with ScopeFoundry framework
- Manages MetaWear sensor connections and data acquisition
- Processes acceleration data and applies movement models
- Sends mobile speed/volume commands via ZMQ (port 5556)

**Stimuli Subprocess**: (`stimuli_sound_pygame_midi.py`)
- Launched by MobileControllerUI via subprocess
- Receives speed/volume updates from ZMQ
- Controls MIDI playback speed and volume in real-time
- Terminated on application exit via `atexit` handler

### Configuration System

`config.yaml` structure:
- `tasks`: Experimental protocol steps with duration, limb connections, and music settings
- `hardware_shiba` / `hardware_hebrew`: MAC addresses for two different sensor sets
- `music`: Audio file paths and volume settings
- `baseline`: Timing parameters for baseline step

### Mobile Movement Models

Two models control how infant movement affects mobile stimuli:

**Zaadnoordijk Model** (`UI_Mobile_Control.py`):
- Based on research paper (https://doi.org/10.1016/j.dcn.2020.100760)
- Threshold-based: mobile plays for fixed duration when acceleration exceeds threshold
- Includes dead time after triggering

**Physical Model (Lior)**:
- Simulates physics: acceleration increases speed, friction decreases it
- More continuous/proportional response to movement

### Data Flow

1. MetaWear sensors stream acceleration data → `HW_MetaMotionRL`
2. Data buffered in `AccelerationDataBuffer` → `UI_MetaMotionRL`
3. Selected limb data → `UI_Mobile_Control`
4. Movement model processes acceleration → speed/volume
5. ZMQ publishes to stimuli subprocess → MIDI playback adjustment
6. All data logged to HDF5 files in `data/` directory

## Key Files

- `Agency_Sensor_MAIN.py` - Application entry point, initializes hardware and UI
- `config.yaml` - Main configuration for hardware, experimental tasks, and audio
- `HW_MetaMotionRL.py` - MetaWear sensor hardware abstraction
- `UI_Experiment_Control.py` - Experimental protocol state machine
- `UI_Mobile_Control.py` - Mobile control models and ZMQ communication
- `UI_MetaMotionRL.py` - Sensor data visualization and buffering
- `stimuli_sound_pygame_midi.py` - Separate process for real-time MIDI audio

## Important Implementation Notes

### MetaWear Sensor Integration
- Uses `mbientlab.metawear` and `mbientlab.warble` libraries
- Sensor configuration cached in `.metawear/*.json` files
- Connection requires Bluetooth; MAC addresses are hardware-specific
- Uses data fusion algorithm for linear acceleration extraction

### PyQt5 Threading
- COM initialization required on Windows: `pythoncom.CoInitialize()`
- Signal/slot pattern used for cross-thread communication (e.g., `acc_data_updated` signal)
- UI updates must happen on main thread

### Data Persistence
- HDF5 format used for experimental data (via ScopeFoundry's `h5_io`)
- CSV files in `Utils/` directory contain exported mobile control data
- Files named with pattern: `{StepDescription}_Mobile.{YYYY.MM.DD.SSSS.MM.NNN}.csv`

### Process Management
- Stimuli subprocess must be cleanly terminated to avoid orphaned processes
- Uses `atexit.register()` to ensure subprocess cleanup
- Version 1.0.1 introduced clean subprocess termination
