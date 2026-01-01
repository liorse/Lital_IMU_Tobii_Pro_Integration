# Research Report: USB TTL Module Technical Implementation

**Feature**: USB TTL Module Integration for Tobii Pro Event Signaling
**Date**: 2026-01-01
**Status**: Complete

---

## Executive Summary

This research consolidates findings from three key areas:
1. Black Box Toolkit USB TTL Module specifications (official manual)
2. ScopeFoundry hardware component integration patterns
3. Testing strategies for hardware components in Python

All technical questions from the specification phase have been resolved with concrete implementation guidance.

---

## 1. Black Box Toolkit USB TTL Module Specifications

### Communication Protocol

**Decision**: The USB TTL Module uses a simple serial protocol at **115200 baud, 8N1** configuration.

**Serial Configuration**:
```python
port = 'COM3'
baudrate = 115200
bytesize = 8          # 8 data bits
parity = 'N'          # No parity
stopbits = 1          # 1 stop bit
timeout = 1.0         # 1 second read timeout
write_timeout = 0.1   # 100ms write timeout (non-blocking)
flow_control = None   # No hardware/software flow control
```

**Command Structure**:

1. **Initialization** (required on first connect):
   ```python
   serial_port.write(b'RR')  # Resets module and clears all TTL lines
   ```

2. **Verification** (optional, confirms module is responding):
   ```python
   serial_port.write(b'##')  # Should receive 'XX' back
   ```

3. **Sending TTL Output Signals** (0x00 to 0xFF):
   ```python
   # Example: Turn on TTL Output Line 1
   serial_port.write(b'01')  # Hex byte pair in CAPITALS

   # Example: Turn on all 8 output lines
   serial_port.write(b'FF')

   # Example: Clear all outputs
   serial_port.write(b'00')
   ```

4. **Receiving TTL Input Signals**:
   - Module automatically sends 2-byte hex strings when input lines change
   - Only changes are reported (not continuous polling)
   - Example: If TTL Input Line 1 goes HIGH, module sends `b'01'`

**Critical Requirements**:
- Always send/receive **exactly 2 bytes** (hex pairs in CAPITALS)
- Sending single bytes causes sync issues
- Open serial port once per session (not per transmission)
- Initialize with `RR` at session start
- Optionally send `RR` at session end to clear outputs

**Rationale**: This protocol is optimized for low-latency event marking. The 2-byte hex format directly maps to 8-bit parallel TTL output (0x00-0xFF = 0-255 decimal = 00000000-11111111 binary, where each bit controls one output pin).

**Alternatives Considered**: None - this is the manufacturer's fixed protocol.

---

### Driver Requirements

**Decision**: Use standard FTDI Virtual COM Port (VCP) drivers on Windows. No custom drivers required.

**Driver Installation**:
- **Windows 7/8/10**: Drivers auto-install via Windows Update when device is first connected
- **Manual installation**: FTDI VCP drivers available at https://ftdichip.com/drivers/vcp-drivers/
- **Driver type**: FTDI FT232R chip - appears as standard COM port

**Critical Configuration Step** (MUST be performed manually):

The default FTDI driver latency is **16ms**, which is too slow for eye-tracking synchronization. This **MUST** be changed to **1ms**:

1. Open Device Manager (`devmgmt.msc`)
2. Navigate to Ports (COM & LPT) → USB Serial Port (COMx)
3. Right-click → Properties → Port Settings → Advanced
4. Set **Latency Timer** to **1ms** (down from default 16ms)
5. Click OK to apply

**Verification**: Use the Black Box Toolkit Configuration Utility to validate latency:
- Expected result: Mean latency <1ms for 50 event mark pairs
- If latency >1ms, driver configuration is incorrect

**Rationale**: The 1ms latency setting ensures TTL signals are transmitted within the sub-17ms requirement for 60Hz eye-tracking synchronization.

