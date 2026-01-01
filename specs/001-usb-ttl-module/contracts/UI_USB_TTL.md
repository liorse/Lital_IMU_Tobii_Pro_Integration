# API Contract: UI_USB_TTL - USB TTL Module UI Component (Optional)

**Feature Branch**: `001-usb-ttl-module` | **Date**: 2026-01-01
**Module**: `UI_USB_TTL.py`
**Base Class**: `ScopeFoundry.Measurement`
**Priority**: P3 (Optional - User Story 3)

## Overview

This contract defines the public API for the `USBTTLMonitorUI` class, which provides a PyQt5-based user interface for monitoring TTL signal activity in real-time. This component is **optional** and implements User Story 3 (Monitor TTL Signal Activity).

**Note**: The core USB TTL functionality (connection and signal transmission) works without this UI component. This is purely for monitoring and debugging purposes.

---

## Class: `USBTTLMonitorUI`

**Inheritance**: `ScopeFoundry.Measurement`

**Description**: User interface for monitoring USB TTL Module connection status and signal transmission activity. Displays real-time log of TTL events with timestamps and provides manual signal testing capabilities.

---

## Constructor

### `__init__(app)`

Initialize the USB TTL monitoring UI component.

**Parameters**:
- `app` (`BaseMicroscopeApp`): The parent ScopeFoundry application instance

**Returns**: None

**Side Effects**:
- Stores reference to parent application
- Calls parent `Measurement.__init__()`

**Example**:
```python
from ScopeFoundry import BaseMicroscopeApp
from UI_USB_TTL import USBTTLMonitorUI

app = BaseMicroscopeApp()
ttl_ui = USBTTLMonitorUI(app)
```

---

## Lifecycle Methods

### `setup()`

Configure UI settings and initialize signal log buffer.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Creates `max_log_entries` setting (int, default 1000)
- Creates `enable_logging` setting (bool, default True)
- Initializes internal signal history buffer (deque with maxlen=1000)
- Connects to hardware component's signal emissions

**Example**:
```python
ttl_ui.setup()
# Settings accessible via:
# ttl_ui.settings.max_log_entries
# ttl_ui.settings.enable_logging
```

**Notes**:
- Called automatically by ScopeFoundry framework
- Must be called before `setup_figure()`

---

### `setup_figure()`

Build PyQt5 user interface widgets.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Creates QGroupBox titled "USB TTL Module Monitor"
- Adds status indicator (QLabel) showing connection state
- Adds signal activity log (QTextEdit, read-only, monospace font)
- Adds manual test controls:
  - Signal value input (QSpinBox, range 0-255)
  - "Send Test Signal" button
  - "Reset Hardware" button
  - "Clear Log" button
