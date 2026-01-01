# Data Model: USB TTL Module Integration for Tobii Pro Event Signaling

**Feature Branch**: `001-usb-ttl-module` | **Date**: 2026-01-01
**Input**: [spec.md](spec.md), [research.md](research.md)

## Overview

This document defines the data model for the USB TTL Module integration, describing the key entities, their attributes, relationships, state transitions, and data flow patterns. The model follows the ScopeFoundry hardware abstraction pattern and ensures compatibility with the existing PyQt5-based experimental control application.

## Core Entities

### 1. USB TTL Hardware Component

**Description**: The primary hardware abstraction representing the Black Box Toolkit USB TTL Module as a ScopeFoundry `HardwareComponent`.

**Attributes**:

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `name` | String | Component identifier | Unique within application |
| `port` | String | Serial COM port identifier | Valid COM port (e.g., "COM3") |
| `baudrate` | Integer | Serial communication speed | Fixed at 115200 |
| `connection_status` | Enum | Current hardware state | One of: {DISCONNECTED, CONNECTED, SIMULATED} |
| `serial_handle` | SerialPort | Active serial connection | Null when disconnected/simulated |
| `last_signal_sent` | Integer | Most recent TTL value | Range: 0x00-0xFF, null if none sent |
| `last_signal_timestamp` | Timestamp | Time of last transmission | ISO 8601 format |
| `initialization_state` | Enum | Hardware init status | One of: {UNINITIALIZED, READY, FAILED} |

**Lifecycle States**:
- **UNINITIALIZED**: Component created but not configured
- **DISCONNECTED**: Component configured but not connected to hardware
- **CONNECTED**: Successfully connected to physical hardware on specified port
- **SIMULATED**: Operating in software-only mode (hardware unavailable)
- **FAILED**: Connection attempt failed, requires manual intervention

**Operations**:
- `connect()`: Establish connection to hardware or enter simulated mode
- `disconnect()`: Close serial connection and release port
- `send_ttl_signal(value)`: Transmit 8-bit hex value to Tobii Pro
- `reset_hardware()`: Send initialization command to USB TTL Module
- `validate_signal(value)`: Check if value is within 0x00-0xFF range

---

### 2. TTL Event Signal

**Description**: A discrete event marker transmitted to the Tobii Pro system for experimental event synchronization.

**Attributes**:

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `signal_value` | Integer (hex) | 8-bit event identifier | Range: 0x00-0xFF (0-255 decimal) |
| `timestamp` | Timestamp | Transmission time | High-precision (microsecond) |
| `source_event` | String | Experimental event that triggered signal | Optional, for logging |
| `transmission_mode` | Enum | Hardware or simulated | One of: {HARDWARE, SIMULATED} |
| `transmission_status` | Enum | Success/failure state | One of: {PENDING, SENT, FAILED} |
| `latency_ms` | Float | Time from trigger to transmission | Target: <17ms for 60Hz sync |

**Signal Value Semantics** (Example Convention):
- `0x00`: Reserved for baseline/no-event marker
- `0x01-0x0F`: System events (start/stop experiment, calibration)
- `0x10-0x7F`: Experimental stimulus events
- `0x80-0xFE`: Participant response events
- `0xFF`: Reserved for error/diagnostic signals

*Note: Actual signal mapping will be defined in `config.yaml` for flexibility.*

**State Transitions**:
```
PENDING → SENT (successful transmission)
PENDING → FAILED (serial write error, timeout)
```

---

### 3. Hardware Status

**Description**: The operational state of the USB TTL Module, tracking connection health and mode.

**Attributes**:

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `status_code` | Enum | Connection state | One of: {CONNECTED, DISCONNECTED, SIMULATED} |
| `status_message` | String | Human-readable description | Max 256 characters |
| `last_updated` | Timestamp | Last status change | ISO 8601 format |
| `error_details` | String | Diagnostic information | Null if no error, max 1024 chars |
| `connection_attempts` | Integer | Retry count | Increments on failed connects |
| `hardware_detected` | Boolean | Physical device presence | False in simulated mode |

**Status Definitions**:
- **CONNECTED**: Serial port open, hardware initialized (RR command successful)
- **DISCONNECTED**: Port not accessible or connection not established
- **SIMULATED**: Operating without physical hardware, all signals logged only

**PyQt Signal Emissions**:
- `status_changed(status_code, message)`: Emitted when connection state transitions
- `error_occurred(error_details)`: Emitted on connection or transmission errors

---

## Entity Relationships