**Alternatives Considered**:
- Using default 16ms latency: Rejected - too slow for research timing requirements
- Custom driver development: Not necessary - FTDI VCP drivers are industry standard

---

### Timing Specifications

**Decision**: The USB TTL Module provides sub-millisecond latency suitable for eye-tracking synchronization.

**Measured Performance** (from manufacturer specifications):

| Metric | Value | Notes |
|--------|-------|-------|
| Sampling rate | 109 kHz | Module checks TTL I/O status 109,000 times/second |
| Output latency | 254 μs (typical) | Time from receiving hex bytes to TTL output |
| Input response | 350 μs (typical) | Time from TTL input change to sending hex bytes to PC |
| 50 event mark pairs | M=290μs, SD=10μs | Measured with internal hardware timer |
| Total PC-to-TTL latency | ~1-3ms | Includes USB overhead (1-2ms) + transmission (0.087ms @ 115200 baud) |

**Meets Requirements**:
- ✅ Sub-17ms for 60Hz eye-tracking (actual: 1-3ms total latency)
- ✅ Precise enough for event marking experimental events
- ✅ Stable for 2+ hour sessions

**Jitter Considerations**:
- USB inherent jitter: ±1ms typical
- Tobii Pro systems handle this jitter level well
- For precise timing analysis, timestamp should be captured in Python immediately before write()

**Signal Duration**:
- TTL outputs **latch** (remain on until changed)
- To create pulses: send ON code, wait desired duration, send OFF code
  ```python
  ttl.write(b'42')      # Event marker on
  time.sleep(0.001)     # 1ms pulse width
  ttl.write(b'00')      # Reset to baseline
  ```

**Rationale**: Hardware-timed at 109kHz provides deterministic, sub-millisecond event marking far exceeding the <17ms requirement.

**Alternatives Considered**: None - hardware specifications are fixed.

---

### Python Integration Best Practices

**Decision**: Use `pyserial` library (already in environment.yml as version 3.5) with non-blocking writes and proper buffer management.

**Recommended Implementation Pattern**:

```python
import serial
import time
import logging

class USBTTLModule:
    """
    USB TTL Module for event signaling to Tobii Pro
    Following Black Box Toolkit specifications
    """

    def __init__(self, port='COM3', baudrate=115200, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.simulated = False

    def connect(self):
        """Open serial connection with automatic fallback to simulated mode"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=0.1,  # 100ms write timeout (non-blocking)
                xonxoff=False,      # No software flow control
                rtscts=False,       # No hardware RTS/CTS
                dsrdtr=False        # No DSR/DTR
            )

            # Set DTR and RTS (some modules need this for power)
            self.serial_connection.dtr = True
            self.serial_connection.rts = False

            # Clear buffers
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

            # Initialize module (CRITICAL!)
            self.serial_connection.write(b'RR')
            time.sleep(0.1)  # Brief pause after init

            # Verify with ping
            self.serial_connection.write(b'##')
            response = self.serial_connection.read(2)
            if response != b'XX':
                logging.warning(f"Unexpected response to ping: {response}")

            self.simulated = False
            logging.info(f"USB TTL Module connected on {self.port}")
            return True

        except serial.SerialException as e:
            logging.warning(f"Hardware not found: {e}. Switching to SIMULATED mode.")
            self.simulated = True
            return False

    def send_signal(self, value):
        """
        Send 8-bit TTL signal (0x00 to 0xFF)

        Args:
            value (int): Hex value between 0 and 255
        Returns:
            bool: True if successful
        """
        if not (0 <= value <= 255):
            logging.error(f"Invalid value {value}. Must be 0-255.")
            return False

        # Convert to 2-byte hex string in CAPITALS
        hex_string = f"{value:02X}".encode('ascii')

        if self.simulated:
            logging.debug(f"[SIMULATED] TTL signal: {hex_string.decode()}")
            return True

        try:
            bytes_written = self.serial_connection.write(hex_string)
            if bytes_written == 2:
                return True
            else:
                logging.error(f"Incomplete write: {bytes_written}/2 bytes")
                return False
        except serial.SerialTimeoutException:
            logging.error("Write timeout (>100ms)")
            return False
        except Exception as e:
            logging.error(f"Write error: {e}")
            return False

    def disconnect(self):
        """Close connection and reset all outputs"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                # Reset all outputs before disconnect
                self.serial_connection.write(b'RR')
                time.sleep(0.05)
                self.serial_connection.close()
                logging.info("USB TTL Module disconnected")
            except Exception as e:
                logging.error(f"Error during disconnect: {e}")

        self.serial_connection = None
```

