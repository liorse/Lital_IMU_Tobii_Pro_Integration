---
description: "Task list for USB TTL Module integration implementation"
---

# Tasks: USB TTL Module Integration for Tobii Pro Event Signaling

**Input**: Design documents from `/specs/001-usb-ttl-module/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/HW_USB_TTL.md, contracts/UI_USB_TTL.md

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are included as optional for validation purposes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Repository root structure**: Flat module layout (HW_*.py, UI_*.py at root)
- **Tests**: tests/test_*.py (new directory to be created)
- **Config**: config.yaml (existing file to be modified)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for USB TTL Module integration

- [ ] T001 Verify Python 3.10.15 and conda environment 'lital' is activated
- [ ] T002 [P] Verify pyserial 3.5 is installed in environment (check environment.yml)
- [ ] T003 [P] Create tests/ directory at repository root for unit tests
- [ ] T004 [P] Verify FTDI VCP drivers are installed (check Windows Device Manager)
- [ ] T005 Read User_Manuals/USBTTLv1r18.pdf to understand hardware serial protocol
- [ ] T006 [P] Read HW_MetaMotionRL.py to understand ScopeFoundry HardwareComponent pattern
- [ ] T007 [P] Read UI_MetaMotionRL.py to understand ScopeFoundry Measurement UI pattern

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Document FTDI driver latency configuration requirement (1ms vs default 16ms) in CLAUDE.md or setup notes
- [ ] T009 Create baseline configuration section for USB TTL Module in config.yaml (disabled: false placeholder)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Connect to USB TTL Hardware (Priority: P1) 🎯 MVP

**Goal**: Establish connection to Black Box Toolkit USB TTL Module on COM3 with automatic fallback to simulated mode

**Independent Test**: Launch the application and verify the hardware connection status shows "Connected" for the USB TTL Module (if hardware present), or "Simulated" if hardware unavailable. Check application logs for connection status messages.

### Implementation for User Story 1

- [ ] T010 [US1] Create HW_USB_TTL.py at repository root with USBTTLHardware class skeleton (inherit from ScopeFoundry.HardwareComponent)
- [ ] T011 [US1] Implement __init__ method in HW_USB_TTL.py (accept app, name, port='COM3' parameters)
- [ ] T012 [US1] Implement setup() method in HW_USB_TTL.py (create settings: port, baudrate, connection_status, simulated_mode)
- [ ] T013 [US1] Implement connect() method in HW_USB_TTL.py (open serial port at 115200 baud, 8N1, send 'RR' reset command)
- [ ] T014 [US1] Add automatic fallback to simulated mode in connect() method (try/except serial.SerialException, set simulated_mode=True)
- [ ] T015 [US1] Implement disconnect() method in HW_USB_TTL.py (close serial port, update connection_status)
- [ ] T016 [US1] Add logging for connection events in HW_USB_TTL.py (INFO for success/simulated, WARNING for fallback, ERROR for failures)
- [ ] T017 [US1] Register USBTTLHardware in Agency_Sensor_MAIN.py setup() method (add import and self.add_hardware call)
- [ ] T018 [US1] Update config.yaml to add hardware.usb_ttl_module section (enabled, port, timeout_seconds, fallback_to_simulated)
- [ ] T019 [US1] Test hardware connection with physical USB TTL Module on COM3 (verify "Connected" status in logs)
- [ ] T020 [US1] Test simulated mode by unplugging hardware or using invalid COM port (verify "Simulated" status in logs)
- [ ] T021 [US1] Test COM port conflict by opening serial monitor on COM3, then launching app (verify graceful error message)

**Checkpoint**: At this point, User Story 1 should be fully functional - application connects to hardware or enters simulated mode gracefully

---

## Phase 4: User Story 2 - Send Event Signals to Tobii Pro (Priority: P2)

**Goal**: Enable sending 8-bit TTL event signals (0x00-0xFF) to Tobii Pro system for experimental event synchronization

**Independent Test**: Trigger an experimental event (e.g., manually call send_ttl_signal(0x42)) and verify: (1) in hardware mode, signal appears in Tobii Pro recording timeline; (2) in simulated mode, signal is logged to console. Verify rapid succession of 10 signals maintains correct temporal order.

**Dependencies**: Requires User Story 1 (hardware connection) to be complete

### Implementation for User Story 2

- [ ] T022 [US2] Implement send_ttl_signal(value) method in HW_USB_TTL.py (validate 0x00 ≤ value ≤ 0xFF)
- [ ] T023 [US2] Add serial port write logic in send_ttl_signal() for hardware mode (convert value to 2-byte uppercase hex string, e.g., 0x42 → "42")
- [ ] T024 [US2] Add simulated mode logging in send_ttl_signal() (log signal value with timestamp, return True)
- [ ] T025 [US2] Implement reset_hardware() method in HW_USB_TTL.py (send "RR" command to serial port)
- [ ] T026 [US2] Register send_ttl_signal and reset_hardware as operations in setup() method (self.add_operation calls)
- [ ] T027 [US2] Add error handling for invalid signal values in send_ttl_signal() (raise ValueError if outside 0x00-0xFF)
- [ ] T028 [US2] Add error handling for serial write timeout in send_ttl_signal() (catch serial.SerialTimeoutException, return False)
- [ ] T029 [US2] Add internal tracking for last_signal_sent and last_signal_timestamp attributes in HW_USB_TTL.py
- [ ] T030 [US2] Update config.yaml signal_map section (add experimental event → hex value mappings: experiment_start: 0x01, mobile_stimulus_on: 0x10, etc.)
- [ ] T031 [US2] Create example integration in UI_Experiment_Control.py or UI_Mobile_Control.py (send TTL signal on mobile stimulus activation)
- [ ] T032 [US2] Test send_ttl_signal with hardware mode (verify 0x42 appears in Tobii Pro timeline with correct timestamp)
- [ ] T033 [US2] Test send_ttl_signal with simulated mode (verify log entry shows signal value and timestamp)
- [ ] T034 [US2] Test rapid signal sequence (send 10 signals in 1 second, verify all transmitted in order)
- [ ] T035 [US2] Test invalid signal values (verify ValueError raised for -1, 256, None, "invalid")
- [ ] T036 [US2] Measure signal transmission latency (verify <17ms for 60Hz eye-tracking sync, typical <5ms)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - hardware connects and transmits TTL signals successfully

---

## Phase 5: User Story 3 - Monitor TTL Signal Activity (Priority: P3)

**Goal**: Provide real-time UI log of TTL signal transmissions for debugging and verification

**Independent Test**: Launch the application, open the USB TTL Monitor UI panel, trigger several experimental events (send 5+ TTL signals), and verify each signal's timestamp and hex value appear in the activity log display.

**Dependencies**: Requires User Story 2 (signal transmission) to be complete for meaningful monitoring

### Implementation for User Story 3

- [ ] T037 [P] [US3] Create UI_USB_TTL.py at repository root with USBTTLMonitorUI class skeleton (inherit from ScopeFoundry.Measurement)
- [ ] T038 [US3] Implement setup() method in UI_USB_TTL.py (create settings: max_log_entries=1000, enable_logging=True)
- [ ] T039 [US3] Initialize internal signal history buffer in setup() (collections.deque with maxlen=1000)
- [ ] T040 [US3] Implement setup_figure() method in UI_USB_TTL.py (create PyQt5 QGroupBox titled "USB TTL Module Monitor")
- [ ] T041 [P] [US3] Add status indicator QLabel in setup_figure() (show connection state with color-coded text: green for Connected, yellow for Simulated, red for Disconnected)
- [ ] T042 [P] [US3] Add activity log QTextEdit in setup_figure() (read-only, monospace font, scrollable)
- [ ] T043 [P] [US3] Add manual test controls in setup_figure() (QSpinBox for signal value 0-255 hex, "Send Test Signal" QPushButton)
- [ ] T044 [P] [US3] Add "Reset Hardware" QPushButton in setup_figure() (calls hardware.reset_hardware())
- [ ] T045 [P] [US3] Add "Clear Log" QPushButton in setup_figure() (clears activity_log QTextEdit and history buffer)
- [ ] T046 [US3] Implement log_signal(value, status, latency_ms) method in UI_USB_TTL.py (format: "[HH:MM:SS.mmm] 0xVV → STATUS (latency ms)")
- [ ] T047 [US3] Implement log_message(message) method in UI_USB_TTL.py (append timestamped message to activity log)
- [ ] T048 [US3] Connect hardware status_changed signal to UI status label update handler (use PyQt signal/slot)
- [ ] T049 [US3] Implement update_display() method in UI_USB_TTL.py (refresh status indicator, append new signals to log, manage max_log_entries)
- [ ] T050 [US3] Implement on_send_test_clicked() slot in UI_USB_TTL.py (read spinbox value, call hardware.send_ttl_signal, log result)
- [ ] T051 [US3] Implement on_reset_clicked() slot in UI_USB_TTL.py (call hardware.reset_hardware, log outcome)
- [ ] T052 [US3] Implement on_clear_log_clicked() slot in UI_USB_TTL.py (clear QTextEdit and deque buffer)
- [ ] T053 [US3] Register USBTTLMonitorUI in Agency_Sensor_MAIN.py setup() method (add import and self.add_measurement call)
- [ ] T054 [US3] Test UI status indicator updates (verify color changes: green Connected → yellow Simulated when hardware unplugged)
- [ ] T055 [US3] Test activity log display (send 10 signals, verify all appear with timestamps in format "[14:30:45.123] 0x42 → SENT (2.3ms)")
- [ ] T056 [US3] Test manual signal sending via UI spinbox and button (set value 0x42, click Send, verify signal transmitted and logged)
- [ ] T057 [US3] Test log size management (send 1500 signals, verify only last 1000 remain in log)
- [ ] T058 [US3] Test reset button (click Reset Hardware, verify "RR" command sent and logged)
- [ ] T059 [US3] Test clear log button (send 20 signals, click Clear Log, verify activity log is empty)

**Checkpoint**: All user stories should now be independently functional - connection, signal transmission, and monitoring all working

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, cleanup, and final validation

- [ ] T060 [P] Add unit tests for send_ttl_signal in tests/test_HW_USB_TTL.py (use unittest.mock to mock serial.Serial, verify correct hex conversion)
- [ ] T061 [P] Add unit tests for connect/disconnect lifecycle in tests/test_HW_USB_TTL.py (verify simulated mode fallback, connection status updates)
- [ ] T062 [P] Add unit tests for signal value validation in tests/test_HW_USB_TTL.py (verify ValueError for out-of-range values)
- [ ] T063 Add integration test for complete workflow in tests/test_integration_usb_ttl.py (connect → send signal → verify in Tobii Pro → disconnect)
- [ ] T064 [P] Update CLAUDE.md with USB TTL Module integration notes (COM port configuration, FTDI latency requirement, signal mapping conventions)
- [ ] T065 [P] Add docstrings to all public methods in HW_USB_TTL.py (follow Google Python style guide)
- [ ] T066 [P] Add docstrings to all public methods in UI_USB_TTL.py (follow Google Python style guide)
- [ ] T067 Code review HW_USB_TTL.py for error handling completeness (verify all serial exceptions caught, no crashes on hardware failure)
- [ ] T068 Code review UI_USB_TTL.py for thread safety (verify all UI updates on main thread, PyQt signals used correctly)
- [ ] T069 Performance validation: measure signal latency under load (send 100 signals in rapid succession, verify all <17ms)
- [ ] T070 Stability test: run 2+ hour experimental session (verify no connection drops, memory leaks, or signal transmission failures)
- [ ] T071 Validate quickstart.md steps (follow guide from Step 1-6, verify all instructions work on clean environment)
- [ ] T072 [P] Add error recovery documentation (what to do when COM port unavailable, driver latency misconfigured, hardware disconnected mid-session)
- [ ] T073 Final cleanup: remove debug print statements, ensure consistent logging levels (INFO for normal operation, DEBUG for detailed serial communication)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (requires hardware connection infrastructure)
- **User Story 3 (Phase 5)**: Depends on User Story 2 completion (monitors signal transmission, needs signals to monitor)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - **No dependencies on other stories**
- **User Story 2 (P2)**: **Depends on User Story 1** (requires hardware connection before signals can be sent)
- **User Story 3 (P3)**: **Depends on User Story 2** (monitors signal transmission, needs functional signal sending)

**Note**: Unlike typical multi-story features, these user stories have sequential dependencies because each builds on the previous infrastructure. However, each story still delivers independent value and can be tested standalone.

### Within Each User Story

- **User Story 1**: Tasks T010-T021 should be done in order (class skeleton → lifecycle methods → registration → testing)
- **User Story 2**: Tasks T022-T029 can be partially parallelized (signal method implementation), but T030-T036 (integration and testing) depend on T022-T029 completion
- **User Story 3**: Tasks T037-T045 (UI widgets) can be parallelized, T046-T052 (logic) depend on widgets, T053-T059 (testing) depend on all implementation

### Parallel Opportunities

- **Setup (Phase 1)**: Tasks T002, T003, T004, T006, T007 marked [P] can run in parallel
- **User Story 3**: Tasks T037, T041, T042, T043, T044, T045 (UI widgets) can be created in parallel since they're in different layout sections
- **Polish (Phase 6)**: Tasks T060, T061, T062, T064, T065, T066, T072 can all run in parallel (different files, independent)

---

## Parallel Example: User Story 3 (UI Widgets)

```bash
# Launch all UI widget creation tasks together:
Task: "Add status indicator QLabel in setup_figure()"
Task: "Add activity log QTextEdit in setup_figure()"
Task: "Add manual test controls in setup_figure()"
Task: "Add Reset Hardware QPushButton in setup_figure()"
Task: "Add Clear Log QPushButton in setup_figure()"

