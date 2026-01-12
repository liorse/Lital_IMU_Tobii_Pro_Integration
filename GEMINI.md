# Lital IMU Tobii Pro Integration

## Project Overview

This is a research application designed for studying infant agency using IMU sensors and mobile stimuli. Built on the **ScopeFoundry** framework, it integrates **MetaWear** motion sensors with audio/visual feedback controlled by infant movements. It also includes **USB TTL** integration for synchronization with external devices like Tobii Pro eye trackers.

## Environment Setup

### Prerequisites
*   **Miniconda** (64-bit)
*   **Visual Studio Code**
*   **Git for Windows**
*   **FFmpeg** (ensure it's in the system PATH)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/liorse/Lital_IMU_Tobii_Pro_Integration
    cd Lital_IMU_Tobii_Pro_Integration
    ```

2.  **Create the Conda environment:**
    ```bash
    conda env create --file environment.yml
    ```
    *This process may take 5+ minutes.*

3.  **Activate the environment:**
    ```bash
    conda activate lital
    ```

## Running the Application

### Command Line Interface
The application requires a hardware configuration argument (`shiba` or `hebrew`) to load the correct Bluetooth MAC addresses for the sensors.

*   **Shiba Configuration:**
    ```bash
    python Agency_Sensor_MAIN.py shiba
    # OR
    shiba.bat
    ```

*   **Hebrew Configuration:**
    ```bash
    python Agency_Sensor_MAIN.py hebrew
    # OR
    hebrew.bat
    ```

*   **Default Run (might fail if config missing):**
    ```bash
    python Agency_Sensor_MAIN.py
    ```

### VS Code
Launch configurations are provided in `.vscode/launch.json` for debugging both "hebrew" and "shiba" setups.

## Project Architecture

The application follows the **ScopeFoundry** architecture, separating **Hardware** (device interface) from **Measurement/UI** (logic & control).

### Key Files & Directories

*   **`Agency_Sensor_MAIN.py`**: The entry point. Initializes the `AgencySensor` app, loads `config.yaml`, and instantiates hardware/measurement components.
*   **`config.yaml`**: Central configuration file. Defines hardware MAC addresses, experiment tasks, music paths, and TTL settings.
*   **`environment.yml`**: Conda environment definition.

### Hardware Components
*   **`HW_MetaMotionRL.py`**: Interface for MetaWear IMU sensors. Handles Bluetooth connection and data streaming.
*   **`HW_USB_TTL.py`**: Interface for the USB TTL module (typically FTDI). Used for sending event markers to external systems (e.g., Tobii Pro).

### Measurement & UI Components
*   **`UI_Experiment_Control.py`**: Manages the experimental protocol (state machine for steps like "Fixation", "Baseline", "Connect").
*   **`UI_Mobile_Control.py`**: Controls the stimuli (mobile) based on sensor data. Implements movement models (Zaadnoordijk & Physical).
*   **`UI_MetaMotionRL.py`**: Visualization and buffering of raw IMU data.
*   **`UI_USB_TTL.py`**: UI for monitoring and manually triggering TTL signals.

### Subprocesses
*   **`stimuli_sound_pygame_midi.py`**: A separate process for handling real-time audio/visual feedback. Communicates with the main app via **ZeroMQ (ZMQ)** on port `5556`.

## Configuration (`config.yaml`)

*   **`participant_ranges`**: ID ranges for different study groups.
*   **`tasks`**: Ordered list of experiment steps (duration, active limb, music).
*   **`hardware_shiba` / `hardware_hebrew`**: Bluetooth MAC addresses for the 4 IMU sensors (Left/Right Hand/Leg).
*   **`hardware.usb_ttl_module`**: COM port (`COM3`), baudrate, and signal mappings for TTL.
*   **`music`**: File paths for audio assets and volume settings.

## Development Notes

### Conventions
*   **ScopeFoundry**: Inherit from `BaseMicroscopeApp`, `HardwareComponent`, or `Measurement`.
*   **Threading**: The main GUI runs on the PyQt5 thread. Heavy processing or hardware I/O should handle threading carefully (ScopeFoundry handles much of this).
*   **Data Persistence**: Experimental data is saved in **HDF5** format via ScopeFoundry.
*   **Subprocess Cleanup**: The stimuli subprocess is managed via `atexit` to ensure it terminates when the main app closes.

### Troubleshooting
*   **Bluetooth Connection**: Ensure the correct configuration (`shiba`/`hebrew`) is used for the physical sensors present.
*   **COM Ports**: If the USB TTL module fails, check the Windows Device Manager for the correct COM port and update `config.yaml`.
*   **Latency**: For the USB TTL module, ensure the FTDI driver latency timer is set to **1ms** in Device Manager.