**Key Best Practices**:

1. **Non-blocking writes**: `write_timeout=0.1` prevents blocking PyQt5 event loop
2. **Buffer clearing**: Always clear buffers after connection to avoid stale data
3. **Single open/close**: Open once per session, not per transmission
4. **Initialization**: Always send `RR` after opening port
5. **2-byte commands**: Always send exactly 2 bytes in hex, CAPITALS
6. **Error handling**: Try/except with fallback to simulated mode
7. **Simulated mode**: For development/testing without hardware

**Rationale**: This pattern follows manufacturer recommendations and integrates cleanly with ScopeFoundry's architecture.

**Alternatives Considered**:
- Using parallel port emulation: Not supported by hardware
- Direct USB communication: Module requires serial protocol via FTDI chip

---

## 2. ScopeFoundry Hardware Component Integration Patterns

### HardwareComponent Lifecycle

**Decision**: Follow the existing `MetaMotionRLHW` pattern with three-phase lifecycle: `__init__` → `setup()` → `connect()` → `disconnect()`.

**Lifecycle Pattern**:

```python
from ScopeFoundry import HardwareComponent
from PyQt5.QtCore import pyqtSignal
import serial

class USBTTLHardware(HardwareComponent):

    name = 'USB_TTL_Module'

    # Signal for event notification (optional)
    signal_sent = pyqtSignal(int, float)  # (hex_value, timestamp)

    def __init__(self, app, name=None, debug=False, port='COM3'):
        # Initialize instance variables BEFORE calling parent
        self.debug = debug
        self.port = port
        self.serial_connection = None
        self.simulated_mode = False

        # Call parent AFTER instance variables
        HardwareComponent.__init__(self, app, name=name)

    def setup(self):
        """Define settings and operations. Called once during app init."""
        # Settings (exposed to UI)
        self.settings.New(name='port', initial=self.port, dtype=str, ro=False)
        self.settings.New(name='baud_rate', initial=115200, dtype=int, ro=False)
        self.settings.New(name='connected', initial=False, dtype=bool, ro=True)
        self.settings.New(name='simulated', initial=False, dtype=bool, ro=True)

        # Operations (appear as buttons in UI)
        self.add_operation(name='send_test_pulse', op_func=self.send_test_pulse)
        self.add_operation(name='reset_module', op_func=self.reset_module)

    def connect(self):
        """Establish hardware connection. Called when user clicks Connect."""
        # [Implementation from section 1.4 above]
        pass

    def disconnect(self):
        """Clean up connection. MUST be robust to partial initialization."""
        try:
            if hasattr(self, 'serial_connection') and self.serial_connection:
                self.serial_connection.write(b'RR')
                time.sleep(0.05)
                self.serial_connection.close()
        except Exception as e:
            print(f"Disconnect error: {e}")

        # ALWAYS disconnect settings (even if errors occurred)
        self.settings.disconnect_all_from_hardware()

    def send_ttl_signal(self, value):
        """Method to be called by other components"""
        # [Implementation from section 1.4 above]
        pass

    def send_test_pulse(self):
        """Operation for testing"""
        self.send_ttl_signal(0x01)
        time.sleep(0.01)
        self.send_ttl_signal(0x00)

    def reset_module(self):
        """Operation to reset module"""
        if self.serial_connection:
            self.serial_connection.write(b'RR')
```