# These can all be worked on simultaneously since they're independent PyQt5 widgets
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (hardware connection)
4. **STOP and VALIDATE**: Test hardware connection independently
   - Launch application with hardware plugged in → verify "Connected"
   - Unplug hardware → verify "Simulated" mode
   - Test COM port conflict → verify graceful error
5. Deploy/demo if ready (this is a usable MVP - researchers can verify hardware integration)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Deploy/Demo (MVP!)** - Hardware integration working
3. Add User Story 2 → Test independently → **Deploy/Demo** - Can now send TTL signals to Tobii Pro
4. Add User Story 3 → Test independently → **Deploy/Demo** - Full monitoring and debugging capabilities
5. Add Polish → Final validation → **Production Release**

Each story adds value incrementally:
- **After US1**: Researchers can verify hardware detection and simulated mode fallback
- **After US2**: Researchers can synchronize experimental events with Tobii Pro eye-tracking
- **After US3**: Researchers can debug timing issues and verify signal transmission in real-time

### Sequential Implementation (Recommended for Solo Developer)

Due to sequential dependencies, implement in strict priority order:

1. Phase 1 (Setup) → Phase 2 (Foundational) → **Checkpoint: Foundation Ready**
2. Phase 3 (US1: Hardware Connection) → **Checkpoint: Test connection works**
3. Phase 4 (US2: Signal Transmission) → **Checkpoint: Test signals appear in Tobii Pro**
4. Phase 5 (US3: Monitoring UI) → **Checkpoint: Test UI displays signals**
5. Phase 6 (Polish) → Final validation → **Complete**

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - **Developer A**: User Story 1 (hardware connection)
   - **Developer B**: Prepare User Story 2 tasks (review serial protocol, plan signal method)
   - **Developer C**: Prepare User Story 3 tasks (design UI mockups, review PyQt5 patterns)
