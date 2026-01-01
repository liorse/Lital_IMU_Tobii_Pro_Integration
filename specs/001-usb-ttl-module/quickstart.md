# Quickstart Guide: USB TTL Module Integration

**Feature Branch**: `001-usb-ttl-module` | **Date**: 2026-01-01
**Time to Complete**: 30-45 minutes (excluding driver configuration)

## Overview

This guide walks you through implementing the USB TTL Module integration from start to finish. By the end, you'll have a working ScopeFoundry hardware component that sends TTL event signals to Tobii Pro instruments.

---

## Prerequisites

### Required Hardware
- **Black Box Toolkit USB TTL Module** (connected to USB port)
- **Tobii Pro eye-tracking instrument** (configured to receive TTL input)
- Windows 10+ computer with available COM port

### Required Software
- **Python 3.10.15** (verify: `python --version`)
- **Conda environment**: `lital` (see `environment.yml`)
- **FTDI VCP Drivers** installed (verify in Device Manager)
- **pyserial 3.5+** (already in environment.yml)

### Knowledge Requirements
- Familiarity with ScopeFoundry framework
- Basic PyQt5 understanding
- Serial communication concepts

---

## Step 1: Verify Hardware Connection (10 minutes)

### 1.1 Connect USB TTL Module

1. Plug USB TTL Module into Windows computer
2. Open **Device Manager** → **Ports (COM & LPT)**
3. Identify COM port number (e.g., COM3, COM5)
4. Note the port number for later use

