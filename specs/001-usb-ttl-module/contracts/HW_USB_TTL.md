# API Contract: HW_USB_TTL - USB TTL Module Hardware Component

**Feature Branch**: `001-usb-ttl-module` | **Date**: 2026-01-01
**Module**: `HW_USB_TTL.py`
**Base Class**: `ScopeFoundry.HardwareComponent`

## Overview

This contract defines the public API for the `USBTTLHardware` class, which implements the Black Box Toolkit USB TTL Module as a ScopeFoundry hardware component. The API follows the standard ScopeFoundry hardware lifecycle pattern and provides methods for TTL signal transmission to Tobii Pro instruments.

---

## Class: `USBTTLHardware`

**Inheritance**: `ScopeFoundry.HardwareComponent`

**Description**: Hardware abstraction for the Black Box Toolkit USB TTL Module, managing serial communication on a specified COM port and providing TTL event signaling capabilities with automatic fallback to simulated mode.

---

## Constructor

### `__init__(app, name=None, port='COM3')`

Initialize the USB TTL hardware component.

**Parameters**:
- `app` (`BaseMicroscopeApp`): The parent ScopeFoundry application instance
- `name` (`str`, optional): Component name for identification. Default: `"usb_ttl_module"`
- `port` (`str`, optional): Serial COM port identifier. Default: `"COM3"`

**Returns**: None

**Side Effects**:
- Stores reference to parent application
- Sets initial port configuration
- Calls parent `HardwareComponent.__init__()`

**Example**:
```python
from ScopeFoundry import BaseMicroscopeApp
from HW_USB_TTL import USBTTLHardware

app = BaseMicroscopeApp()
ttl_hw = USBTTLHardware(app, name="usb_ttl", port="COM3")
```

**Notes**:
- Must be called before any other methods
- Port can be overridden via settings after initialization

---

## Lifecycle Methods

### `setup()`

Configure hardware settings and register operations.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Creates `port` setting (LoggedQuantity, dtype=str, initial from constructor)
- Creates `baudrate` setting (read-only, fixed at 115200)
- Creates `connection_status` setting (read-only, dtype=str)
- Creates `simulated_mode` setting (read-only, dtype=bool)
- Registers `send_ttl_signal` operation
- Registers `reset_hardware` operation

**Example**:
```python
ttl_hw.setup()
# Settings now accessible via:
# ttl_hw.settings.port
# ttl_hw.settings.connection_status
```

**Notes**:
- Called automatically by ScopeFoundry framework during app initialization
- Must be called before `connect()`
- Settings are accessible via `self.settings.<setting_name>`

---

### `connect()`

Establish connection to USB TTL Module or enter simulated mode.

**Parameters**: None

**Returns**: `bool`
- `True`: Successfully connected to hardware
- `False`: Hardware unavailable, operating in simulated mode

**Raises**:
- `serial.SerialException`: If port is occupied or inaccessible (handled internally, switches to simulated mode)

**Side Effects**:
- Opens serial connection on `settings.port` with 115200 baud, 8N1 configuration
- Sends "RR" initialization command to hardware
- Sets `settings.connection_status` to "Connected" or "Simulated"
- Sets `settings.simulated_mode` to `True` or `False`
- Emits `status_changed` signal (if implemented)
- Logs connection status to application log

**Example**:
```python
success = ttl_hw.connect()
if success:
    print("Hardware connected")
else:
    print("Operating in simulated mode")

# Check status
status = ttl_hw.settings.connection_status.value  # "Connected" or "Simulated"
```

**Connection Algorithm**:
```
1. Read port from settings.port
2. Attempt serial.Serial(port, 115200, 8N1, timeout=5.0)
3. If successful:
   a. Write b'RR' (reset command)
   b. Wait 100ms for hardware initialization
   c. Set connection_status = "Connected"
   d. Set simulated_mode = False
   e. Return True
4. If exception (port unavailable, hardware not found):
   a. Log error details
   b. Set connection_status = "Simulated"
   c. Set simulated_mode = True
   d. Return False
```

**Notes**:
- **Non-blocking**: Must return within 5 seconds (connection timeout)
- **Graceful degradation**: Never raises exceptions to caller, always switches to simulated mode on failure
- **Thread-safe**: Can be called from PyQt UI thread
- Serial configuration: 115200 baud, 8 data bits, no parity, 1 stop bit (8N1)

---

### `disconnect()`

Close serial connection and release COM port.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Closes serial port if open
- Sets `settings.connection_status` to "Disconnected"
- Releases exclusive COM port lock
- Logs disconnection event

**Example**:
```python
ttl_hw.disconnect()
# Port is now available for other applications
```

**Notes**:
- Safe to call multiple times (idempotent)
- No-op in simulated mode (no physical connection to close)
- Called automatically by ScopeFoundry during app shutdown

---

## Operations (Public Methods)

### `send_ttl_signal(value)`

Send an 8-bit TTL event signal to Tobii Pro system.

**Parameters**:
- `value` (`int`): Hex value to transmit, range 0x00-0xFF (0-255 decimal)

