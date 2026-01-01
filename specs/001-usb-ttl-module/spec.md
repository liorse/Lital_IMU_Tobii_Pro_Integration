# Feature Specification: USB TTL Module Integration for Tobii Pro Event Signaling

**Feature Branch**: `001-usb-ttl-module`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "USB_TTL_Module - I would like to add this hardware from The Black Box Toolkit to my program. It runs on COM3. I would like it to be added as a hardware device under the scopefoundry framework that is currently used in the program. If the hardware is not found, please replace with a simulated version. This hardware function is to signal events to the Tobii Pro instruments using TTL signal. It is able to output 8 bit outputs, and we write to it an hex number between 00 and 0xff."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect to USB TTL Hardware (Priority: P1)

The researcher needs to establish a connection to the Black Box Toolkit USB TTL Module on COM3 to enable event signaling to Tobii Pro eye-tracking instruments during experimental sessions.

**Why this priority**: This is the foundational capability - without hardware connectivity, no event signaling is possible. This must work first before any event transmission can occur.

**Independent Test**: Can be fully tested by launching the application and verifying the hardware connection status indicator shows "Connected" for the USB TTL Module, or "Simulated" if hardware is unavailable. Delivers immediate value by confirming hardware integration into the ScopeFoundry framework.

**Acceptance Scenarios**:

1. **Given** the USB TTL Module is connected to COM3, **When** the application starts, **Then** the hardware component successfully connects and reports "Connected" status
2. **Given** the USB TTL Module is not physically connected, **When** the application starts, **Then** the system automatically switches to simulated mode and reports "Simulated" status
3. **Given** COM3 is occupied by another application, **When** the application attempts to connect, **Then** an error message is displayed indicating the port is unavailable

---

### User Story 2 - Send Event Signals to Tobii Pro (Priority: P2)

During an experiment, the researcher needs to send timestamped event markers (8-bit hex values from 0x00 to 0xFF) to the Tobii Pro system to synchronize experimental events with eye-tracking data.

**Why this priority**: This is the core functionality that delivers research value - marking specific experimental events in the eye-tracking timeline. Depends on P1 (hardware connection) being established first.

**Independent Test**: Can be tested by triggering a known experimental event (e.g., mobile stimulus activation) and verifying that the corresponding TTL signal value appears in the Tobii Pro recording timeline. Delivers value by enabling precise synchronization of behavioral and eye-tracking data.

**Acceptance Scenarios**:

1. **Given** the USB TTL Module is connected, **When** an experimental event occurs, **Then** a corresponding 8-bit hex value is sent to the Tobii Pro system
2. **Given** multiple events occur in rapid succession, **When** event signals are sent, **Then** all signals are transmitted in the correct temporal order
3. **Given** the system is in simulated mode, **When** an event signal is triggered, **Then** the signal value is logged but no physical TTL output occurs

---

### User Story 3 - Monitor TTL Signal Activity (Priority: P3)

The researcher wants to view a real-time log of TTL signals being sent during the experiment to verify proper event synchronization and troubleshoot any timing issues.

**Why this priority**: This is a quality-of-life and debugging feature that helps researchers verify correct operation but isn't essential for basic functionality. The experiment can run without this monitoring capability.

**Independent Test**: Can be tested by triggering several experimental events and verifying that each event's timestamp and hex value appear in the TTL activity log display. Delivers value by providing transparency and debugging support for researchers.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** TTL signals are sent, **Then** each signal is logged with timestamp and hex value in the UI
2. **Given** the researcher wants to review past signals, **When** scrolling the activity log, **Then** all signals from the current session are visible
3. **Given** a long experimental session, **When** the log reaches 1000 entries, **Then** older entries are automatically removed to prevent memory issues

---

### Edge Cases

- What happens when the USB TTL Module disconnects mid-experiment?
- How does the system handle COM3 being unavailable at startup?
- What occurs if an invalid hex value (outside 0x00-0xFF range) is attempted?
- How does the system behave if COM3 is the wrong port for the device?
- What happens when transitioning from hardware to simulated mode during an active experiment?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a ScopeFoundry HardwareComponent for the USB TTL Module following the existing hardware abstraction pattern used by MetaMotionRLHW
- **FR-002**: System MUST attempt to connect to the USB TTL Module on COM3 at application startup
- **FR-003**: System MUST automatically switch to a simulated mode if the USB TTL Module hardware is not found on COM3
- **FR-004**: System MUST provide a method to send 8-bit hex values (0x00 to 0xFF) as TTL output signals
- **FR-005**: System MUST validate that output values are within the valid 8-bit range (0x00 to 0xFF) before transmission
- **FR-006**: System MUST report hardware connection status (Connected, Disconnected, Simulated) to the user interface
- **FR-007**: Simulated mode MUST log all TTL signal attempts without requiring physical hardware
- **FR-008**: System MUST handle COM port access errors gracefully without crashing the application
- **FR-009**: System MUST integrate with the existing ScopeFoundry architecture without requiring modifications to the core framework
- **FR-010**: System MUST allow configuration of the COM port number through the existing config.yaml structure

### Key Entities

- **USB TTL Hardware Component**: A ScopeFoundry HardwareComponent representing the Black Box Toolkit USB TTL Module, managing serial communication on COM3 and exposing TTL signal transmission methods
- **TTL Event Signal**: An 8-bit hex value (0x00-0xFF) transmitted to mark specific experimental events for Tobii Pro synchronization
- **Hardware Status**: The connection state of the USB TTL Module (Connected, Disconnected, Simulated)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Researchers can successfully establish connection to USB TTL Module within 5 seconds of application startup when hardware is present
- **SC-002**: System seamlessly switches to simulated mode within 3 seconds when hardware is not detected, allowing experiments to proceed without hardware dependency
- **SC-003**: All TTL event signals are transmitted with timestamp precision sufficient for synchronization with 60Hz+ eye-tracking data (sub-17ms timing accuracy)
- **SC-004**: 100% of valid hex values (0x00-0xFF) are successfully transmitted to Tobii Pro system during hardware mode
- **SC-005**: System maintains stable operation for continuous experimental sessions lasting 2+ hours without connection drops or signal transmission failures

## Assumptions *(optional)*

- The Black Box Toolkit USB TTL Module uses standard serial communication protocol
- COM3 is the dedicated port for this hardware and will not conflict with other devices
- The Tobii Pro system is configured to receive TTL input signals on its hardware interface
- Event timing requirements align with standard eye-tracking synchronization needs (sub-frame precision)
- The existing ScopeFoundry framework supports adding new hardware components without core modifications

## Dependencies *(optional)*

- Requires ScopeFoundry framework (already present in codebase)
- Requires Python serial communication library (pyserial or similar)
- Requires Black Box Toolkit USB TTL Module driver/documentation for communication protocol
- May require Windows COM port access permissions depending on system security settings

## Out of Scope *(optional)*

- Bidirectional communication (receiving signals from Tobii Pro back to the system)
- Support for TTL modules from other manufacturers
- Dynamic port scanning to auto-detect the TTL module on different COM ports
- Graphical waveform visualization of TTL signals
- Recording TTL signals to the existing HDF5 experimental data files (this may be future work but is not required for initial integration)