3. Once US1 complete:
   - **Developer A**: Moves to polish tasks (documentation, unit tests)
   - **Developer B**: Implements User Story 2 (can now test with US1 hardware)
   - **Developer C**: Waits for US2 completion
4. Once US2 complete:
   - **Developer B**: Assists with polish tasks
   - **Developer C**: Implements User Story 3 (can now test with real signals)
5. Final integration testing and polish by all developers

---

## Testing Checklist (Per User Story)

### User Story 1: Hardware Connection
- [ ] Application launches successfully with hardware connected (verify "Connected" log)
- [ ] Application launches successfully without hardware (verify "Simulated" log)
- [ ] COM port conflict handled gracefully (verify error message, no crash)
- [ ] Connection status setting updates correctly (check via ScopeFoundry UI)
- [ ] Simulated mode flag set correctly (verify via settings)

### User Story 2: Signal Transmission
- [ ] Valid signal (0x42) transmitted successfully in hardware mode (verify in Tobii Pro timeline)
- [ ] Valid signal (0x42) logged successfully in simulated mode (check console output)
- [ ] Rapid signal sequence (10 signals/second) maintains order (verify timestamps)
- [ ] Invalid signal value (256) raises ValueError (test exception handling)
- [ ] Signal latency <17ms verified (measure with time.time() before/after call)
- [ ] Serial write timeout handled gracefully (mock timeout exception)