```
┌─────────────────────────────┐
│ USB TTL Hardware Component  │
│ (ScopeFoundry HW)           │
├─────────────────────────────┤
│ - port: String              │
│ - connection_status: Enum   │
│ - serial_handle: SerialPort │
└────────┬────────────────────┘
         │
         │ manages (1:1)
         │
         ▼
┌─────────────────────────────┐
│   Hardware Status           │
├─────────────────────────────┤
│ - status_code: Enum         │
│ - status_message: String    │
│ - error_details: String     │
└─────────────────────────────┘

┌─────────────────────────────┐
│ USB TTL Hardware Component  │
└────────┬────────────────────┘
         │
         │ produces (1:N)
         │
         ▼
┌─────────────────────────────┐
│   TTL Event Signal          │
├─────────────────────────────┤
│ - signal_value: Hex         │
│ - timestamp: Timestamp      │
│ - transmission_status: Enum │
└─────────────────────────────┘
```

**Relationship Rules**:
1. **Hardware Component → Hardware Status** (1:1):
   - Each hardware component has exactly one status at any time
   - Status updates trigger PyQt signals for UI reflection

2. **Hardware Component → TTL Event Signals** (1:N):
   - Component produces multiple signals over its lifetime
   - Signals are stateless once transmitted (no persistent storage in this version)
   - Signal history may be logged to external systems (Tobii Pro, CSV logs)

3. **Hardware Component ↔ Serial Port** (1:0..1):
   - In CONNECTED mode: 1:1 relationship with serial port
   - In SIMULATED/DISCONNECTED mode: No serial port relationship

---

## Data Flow

### Initialization Flow

```
Application Start
    ↓
Register USB TTL Hardware Component
    ↓
Call component.setup()
    ├─→ Create settings (port, baudrate)
    └─→ Register operations (send_ttl_signal)
    ↓
Call component.connect()
    ↓
Attempt Serial Port Open (COM3, 115200 baud)
    ├─→ SUCCESS:
    │   ├─→ Send "RR" initialization command
    │   ├─→ Set status = CONNECTED
    │   └─→ Emit status_changed signal
    │
    └─→ FAILURE:
        ├─→ Log error details
        ├─→ Set status = SIMULATED
        ├─→ Emit status_changed signal
        └─→ Continue without hardware
```

### Event Signal Transmission Flow

```
Experimental Event Occurs
    ↓
Application calls send_ttl_signal(0x42)
    ↓
Validate signal value (0x00 ≤ value ≤ 0xFF)
    ├─→ INVALID: Raise ValueError, return
    │
    └─→ VALID: Continue
        ↓
    Check connection_status
        ├─→ CONNECTED:
        │   ├─→ Convert to 2-byte hex string ("42")
        │   ├─→ Write to serial port
        │   ├─→ Record timestamp
        │   ├─→ Update last_signal_sent
        │   └─→ Return success
        │
        └─→ SIMULATED:
            ├─→ Log signal to console/file
            ├─→ Record timestamp
            ├─→ Update last_signal_sent
            └─→ Return success (simulated)
```

### Status Monitoring Flow

```
PyQt Main Loop
    ↓
Hardware Component monitors serial connection
    ├─→ Connection Active: No action
    │
    └─→ Connection Lost Detected:
        ├─→ Update status = DISCONNECTED
        ├─→ Emit status_changed signal
        ├─→ UI updates status indicator
        └─→ (Optional) Attempt reconnection or switch to SIMULATED
```

---

## Configuration Data

### config.yaml Structure (New Section)

```yaml
hardware:
  usb_ttl_module:
    enabled: true
    port: "COM3"
    baudrate: 115200
    timeout_seconds: 5
    fallback_to_simulated: true

    # Signal mapping (experimental event → hex value)
    signal_map:
      experiment_start: 0x01
      experiment_stop: 0x02
      mobile_stimulus_on: 0x10
      mobile_stimulus_off: 0x11
      baseline_start: 0x20
      baseline_end: 0x21
```

**Configuration Attributes**:
- `enabled`: Feature toggle for USB TTL Module
- `port`: COM port identifier (overridable at runtime)
- `baudrate`: Serial speed (default 115200, should not be changed)
- `timeout_seconds`: Maximum time for connection attempt
- `fallback_to_simulated`: Auto-switch to simulated mode on hardware failure
- `signal_map`: Mapping of experimental events to hex values (0x00-0xFF)

---

## Logging and Persistence

### Signal Event Log (Optional - User Story 3)

**Structure**:
- Format: CSV or append to existing HDF5 experimental data
- Columns: `timestamp`, `signal_value`, `source_event`, `transmission_mode`, `latency_ms`
- Retention: Per-session (cleared on new experiment start)

**Example CSV Format**:
```csv
timestamp,signal_value,source_event,transmission_mode,latency_ms
2026-01-01T14:30:45.123456,0x10,mobile_stimulus_on,HARDWARE,2.3
2026-01-01T14:30:47.654321,0x11,mobile_stimulus_off,HARDWARE,1.8
```

### Status Change Log

**Structure**:
- Format: Application log file (existing `log/` directory)
- Level: INFO for status changes, ERROR for failures
- Content: Timestamp, old status, new status, reason/error details