**Troubleshooting**:
- If no COM port appears: Install FTDI VCP drivers from [ftdichip.com](https://ftdichip.com/drivers/vcp-drivers/)
- If port shows "Error": Check USB cable and try different USB port

### 1.2 Configure FTDI Driver Latency (CRITICAL)

The USB TTL Module requires **1ms latency** for sub-17ms signal timing:

1. Open **Device Manager** → **Ports (COM & LPT)**
2. Right-click on "USB Serial Port (COMX)" → **Properties**
3. Go to **Port Settings** tab → **Advanced**
4. Set **Latency Timer**: `1 ms` (default is 16ms - too slow!)
5. Click **OK** to save

**Why this matters**: Default 16ms latency causes signals to batch, breaking Tobii Pro synchronization.

### 1.3 Test Serial Communication (Optional)

Use a serial terminal to verify hardware:

```bash
# Using pyserial-miniterm (already in environment)
python -m serial.tools.miniterm COM3 115200

# You should see connection open
# Type: RR (reset command)
# Hardware should respond with initialization (LEDs blink)
# Ctrl+] to exit
```

---

## Step 2: Create Hardware Component (15 minutes)

### 2.1 Create `HW_USB_TTL.py`

Create new file at repository root:

```python
# HW_USB_TTL.py
"""
USB TTL Module Hardware Component for Tobii Pro Event Signaling
Black Box Toolkit USB TTL Module integration via ScopeFoundry
"""

import serial
import time
import logging
from ScopeFoundry import HardwareComponent

log = logging.getLogger(__name__)


class USBTTLHardware(HardwareComponent):
    """
    ScopeFoundry hardware component for Black Box Toolkit USB TTL Module.

    Provides 8-bit TTL event signaling (0x00-0xFF) for Tobii Pro synchronization.
    Automatically falls back to simulated mode if hardware unavailable.
    """

    name = 'usb_ttl_module'

    def __init__(self, app, name=None, port='COM3'):
        """
        Initialize USB TTL hardware component.

        Args:
            app: ScopeFoundry BaseMicroscopeApp instance
            name: Optional component name override
            port: Serial COM port (default: COM3)
        """
        self.port = port
        self.serial_handle = None
        self.last_signal_sent = None
        self.last_signal_timestamp = None
        HardwareComponent.__init__(self, app, name=name)

    def setup(self):
        """Configure settings and register operations."""
        # Settings
        self.settings.New(name='port', dtype=str, initial=self.port,
                          description='Serial COM port')
        self.settings.New(name='baudrate', dtype=int, initial=115200,
                          ro=True, description='Serial baudrate (fixed)')
        self.settings.New(name='connection_status', dtype=str,
                          initial='Disconnected', ro=True,
                          description='Hardware connection state')
        self.settings.New(name='simulated_mode', dtype=bool,
                          initial=False, ro=True,
                          description='Operating without physical hardware')

        # Operations (callable from UI or other measurements)
        self.add_operation(name='send_ttl_signal', op_func=self.send_ttl_signal)
        self.add_operation(name='reset_hardware', op_func=self.reset_hardware)

    def connect(self):
        """
        Establish connection to USB TTL Module.

        Returns:
            bool: True if hardware connected, False if simulated mode
        """
        port = self.settings['port']
        log.info(f"USBTTLHardware: Attempting connection to {port}...")

        try:
            # Open serial port with 115200 baud, 8N1 configuration
            self.serial_handle = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=5.0,          # 5 second read timeout
                write_timeout=0.1,    # 100ms write timeout (non-blocking)
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )

            # Send reset command to initialize hardware
            time.sleep(0.1)  # Brief delay for port stabilization
            self.serial_handle.write(b'RR')
            time.sleep(0.1)  # Wait for hardware initialization

            # Update status
            self.settings['connection_status'] = 'Connected'
            self.settings['simulated_mode'] = False
            log.info(f"USBTTLHardware: Connected to {port} successfully")

            # Disconnect settings from hardware (prevent auto-update during session)
            self.settings.disconnect_all_from_hardware()

            return True

        except (serial.SerialException, OSError) as e:
            # Hardware unavailable - switch to simulated mode
            log.warning(f"USBTTLHardware: {port} unavailable ({e}), switching to SIMULATED mode")
            self.serial_handle = None
            self.settings['connection_status'] = 'Simulated'
            self.settings['simulated_mode'] = True

            return False

    def disconnect(self):
        """Close serial connection and release COM port."""
        if self.serial_handle and self.serial_handle.is_open:
            self.serial_handle.close()
            log.info("USBTTLHardware: Serial port closed")

        self.serial_handle = None
        self.settings['connection_status'] = 'Disconnected'

    def send_ttl_signal(self, value):
        """
        Send 8-bit TTL event signal to Tobii Pro.

        Args:
            value (int): Hex value 0x00-0xFF (0-255 decimal)

        Returns:
            bool: True if sent successfully, False otherwise

        Raises:
            ValueError: If value outside valid range
        """
        # Validate input
        if not isinstance(value, int) or value < 0x00 or value > 0xFF:
            raise ValueError(f"TTL signal value must be 0x00-0xFF, got {value}")

        # Convert to 2-byte uppercase hex string (hardware requirement)
        hex_string = f"{value:02X}"

        timestamp = time.time()

        # Hardware mode: transmit via serial
        if self.serial_handle and self.serial_handle.is_open:
            try:
                bytes_written = self.serial_handle.write(hex_string.encode('ascii'))

                if bytes_written == 2:
                    latency_ms = (time.time() - timestamp) * 1000
                    self.last_signal_sent = value
                    self.last_signal_timestamp = timestamp
                    log.debug(f"USBTTLHardware: Sent 0x{hex_string} ({latency_ms:.2f}ms)")
                    return True
                else:
                    log.error(f"USBTTLHardware: Serial write incomplete ({bytes_written}/2 bytes)")
                    return False

            except serial.SerialTimeoutException:
                log.error("USBTTLHardware: Serial write timeout")
                return False
            except Exception as e:
                log.error(f"USBTTLHardware: Serial write error: {e}")
                return False

        # Simulated mode: log only
        else:
            self.last_signal_sent = value
            self.last_signal_timestamp = timestamp
            log.info(f"USBTTLHardware: [SIMULATED] Signal 0x{hex_string}")
            return True

    def reset_hardware(self):
        """
        Send reset command (RR) to USB TTL Module.

        Returns:
            bool: True if reset successful, False otherwise
        """
        if self.serial_handle and self.serial_handle.is_open:
            try:
                self.serial_handle.write(b'RR')
                log.info("USBTTLHardware: Hardware reset command sent")
                return True
            except Exception as e:
                log.error(f"USBTTLHardware: Reset failed: {e}")
                return False
        else:
            log.warning("USBTTLHardware: Cannot reset (disconnected or simulated)")
            return False
```

**Key Implementation Notes**:
- **Uppercase hex**: Hardware requires "42", not "42"
- **2-byte format**: Always send exactly 2 ASCII characters
- **Graceful degradation**: Never crashes, always switches to simulated mode
- **Non-blocking writes**: 100ms timeout prevents UI freezing

---

## Step 3: Integrate with Main Application (10 minutes)

### 3.1 Register Hardware in `Agency_Sensor_MAIN.py`

Add to the `AgencySensor.setup()` method:

```python
# Agency_Sensor_MAIN.py

from HW_USB_TTL import USBTTLHardware  # Add import at top

class AgencySensor(BaseMicroscopeApp):

    name = 'agency_sensor'

    def setup(self):
        # ... existing hardware setup ...

        # Add USB TTL Module hardware
        self.add_hardware(USBTTLHardware(self, port='COM3'))

        # ... rest of setup ...
```

**Port Configuration**: Change `port='COM3'` to match your hardware's COM port.

### 3.2 Add Configuration to `config.yaml`

Add new section under `hardware`:

```yaml
hardware:
  # ... existing hardware ...

  usb_ttl_module:
    enabled: true
    port: "COM3"  # Change to your COM port
    timeout_seconds: 5
    fallback_to_simulated: true

    # Optional: Signal mapping for experimental events
    signal_map:
      experiment_start: 0x01
      experiment_stop: 0x02
      mobile_stimulus_on: 0x10
      mobile_stimulus_off: 0x11
      baseline_start: 0x20
      baseline_end: 0x21
```

---

## Step 4: Send TTL Signals from Experiments (5 minutes)

### 4.1 Example: Send Signal During Mobile Stimulus

In `UI_Mobile_Control.py` or `UI_Experiment_Control.py`:

```python
def on_mobile_activated(self):
    """Called when mobile stimulus starts playing."""
    # Get TTL hardware component
    ttl_hw = self.app.hardware.get('usb_ttl_module')

    if ttl_hw:
        # Send mobile stimulus start signal
        ttl_hw.send_ttl_signal(0x10)  # 0x10 = mobile stimulus ON

    # ... rest of mobile activation code ...

def on_mobile_deactivated(self):
    """Called when mobile stimulus stops playing."""
    ttl_hw = self.app.hardware.get('usb_ttl_module')

    if ttl_hw:
        ttl_hw.send_ttl_signal(0x11)  # 0x11 = mobile stimulus OFF

    # ... rest of mobile deactivation code ...
```

### 4.2 Using Signal Map from Config

```python
def send_event_signal(self, event_name):
    """Send TTL signal based on config.yaml signal_map."""
    ttl_hw = self.app.hardware.get('usb_ttl_module')

    # Load signal value from config
    config = self.app.settings['config']
    signal_map = config['hardware']['usb_ttl_module']['signal_map']
    signal_value = signal_map.get(event_name)

    if signal_value is not None and ttl_hw:
        ttl_hw.send_ttl_signal(signal_value)

# Usage:
send_event_signal('experiment_start')  # Sends 0x01
send_event_signal('mobile_stimulus_on')  # Sends 0x10
```

---

## Step 5: Test the Integration (10 minutes)

### 5.1 Basic Connectivity Test

```bash
# Activate conda environment
conda activate lital

# Run application
python Agency_Sensor_MAIN.py
```

**Expected Output**:
```
[INFO] USBTTLHardware: Attempting connection to COM3...
[INFO] USBTTLHardware: Connected to COM3 successfully
[INFO] USBTTLHardware: Hardware initialized
```

**If Simulated Mode**:
```
[WARNING] USBTTLHardware: COM3 unavailable (...), switching to SIMULATED mode
```

### 5.2 Manual Signal Test (Python Console)

```python
# In Python console or test script
from Agency_Sensor_MAIN import AgencySensor

app = AgencySensor()
app.setup()
app.hardware['usb_ttl_module'].connect()

# Send test signal
app.hardware['usb_ttl_module'].send_ttl_signal(0x42)
# Expected log: [DEBUG] USBTTLHardware: Sent 0x42 (2.3ms)

# Verify on Tobii Pro recording that signal 0x42 appears with timestamp
```

### 5.3 Timing Verification

Measure signal transmission latency:

```python
import time

ttl_hw = app.hardware['usb_ttl_module']

start = time.time()
ttl_hw.send_ttl_signal(0x10)
latency_ms = (time.time() - start) * 1000

print(f"Signal latency: {latency_ms:.2f}ms")
# Target: <17ms for 60Hz eye-tracking sync
# Typical: 2-5ms in hardware mode
```

---

## Step 6: (Optional) Add Monitoring UI (15 minutes)

For User Story 3 (Monitor TTL Signal Activity), implement `UI_USB_TTL.py`:

See [UI API Contract](contracts/UI_USB_TTL.md) for full implementation details.

**Quick Integration**:
```python
# In Agency_Sensor_MAIN.py
from UI_USB_TTL import USBTTLMonitorUI  # After implementing UI_USB_TTL.py

class AgencySensor(BaseMicroscopeApp):
    def setup(self):
        # ... hardware setup ...

        # Add monitoring UI (optional)
        self.add_measurement(USBTTLMonitorUI(self))
```

---

## Common Issues & Solutions

### Issue 1: "COM3 unavailable" at startup

**Cause**: Port occupied by another application or incorrect port number

**Solution**:
1. Close other serial monitor applications (Arduino IDE, PuTTY, etc.)
2. Verify COM port in Device Manager
3. Update `port` parameter in `Agency_Sensor_MAIN.py` or `config.yaml`

### Issue 2: Signals transmitted but not appearing in Tobii Pro

**Cause**: Tobii Pro not configured to receive TTL input

**Solution**:
1. Check Tobii Pro hardware manual for TTL input configuration
2. Verify physical cable connection between USB TTL Module and Tobii Pro
3. Ensure Tobii Pro recording is active when signals are sent

### Issue 3: High latency (>17ms)

**Cause**: FTDI driver latency set to default 16ms

**Solution**:
1. Follow **Step 1.2** to set latency to 1ms in Device Manager
2. Reconnect USB TTL Module (unplug/replug USB)
3. Restart application

### Issue 4: `ValueError: TTL signal value must be 0x00-0xFF`

**Cause**: Invalid signal value passed to `send_ttl_signal()`

**Solution**:
```python
# Incorrect:
ttl_hw.send_ttl_signal(256)  # Out of range!
ttl_hw.send_ttl_signal("0x42")  # String, not int!

# Correct:
ttl_hw.send_ttl_signal(0x42)  # Hex notation (66 decimal)
ttl_hw.send_ttl_signal(66)    # Decimal notation (same as 0x42)
```

### Issue 5: Simulated mode even with hardware connected

**Cause**: Driver not installed or COM port permissions

**Solution**:
1. Install FTDI VCP drivers: https://ftdichip.com/drivers/vcp-drivers/
2. Run application as Administrator (right-click → Run as administrator)
3. Check Windows Device Manager for driver errors (yellow exclamation mark)

---

## Testing Checklist

Before considering implementation complete, verify:

- [ ] Hardware connects successfully at application startup (log shows "Connected")
- [ ] Simulated mode activates when hardware unplugged (log shows "Simulated")
- [ ] Manual signal test: `send_ttl_signal(0x42)` completes in <17ms
- [ ] Signal appears in Tobii Pro recording timeline with correct timestamp
- [ ] Rapid signal sequence (10 signals in 1 second) all transmitted in order
- [ ] Application continues operating when hardware disconnected mid-session
- [ ] Config.yaml signal_map values correctly map to experimental events
- [ ] Invalid signal values (e.g., 256) raise ValueError
- [ ] 2+ hour experimental session runs without connection drops

---

## Next Steps

### Minimum Viable Product (MVP)
- [x] Step 1-3: Core hardware integration (User Story 1 & 2)
- [ ] Integration with experimental protocol (`UI_Experiment_Control.py`)
- [ ] Testing with live Tobii Pro session

### Optional Enhancements
- [ ] Implement monitoring UI (`UI_USB_TTL.py` - User Story 3)
- [ ] Log TTL signals to CSV for offline analysis
- [ ] Add signal history to HDF5 experimental data files

### Future Work (Out of Scope for v1)
- Bidirectional TTL communication (receive signals from Tobii Pro)
- Graphical waveform visualization
- Auto-detection of COM port (dynamic port scanning)

---

## Performance Benchmarks

Expected timing characteristics:

| Metric | Target | Typical | Notes |
|--------|--------|---------|-------|
| Connection time | <5s | 2-3s | Startup to "Connected" status |
| Signal latency (hardware) | <17ms | 2-5ms | Call to physical output |
| Signal latency (simulated) | <1ms | <0.1ms | Logging only |
| Throughput | 100 signals/sec | Unlimited | Limited by Tobii Pro, not USB TTL |

---

## Support & Documentation

- **Feature Specification**: [spec.md](spec.md)
- **Data Model**: [data-model.md](data-model.md)
- **API Contracts**: [contracts/HW_USB_TTL.md](contracts/HW_USB_TTL.md)
- **Research Findings**: [research.md](research.md)
- **USB TTL Module Manual**: `User_Manuals/USBTTLv1r18.pdf`
- **ScopeFoundry Documentation**: http://www.scopefoundry.org/docs/

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial quickstart guide for USB TTL Module integration |

---

**Estimated Time Investment**:
- Minimum (Steps 1-3): 30-45 minutes
- With UI (Steps 1-6): 60-75 minutes
- Full testing and validation: +30 minutes

**Success Criteria**: Application launches successfully, TTL signals appear in Tobii Pro timeline with sub-17ms precision, and system operates stably for 2+ hour sessions.