**Key Patterns from Existing Codebase** (`HW_MetaMotionRL.py`):

1. **Instance variables before parent init**:
   ```python
   self.port = port
   HardwareComponent.__init__(self, app, name=name)
   ```

2. **Settings with choices** (for dropdowns):
   ```python
   self.settings.New(name='event_code', initial=1, dtype=int,
                    choices=[(f'Event {i}', i) for i in range(1, 256)])
   ```

3. **Settings connection to hardware**:
   ```python
   def connect(self):
       self.settings.port.connect_to_hardware(
           write_func=self.set_port,
           read_func=lambda: self.port
       )
   ```

4. **PyQt signals for cross-thread communication**:
   ```python
   # In __init__:
   self.signal_sent = pyqtSignal(int, float)

   # When sending signal:
   self.signal_sent.emit(value, time.time())
   ```

**Rationale**: This pattern ensures proper initialization order, clean resource management, and thread-safe UI updates.

**Alternatives Considered**: Custom base class - Rejected to maintain consistency with existing ScopeFoundry components.

---

### Integration with Main Application

**Decision**: Register hardware in `Agency_Sensor_MAIN.py` following the existing pattern for MetaWear sensors.

**Configuration in `config.yaml`**:

```yaml
# Add to config.yaml
hardware_ttl:
  port: "COM3"
  baud_rate: 115200
  simulated: false  # Set to true for testing without hardware
```

**Registration in `Agency_Sensor_MAIN.py`**:

```python
from HW_USB_TTL import USBTTLHardware
import yaml

class AgencySensor(BaseMicroscopeApp):
    name = 'Agency Sensor'

    def __init__(self, argv, dark_mode=False):
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        # Parse TTL configuration
        if 'hardware_ttl' in config:
            self.ttl_port = config['hardware_ttl'].get('port', 'COM3')
            self.ttl_baud = config['hardware_ttl'].get('baud_rate', 115200)
        else:
            self.ttl_port = 'COM3'
            self.ttl_baud = 115200

        BaseMicroscopeApp.__init__(self, argv, dark_mode=dark_mode)

    def setup(self):
        # Add existing hardware
        self.add_hardware(MetaMotionRLHW(self, name='LeftHandMeta',
                                        MAC=self.left_hand_mac))
        # ... other MetaWear sensors ...

        # Add USB TTL Module
        self.add_hardware(USBTTLHardware(self, name='TTL_Module',
                                        port=self.ttl_port))

        # Add measurements/UI
        self.add_measurement(MetaWearUI(self))
        self.add_measurement(MobileControllerUI(self))
        self.add_measurement(ExperimentControllerUI(self))
```

**Usage from Other Components** (e.g., `UI_Experiment_Control.py`):

```python
class ExperimentControllerUI(Measurement):

    def setup(self):
        self.ttl_hardware = self.app.hardware['TTL_Module']

    def on_experiment_step_change(self, step_number):
        """Called when experiment transitions to new step"""
        # Send event code to Tobii Pro
        event_code = step_number  # Simple mapping: step 1 = 0x01, etc.
        self.ttl_hardware.send_ttl_signal(event_code)

        # Log for debugging
        self.log.info(f"TTL event marker sent: {event_code:#04x} for step {step_number}")
```

**Rationale**: This maintains consistency with existing hardware integration patterns and allows easy access from any measurement component.

**Alternatives Considered**: Singleton pattern for global access - Rejected to maintain ScopeFoundry architecture patterns.

---

## 3. Testing Strategies for Hardware Components

### Testing Framework Selection

**Decision**: Use **pytest** with **unittest.mock** for testing the USB TTL hardware component.

**Justification**:
- **pytest**: Less boilerplate, better fixtures, parametrized tests
- **unittest.mock**: Built-in (no extra dependencies), sufficient for serial port mocking
- **pytest-qt**: For testing PyQt5 signals (already recommended for ScopeFoundry)