### User Story 3: Monitoring UI
- [ ] Status indicator shows correct color for each connection state (green/yellow/red)
- [ ] Activity log displays signals with correct format "[HH:MM:SS.mmm] 0xVV → STATUS (latency)"
- [ ] Manual signal test button works (send 0x42 via UI, verify logged)
- [ ] Reset hardware button works (verify "RR" command logged)
- [ ] Clear log button empties activity log (verify UI cleared)
- [ ] Log size management works (send 1500 signals, verify only last 1000 remain)

---

## Notes

- **[P] tasks**: Different files or independent UI widgets, no dependencies
- **[Story] label**: Maps task to specific user story for traceability
- **Sequential dependencies**: User stories build on each other (US2 needs US1, US3 needs US2)
- **File paths**: All at repository root following flat module structure (HW_*.py, UI_*.py)
- **Testing approach**: Manual testing primarily (unit tests in polish phase are optional)
- **Commit strategy**: Commit after each completed user story phase (T021, T036, T059)
- **Validation checkpoints**: Stop at each user story completion to test independently
- **Reference implementations**: HW_MetaMotionRL.py (hardware pattern), UI_MetaMotionRL.py (UI pattern)
- **Critical requirement**: FTDI driver latency MUST be 1ms (document in T008, verify in quickstart validation T071)

---

## Task Count Summary

- **Phase 1 (Setup)**: 7 tasks
- **Phase 2 (Foundational)**: 2 tasks
- **Phase 3 (User Story 1)**: 12 tasks (T010-T021)
- **Phase 4 (User Story 2)**: 15 tasks (T022-T036)
- **Phase 5 (User Story 3)**: 23 tasks (T037-T059)
- **Phase 6 (Polish)**: 14 tasks (T060-T073)
- **Total**: 73 tasks

**Parallel opportunities identified**: 19 tasks marked [P] across all phases

**Independent test criteria**: Defined for all 3 user stories

**Suggested MVP scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 21 tasks
- This delivers functional hardware connection with simulated mode fallback
- Validates ScopeFoundry integration without requiring Tobii Pro hardware for testing