- Connects hardware status changes to UI updates

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ USB TTL Module Monitor                  │
├─────────────────────────────────────────┤
│ Status: [Connected] (green indicator)   │
├─────────────────────────────────────────┤
│ Signal Activity Log:                    │
│ ┌─────────────────────────────────────┐ │
│ │ [14:30:45.123] 0x10 → SENT (2.3ms) │ │
│ │ [14:30:47.654] 0x11 → SENT (1.8ms) │ │
│ │ [14:30:50.001] 0x20 → SENT (2.1ms) │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ Manual Test:                            │
│ Signal Value: [042] (hex)               │
│ [Send Test Signal] [Reset Hardware]     │
│ [Clear Log]                             │
└─────────────────────────────────────────┘
```

**Example**:
```python
ttl_ui.setup_figure()
# UI widgets now available in self.ui
```

**Notes**:
- Called automatically by ScopeFoundry framework after `setup()`
- Creates all Qt widgets and connections
- Updates automatically via PyQt signals

---

### `update_display()`

Refresh UI widgets with current hardware state (called periodically).

**Parameters**: None

**Returns**: None

**Side Effects**:
- Updates status indicator color/text based on connection state
- Appends new signal events to activity log
- Manages log size (removes old entries if >max_log_entries)

**Update Frequency**: ~10Hz (100ms timer, configurable)

**Example**:
```python
# Called automatically by framework, but can be invoked manually
ttl_ui.update_display()
```

**Notes**:
- Non-blocking, executes quickly (<1ms typical)
- Only updates if new signals detected or status changed

---

## UI Components (Accessible via `self.ui`)

### `status_label` (QLabel)

**Description**: Displays current connection status with color-coded indicator

**States**:
- **Connected**: Green circle ● + "Connected to COM3"
- **Disconnected**: Red circle ● + "Disconnected"
- **Simulated**: Yellow circle ● + "Simulated Mode (hardware unavailable)"

**Example**:
```python
# Programmatically update status (typically done via signals)
self.ui.status_label.setText("● Connected to COM3")
self.ui.status_label.setStyleSheet("color: green;")
```

---

### `activity_log` (QTextEdit)

**Description**: Read-only scrollable log of TTL signal transmissions

**Format**: `[HH:MM:SS.mmm] 0xVV → STATUS (latency_ms)`

**Example Entries**:
```
[14:30:45.123] 0x10 → SENT (2.3ms)
[14:30:47.654] 0x11 → SENT (1.8ms)
[14:30:50.001] 0xFF → FAILED (timeout)
```

**Behavior**:
- Auto-scrolls to bottom on new entries
- Monospace font for alignment
- Preserves last 1000 entries (configurable via `max_log_entries`)
- Displays "(SIMULATED)" suffix in simulated mode

**Example**:
```python
# Programmatically add log entry (typically done via signal handler)
self.ui.activity_log.append("[14:30:45.123] 0x42 → SENT (1.5ms)")
```

---

### `test_value_spinbox` (QSpinBox)

**Description**: Input field for manual signal testing

**Range**: 0-255 (0x00-0xFF)
**Display**: Hexadecimal (e.g., "042" for value 66)
**Default**: 0

**Example**:
```python
# Get current test value
test_value = self.ui.test_value_spinbox.value()  # Returns int (0-255)
```

---

### `send_test_button` (QPushButton)

**Description**: Manually trigger TTL signal transmission with test value

**Behavior**:
- Reads value from `test_value_spinbox`
- Calls `hardware.send_ttl_signal(value)`
- Logs result to activity log

**Click Handler**:
```python
def on_send_test_clicked(self):
    value = self.ui.test_value_spinbox.value()
    hw = self.app.hardware['usb_ttl_module']
    success = hw.send_ttl_signal(value)
    if success:
        self.log_signal(value, "SENT (manual test)")
    else:
        self.log_signal(value, "FAILED")
```

---

### `reset_button` (QPushButton)

**Description**: Send reset command to hardware (RR command)

**Behavior**:
- Calls `hardware.reset_hardware()`
- Logs reset event to activity log
- Disabled in simulated mode

**Click Handler**:
```python
def on_reset_clicked(self):
    hw = self.app.hardware['usb_ttl_module']
    if hw.reset_hardware():
        self.log_message("Hardware reset successful")
    else:
        self.log_message("Reset failed (simulated mode or disconnected)")
```

---

### `clear_log_button` (QPushButton)

**Description**: Clear all entries from activity log

**Behavior**:
- Clears `activity_log` QTextEdit
- Clears internal signal history buffer

**Click Handler**:
```python
def on_clear_log_clicked(self):
    self.ui.activity_log.clear()
    self.signal_history.clear()
```

---

## Public Methods

### `log_signal(value, status, latency_ms=None)`

Append a signal transmission event to the activity log.

**Parameters**:
- `value` (`int`): TTL signal value (0-255)
- `status` (`str`): Transmission outcome ("SENT", "FAILED", "SENT (SIMULATED)")
- `latency_ms` (`float`, optional): Transmission latency in milliseconds

**Returns**: None

**Side Effects**:
- Appends formatted entry to `activity_log`
- Stores event in internal history buffer

**Example**:
```python
ttl_ui.log_signal(0x42, "SENT", latency_ms=2.3)
# Output: [14:30:45.123] 0x42 → SENT (2.3ms)