**Dependencies to Add** (`environment.yml` or `pip install`):

```yaml
# Add to environment.yml under pip dependencies
- pytest==7.4.3
- pytest-mock==3.12.0
- pytest-qt==4.2.0
```

**Rationale**: Minimal dependency additions, matches Python testing best practices, integrates with VS Code test explorer.

**Alternatives Considered**:
- unittest: More verbose, less flexible fixtures
- nose/nose2: Deprecated or less maintained

---

### Hardware Mocking Strategies

**Decision**: Use `unittest.mock.patch` to mock `serial.Serial` class for unit testing without hardware.

**Mock Pattern**:

```python
# tests/test_hw_usb_ttl.py
import pytest
from unittest.mock import Mock, MagicMock, patch
import serial

@pytest.fixture
def mock_serial():
    """Mock serial.Serial for testing without hardware"""
    with patch('serial.Serial') as mock:
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_instance.write.return_value = 2  # 2 bytes written
        mock_instance.read.return_value = b'XX'
        mock.return_value = mock_instance
        yield mock_instance

def test_connect_to_hardware(mock_serial):
    """Test successful hardware connection"""
    from HW_USB_TTL import USBTTLHardware

    hw = USBTTLHardware(app=Mock(), port='COM3')
    hw.setup()
    hw.connect()

    # Verify serial port opened with correct params
    serial.Serial.assert_called_once_with(
        port='COM3',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1.0,
        write_timeout=0.1,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False
    )

    # Verify initialization command sent
    assert mock_serial.write.call_count >= 1
    assert b'RR' in [call[0][0] for call in mock_serial.write.call_args_list]

def test_send_ttl_signal(mock_serial):
    """Test sending TTL signal"""
    from HW_USB_TTL import USBTTLHardware

    hw = USBTTLHardware(app=Mock(), port='COM3')
    hw.setup()
    hw.connect()

    # Send signal
    result = hw.send_ttl_signal(0x42)

    assert result == True
    mock_serial.write.assert_called_with(b'42')

@pytest.mark.parametrize("value,expected", [
    (0, b'00'),
    (1, b'01'),
    (255, b'FF'),
    (0x42, b'42'),
])
def test_value_encoding(mock_serial, value, expected):
    """Test hex value encoding"""
    from HW_USB_TTL import USBTTLHardware

    hw = USBTTLHardware(app=Mock(), port='COM3')
    hw.setup()
    hw.connect()
    hw.send_ttl_signal(value)

    mock_serial.write.assert_called_with(expected)
```

**Simulated Mode Testing**:

```python
def test_simulated_mode_fallback():
    """Test automatic fallback to simulated mode"""
    from HW_USB_TTL import USBTTLHardware

    with patch('serial.Serial', side_effect=serial.SerialException("Port not found")):
        hw = USBTTLHardware(app=Mock(), port='COM99')
        hw.setup()
        result = hw.connect()

        assert result == False  # Connection failed
        assert hw.simulated_mode == True

        # Should still accept commands in simulated mode
        assert hw.send_ttl_signal(0x01) == True
```

**Rationale**: Mocking allows testing without physical hardware while verifying correct serial communication protocol.

**Alternatives Considered**:
- Virtual serial port pairs: Overly complex for unit tests
- Hardware-in-loop testing: Better for integration tests, not unit tests

---

### Minimal Test Structure

**Decision**: Create `tests/` directory with organized test files and shared fixtures.

**Directory Structure**:

```
D:\github\Lital_IMU_Tobii_Pro_Integration\
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── test_hw_usb_ttl.py          # USB TTL hardware tests
│   └── fixtures/
│       └── mock_hardware.py         # Custom test utilities
├── HW_USB_TTL.py                    # Implementation
├── pytest.ini                       # Pytest configuration
└── environment.yml
```