**Returns**: `bool`
- `True`: Signal successfully transmitted (hardware) or logged (simulated)
- `False`: Transmission failed (invalid value or serial error)

**Raises**:
- `ValueError`: If `value` is outside range 0x00-0xFF

**Side Effects**:
- **Hardware Mode**: Writes 2-byte hex string to serial port (e.g., value=0x42 → writes b'42')
- **Simulated Mode**: Logs signal to console/file with timestamp
- Updates internal `last_signal_sent` and `last_signal_timestamp` attributes
- Logs transmission event

**Example**:
```python
# Send event marker for mobile stimulus activation
success = ttl_hw.send_ttl_signal(0x10)
if success:
    print("Signal sent successfully")

# Send baseline marker
ttl_hw.send_ttl_signal(0x00)

# Invalid value (raises ValueError)
try:
    ttl_hw.send_ttl_signal(256)  # Out of range
except ValueError as e:
    print(f"Invalid signal value: {e}")
```

**Transmission Protocol**:
```
1. Validate: 0x00 ≤ value ≤ 0xFF
2. Convert to 2-byte hex string: f"{value:02X}" (e.g., 66 → "42")
3. Encode to bytes: hex_string.encode('ascii')
4. Write to serial port with 100ms timeout
5. Log timestamp and value
6. Return True if bytes written == 2, else False
```

**Performance**:
- **Target latency**: <17ms from call to physical TTL output (60Hz eye-tracking sync)
- **Actual latency**: <5ms typical for hardware mode (serial write ~1ms + USB latency)
- **Blocking behavior**: Max 100ms write timeout, then returns False

**Notes**:
- **Uppercase hex required**: Hardware expects "42", not "42" (verified from manual)
- **No acknowledgment**: Fire-and-forget protocol, no response from hardware
- **Thread-safe**: Can be called from any thread (internally acquires serial port lock)
- **Simulated mode**: Always returns True (no actual transmission)

---

### `reset_hardware()`

Send reset command to USB TTL Module.

**Parameters**: None

**Returns**: `bool`
- `True`: Reset command sent successfully
- `False`: Reset failed (disconnected or simulated mode)

**Side Effects**:
- Writes "RR" command to serial port
- Reinitializes hardware to known state
- Logs reset event

**Example**:
```python
# Reinitialize hardware mid-session
ttl_hw.reset_hardware()
```

**Notes**:
- Only effective in hardware mode (no-op in simulated)
- Typically called during `connect()`, rarely needed manually
- Does not close/reopen serial connection

---

## Settings (LoggedQuantities)

Settings are accessible via `self.settings.<setting_name>` and automatically sync with the UI.

### `port` (Read/Write)

**Type**: `str`
**Initial Value**: From constructor (default: `"COM3"`)
**Description**: Serial COM port identifier for USB TTL Module
**Validation**: Must match pattern `COMx` where x is 1-999

**Example**:
```python
# Change port at runtime (requires reconnect)
ttl_hw.settings.port.update_value("COM5")
ttl_hw.disconnect()
ttl_hw.connect()
```

---

### `baudrate` (Read-Only)

**Type**: `int`
**Value**: `115200` (fixed)
**Description**: Serial communication speed (must not be changed)

**Example**:
```python
baud = ttl_hw.settings.baudrate.value  # Always 115200
```

---

### `connection_status` (Read-Only)

**Type**: `str`
**Values**: `"Connected"`, `"Disconnected"`, `"Simulated"`
**Description**: Current hardware connection state

**Example**:
```python
if ttl_hw.settings.connection_status.value == "Connected":
    print("Hardware ready")
```

---

### `simulated_mode` (Read-Only)

**Type**: `bool`
**Description**: Whether operating in simulated mode (hardware unavailable)

**Example**:
```python
if ttl_hw.settings.simulated_mode.value:
    print("Running without physical hardware")
```

---

## Internal Attributes (Not Part of Public API)

These attributes are implementation details and may change without notice:

- `serial_handle` (`serial.Serial`): Active serial connection object
- `last_signal_sent` (`int`): Most recent TTL value transmitted
- `last_signal_timestamp` (`float`): Unix timestamp of last transmission
- `_lock` (`threading.Lock`): Thread synchronization for serial access

**Note**: External code should not access these attributes directly.

---

## Integration with ScopeFoundry App

### Registration in `Agency_Sensor_MAIN.py`:

```python
from HW_USB_TTL import USBTTLHardware

class AgencySensor(BaseMicroscopeApp):
    def setup(self):
        # Register USB TTL hardware
        self.add_hardware(USBTTLHardware(self, port='COM3'))

        # Access later via:
        ttl_hw = self.hardware['usb_ttl_module']
        ttl_hw.send_ttl_signal(0x01)
```

### Integration with Experiment Control:

```python
# In UI_Experiment_Control.py, during experimental events
def on_mobile_stimulus_activated(self):
    ttl_hw = self.app.hardware['usb_ttl_module']
    ttl_hw.send_ttl_signal(0x10)  # Mobile stimulus event marker
```