ttl_ui.log_signal(0xFF, "FAILED")
# Output: [14:30:50.001] 0xFF → FAILED
```

**Format**: `[timestamp] 0x{value:02X} → {status} ({latency}ms)`

---

### `log_message(message)`

Append a general message to the activity log.

**Parameters**:
- `message` (`str`): Message text

**Returns**: None

**Example**:
```python
ttl_ui.log_message("Hardware reset successful")
# Output: [14:30:55.678] Hardware reset successful
```

---

## Signal Handlers (Internal)

These methods are connected to hardware component signals:

### `on_hardware_status_changed(status_code, message)`

**Triggered By**: Hardware component's `status_changed` signal

**Behavior**:
- Updates `status_label` with new connection state
- Logs status change to activity log

---

### `on_signal_sent(value, latency_ms)`

**Triggered By**: Hardware component's `signal_sent` signal (if implemented)

**Behavior**:
- Calls `log_signal(value, "SENT", latency_ms)`

---

## Settings

### `max_log_entries` (Read/Write)

**Type**: `int`
**Default**: `1000`
**Description**: Maximum number of entries to keep in activity log

**Example**:
```python
# Increase log buffer size
ttl_ui.settings.max_log_entries.update_value(5000)
```

---

### `enable_logging` (Read/Write)

**Type**: `bool`
**Default**: `True`
**Description**: Whether to log signal transmissions to activity log

**Example**:
```python
# Temporarily disable logging for performance
ttl_ui.settings.enable_logging.update_value(False)
```

---

## Integration with ScopeFoundry App

### Registration in `Agency_Sensor_MAIN.py`:

```python
from UI_USB_TTL import USBTTLMonitorUI

class AgencySensor(BaseMicroscopeApp):
    def setup(self):
        # Register USB TTL hardware (required)
        self.add_hardware(USBTTLHardware(self, port='COM3'))

        # Register USB TTL monitoring UI (optional)
        self.add_measurement(USBTTLMonitorUI(self))
```

**Access**:
```python
# Access UI component
ttl_ui = self.app.measurements['usb_ttl_monitor_ui']
ttl_ui.log_signal(0x10, "SENT", 2.5)
```

---

## Thread Safety

All public methods should be called from the **PyQt main thread** (UI thread).

**Signal Handlers**: Automatically executed on main thread via Qt's signal/slot mechanism.

**Cross-Thread Logging**: If logging from background threads, use Qt signals:
```python
from PyQt5.QtCore import pyqtSignal

class BackgroundWorker(QThread):
    signal_sent_signal = pyqtSignal(int, float)  # value, latency_ms

    def run(self):
        # Background work
        self.signal_sent_signal.emit(0x42, 2.3)

# In UI class, connect signal
worker.signal_sent_signal.connect(self.log_signal)
```

---

## Performance Considerations

### Memory Usage

- **Signal history buffer**: ~1KB per 1000 entries (default)
- **QTextEdit widget**: Minimal overhead (Qt handles efficiently)

### UI Responsiveness

- **Update frequency**: 10Hz (avoids excessive repainting)
- **Log appends**: Non-blocking, <0.1ms per entry
- **Auto-scroll**: Deferred until next paint cycle

---

## Configuration via `config.yaml`

```yaml
ui:
  usb_ttl_monitor:
    enabled: true  # Set to false to hide UI panel
    max_log_entries: 1000
    update_interval_ms: 100
```

---

## Testing Interface

For UI testing, use Qt Test framework:

```python
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

def test_manual_signal_send(qtbot):
    ttl_ui = USBTTLMonitorUI(app)
    ttl_ui.setup()
    ttl_ui.setup_figure()

    # Set test value
    ttl_ui.ui.test_value_spinbox.setValue(0x42)

    # Click send button
    QTest.mouseClick(ttl_ui.ui.send_test_button, Qt.LeftButton)

    # Verify log entry
    log_text = ttl_ui.ui.activity_log.toPlainText()
    assert "0x42 → SENT" in log_text
```

---

## Accessibility

- **Keyboard Navigation**: All controls accessible via Tab key
- **Screen Reader Support**: Status labels have descriptive text
- **Color Blindness**: Status uses both color and text indicators

---

## Known Limitations

1. **Log Search**: No built-in search/filter functionality (future enhancement)
2. **Export**: No CSV/file export of signal log (can be added later)
3. **Graphical Visualization**: No waveform display (out of scope)

---

## Related Documentation

- [Feature Specification](../spec.md) - User Story 3
- [Hardware API Contract](HW_USB_TTL.md)
- [Data Model](../data-model.md)
- [Quickstart Guide](../quickstart.md)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial API contract for USB TTL monitoring UI |

---

## Contract Compliance

Implementations of this class MUST:
- Inherit from `ScopeFoundry.Measurement`
- Display real-time connection status
- Provide activity log with timestamps and signal values
- Support manual signal testing
- Be thread-safe (all UI updates on main thread)

Implementations MAY:
- Add export functionality for signal logs
- Provide filtering/search capabilities
- Display graphical visualizations (waveforms, histograms)
- Support custom log formatting

Implementations MUST NOT:
- Block UI thread for >100ms
- Modify hardware settings without user action
- Log sensitive experimental data to UI (only TTL values and timestamps)