**pytest.ini Configuration**:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    unit: Unit tests (no hardware)
    hardware: Tests requiring real hardware (skip by default)
addopts =
    -v
    --strict-markers
    -m "not hardware"  # Skip hardware tests by default
```

**conftest.py** (shared fixtures):

```python
"""Shared test fixtures"""
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.fixture
def mock_app():
    """Mock ScopeFoundry app"""
    app = Mock()
    app.settings = {}
    app.log = Mock()
    return app

@pytest.fixture
def mock_serial():
    """Mock serial port"""
    with patch('serial.Serial') as mock:
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_instance.write.return_value = 2
        mock.return_value = mock_instance
        yield mock_instance
```

**Running Tests**:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run hardware tests (if hardware connected)
pytest -m hardware

# Run specific test file
pytest tests/test_hw_usb_ttl.py
```

**Rationale**: Organized structure enables easy test discovery, shared fixtures reduce duplication, configuration allows selective test execution.

**Alternatives Considered**: Flat structure in root - Rejected to keep codebase organized.

---

## 4. Implementation Checklist

Based on research findings, the implementation should proceed in this order:

### Phase 1: Core Hardware Component
- [ ] Create `HW_USB_TTL.py` with `USBTTLHardware` class
- [ ] Implement `__init__`, `setup()`, `connect()`, `disconnect()` lifecycle methods
- [ ] Implement `send_ttl_signal(value)` method with 0x00-0xFF validation
- [ ] Add simulated mode with logging
- [ ] Create settings for port, baud rate, connection status

### Phase 2: Configuration Integration
- [ ] Add `hardware_ttl` section to `config.yaml`
- [ ] Update `Agency_Sensor_MAIN.py` to load TTL configuration
- [ ] Register `USBTTLHardware` in main app setup

### Phase 3: Testing Infrastructure
- [ ] Create `tests/` directory structure
- [ ] Write `pytest.ini` configuration
- [ ] Create `conftest.py` with shared fixtures
- [ ] Write `test_hw_usb_ttl.py` with unit tests

### Phase 4: Optional UI Component (User Story 3 - Priority P3)
- [ ] Create `UI_USB_TTL.py` for TTL signal monitoring
- [ ] Add real-time log display of sent signals
- [ ] Integrate with main app

### Phase 5: Event Integration Points
- [ ] Identify experimental events to mark in `UI_Experiment_Control.py`
- [ ] Add TTL signaling calls at appropriate points
- [ ] Define event code mapping (step numbers → hex values)

---

## 5. Open Questions & Future Work

**Resolved**:
- ✅ Baud rate: 115200 (from manual)
- ✅ Initialization: Send "RR" (from manual)
- ✅ Driver configuration: 1ms latency critical (from manual)
- ✅ Command format: 2-byte hex strings in CAPITALS (from manual)

**Future Enhancements** (out of current scope):
- TTL signal logging to HDF5 files alongside sensor data
- Event code configuration UI (instead of hardcoded mapping)
- Input signal reception for external triggering
- Multiple TTL modules support

---

## 6. References

**Official Documentation**:
- Black Box Toolkit USB TTL Module User Guide v1 (Rev. RC3, 20210330)
  - File: `D:\github\Lital_IMU_Tobii_Pro_Integration\User_Manuals\USBTTLv1r18.pdf`

**Codebase References**:
- `HW_MetaMotionRL.py` - Hardware component pattern reference
- `Agency_Sensor_MAIN.py` - Application setup pattern
- `config.yaml` - Configuration structure
- `environment.yml` - Python 3.10.15, pyserial 3.5

**External Resources**:
- FTDI VCP Drivers: https://ftdichip.com/drivers/vcp-drivers/
- PySerial Documentation: https://pyserial.readthedocs.io/
- ScopeFoundry Framework: (patterns from existing codebase)
- pytest Documentation: https://docs.pytest.org/

---

**Research Complete**: All technical questions resolved. Ready for `/speckit.tasks` phase.