---

## Error Handling

### Error Codes and Recovery

| Error Condition | Behavior | Recovery |
|----------------|----------|----------|
| Port unavailable at startup | Switch to simulated mode | Manual reconnect after freeing port |
| Hardware disconnected mid-session | Log error, continue in simulated | Automatic or manual reconnect |
| Invalid signal value (<0 or >255) | Raise `ValueError` | Caller handles exception |
| Serial write timeout | Return `False`, log error | Retry signal transmission |
| Port occupied by another app | Switch to simulated mode | Close other app, reconnect |

### Exception Handling Pattern:

```python
try:
    ttl_hw.send_ttl_signal(signal_value)
except ValueError as e:
    # Invalid signal value
    log.error(f"TTL signal error: {e}")
except Exception as e:
    # Unexpected error (should not happen)
    log.critical(f"Unexpected TTL error: {e}")
```

---

## Thread Safety

All public methods are thread-safe and can be called from:
- PyQt UI thread (main thread)
- Background measurement threads
- Timer callbacks

**Implementation**: Internal `threading.Lock` protects serial port access during write operations.

---

## Configuration via `config.yaml`

```yaml
hardware:
  usb_ttl_module:
    enabled: true
    port: "COM3"
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

**Usage**:
```python
# Load signal map from config
config = self.app.settings['config']
signal_value = config['hardware']['usb_ttl_module']['signal_map']['mobile_stimulus_on']
ttl_hw.send_ttl_signal(signal_value)
```

---

## Logging

All operations log to the ScopeFoundry application log:

**Log Levels**:
- `INFO`: Connection status changes, signal transmissions (if verbose logging enabled)
- `WARNING`: Simulated mode activation, connection failures
- `ERROR`: Serial write errors, invalid signal values
- `DEBUG`: Detailed serial communication (timestamps, hex values)

**Example Log Output**:
```
[2026-01-01 14:30:00 INFO] USBTTLHardware: Connecting to COM3...
[2026-01-01 14:30:01 INFO] USBTTLHardware: Hardware initialized successfully
[2026-01-01 14:30:01 INFO] USBTTLHardware: Connection status: Connected
[2026-01-01 14:35:12 INFO] USBTTLHardware: Sent TTL signal 0x10 (timestamp: 1735738512.345)
[2026-01-01 14:40:00 WARNING] USBTTLHardware: COM3 unavailable, switching to simulated mode
```

---

## Testing Interface

For unit testing, the class supports dependency injection:

```python
# Mock serial port for testing
from unittest.mock import MagicMock, patch

@patch('serial.Serial')
def test_send_ttl_signal(mock_serial):
    mock_instance = MagicMock()
    mock_instance.write.return_value = 2  # Simulate successful write
    mock_serial.return_value = mock_instance

    ttl_hw = USBTTLHardware(app, port='COM99')
    ttl_hw.connect()

    assert ttl_hw.send_ttl_signal(0x42) == True
    mock_instance.write.assert_called_with(b'42')
```

---

## Backwards Compatibility

This is a new hardware component (v1.0.0), no backwards compatibility concerns.

**Future Breaking Changes** (will increment major version):
- Changing method signatures (parameters, return types)
- Removing public methods or settings
- Changing serial protocol

**Non-Breaking Changes** (minor/patch versions):
- Adding new optional parameters with defaults
- Adding new methods or settings
- Internal implementation improvements

---

## Performance Benchmarks

Expected performance characteristics:

| Operation | Target | Typical | Notes |
|-----------|--------|---------|-------|
| `connect()` | <5s | 2-3s | Includes serial port open + initialization |
| `send_ttl_signal()` | <17ms | <5ms | Hardware mode, includes serial write |
| `send_ttl_signal()` | <1ms | <0.1ms | Simulated mode (logging only) |
| `disconnect()` | <1s | <100ms | Clean serial port closure |

---

## Related Documentation

- [Feature Specification](../spec.md)
- [Data Model](../data-model.md)
- [Research Findings](../research.md)
- [Quickstart Guide](../quickstart.md) (to be generated)
- [ScopeFoundry Hardware Component Documentation](http://www.scopefoundry.org/docs/)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial API contract for USB TTL Module integration |

---

## Contract Compliance

Implementations of this class MUST:
- Inherit from `ScopeFoundry.HardwareComponent`
- Implement all lifecycle methods (`setup`, `connect`, `disconnect`)
- Provide `send_ttl_signal(value)` method with specified signature
- Support automatic fallback to simulated mode
- Validate signal values in range 0x00-0xFF
- Use 115200 baud serial communication
- Be thread-safe for all public methods

Implementations MAY:
- Add additional methods for extended functionality
- Provide UI components (separate `UI_USB_TTL.py` module)
- Log additional diagnostic information
- Optimize internal serial communication buffering

Implementations MUST NOT:
- Block UI thread for >100ms
- Crash application on hardware errors
- Modify global state outside of settings
- Use different serial protocol than specified