**Example Log Entries**:
```
[2026-01-01 14:30:00 INFO] USB TTL Module: Status changed DISCONNECTED → CONNECTED (port: COM3)
[2026-01-01 14:35:12 ERROR] USB TTL Module: Connection failed - COM3 unavailable, switching to SIMULATED
```

---

## Performance Considerations

### Timing Requirements

| Metric | Requirement | Rationale |
|--------|-------------|-----------|
| Signal transmission latency | <17ms (sub-frame at 60Hz) | Tobii Pro synchronization precision |
| Connection timeout | 5 seconds | User experience (startup time) |
| Serial write timeout | 100ms | Prevent UI blocking on hardware issues |
| Status update frequency | On-demand (event-driven) | Minimize CPU overhead |

### Memory Constraints

- **Signal history**: Not stored in memory (external logging only)
- **Status tracking**: Single instance per hardware component (~1KB)
- **Serial buffer**: Managed by pyserial library (minimal overhead)

---

## Error Handling

### Error Categories

1. **Connection Errors**:
   - Port unavailable (occupied by another application)
   - Hardware not detected (USB unplugged)
   - Driver issues (incorrect FTDI latency setting)
   - **Mitigation**: Automatic fallback to SIMULATED mode

2. **Transmission Errors**:
   - Serial write timeout (hardware not responding)
   - Invalid signal value (out of 0x00-0xFF range)
   - Mid-experiment hardware disconnection
   - **Mitigation**: Log error, continue experiment in SIMULATED mode

3. **Configuration Errors**:
   - Invalid port specification in config.yaml
   - Incorrect baudrate setting
   - **Mitigation**: Validation on startup, clear error messages

### Graceful Degradation

The system must continue operating even when hardware is unavailable:

```
Hardware Failure During Experiment
    ↓
Detect serial write error
    ↓
Log error with timestamp and context
    ↓
Switch connection_status to SIMULATED
    ↓
Continue experiment (signals logged, not transmitted)
    ↓
Notify user via UI status indicator
    ↓
Experiment proceeds without interruption
```

---

## Security and Validation

### Input Validation

- **Signal Values**: Must be integers in range 0x00-0xFF (0-255 decimal)
- **Port Names**: Must match pattern `COMx` where x is 1-999
- **Baudrate**: Must be 115200 (fixed, no user override)

### Hardware Access Control

- **COM Port Locking**: Exclusive access required (prevent multi-app conflicts)
- **Permissions**: Windows COM port access may require administrator rights
- **Driver Configuration**: FTDI latency setting must be verified/configured by user

---

## Testing Considerations

### Test Data

**Mock Serial Port Behavior**:
- Simulate successful writes (return 2 bytes written)
- Simulate timeouts (raise `serial.SerialTimeoutException`)
- Simulate disconnections (raise `serial.SerialException`)

**Test Signal Values**:
- Boundary values: `0x00`, `0xFF`
- Invalid values: `-1`, `256`, `None`, `"invalid"`
- Typical experimental values: `0x01`, `0x10`, `0x42`

### State Transition Testing

Test all valid state transitions:
- `DISCONNECTED → CONNECTED` (successful hardware connection)
- `DISCONNECTED → SIMULATED` (hardware unavailable at startup)
- `CONNECTED → DISCONNECTED` (mid-session hardware failure)
- `CONNECTED → SIMULATED` (graceful degradation)

---

## Future Extensibility

### Potential Enhancements (Out of Scope for v1)

1. **Bidirectional Communication**: Receive TTL inputs from Tobii Pro
2. **Signal Recording to HDF5**: Store TTL events in experimental data files
3. **Dynamic Port Detection**: Auto-scan COM ports for USB TTL Module
4. **Signal Waveform Visualization**: Real-time graphical display of TTL outputs
5. **Multi-Device Support**: Control multiple USB TTL Modules simultaneously

### Data Model Compatibility

The current design is extensible without breaking changes:
- Additional attributes can be added to entities (backward compatible)
- New status codes can be introduced (extend enum)
- Signal value mapping can be expanded via `config.yaml`
- Logging formats can evolve (CSV → HDF5 migration path)

---

## Summary

This data model provides a complete abstraction of the USB TTL Module integration, ensuring:

- **Separation of concerns**: Hardware management, signal transmission, status tracking
- **Robustness**: Graceful degradation, comprehensive error handling
- **Performance**: Sub-17ms latency, non-blocking operations
- **Maintainability**: Clear entity boundaries, documented state transitions
- **Testability**: Well-defined interfaces, mockable dependencies
- **Extensibility**: Future enhancements possible without breaking changes

The model aligns with the existing ScopeFoundry architecture and PyQt5 patterns used throughout the codebase (see `HW_MetaMotionRL.py` for reference implementation).
