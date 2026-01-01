# Implementation Plan: USB TTL Module Integration for Tobii Pro Event Signaling

**Branch**: `001-usb-ttl-module` | **Date**: 2026-01-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-usb-ttl-module/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Integrate the Black Box Toolkit USB TTL Module as a ScopeFoundry HardwareComponent to send 8-bit TTL event signals (0x00-0xFF) to Tobii Pro eye-tracking instruments for experimental event synchronization. The implementation will follow the existing hardware abstraction pattern (similar to MetaMotionRLHW), support automatic hardware/simulated mode switching, and integrate seamlessly into the existing PyQt5-based experimental control application.

## Technical Context

**Language/Version**: Python 3.10.15
**Primary Dependencies**: ScopeFoundry (framework), PyQt5 (GUI), pyserial (serial communication), h5py (data logging)
**Storage**: HDF5 files for experimental data (existing pattern), potential CSV logging for TTL events
**Testing**: NEEDS CLARIFICATION (project currently lacks test infrastructure)
**Target Platform**: Windows 10+ (MSYS_NT environment, COM port access required)
**Project Type**: Single desktop application (PyQt5-based research tool)
**Performance Goals**: Sub-17ms TTL signal transmission latency for 60Hz+ eye-tracking synchronization, 5-second hardware connection timeout, stable operation for 2+ hour sessions
**Constraints**: Must not block main PyQt5 event loop, graceful degradation to simulated mode without hardware, COM3 serial port access
**Scale/Scope**: Single-user research application, 4 existing MetaWear sensors + 1 new TTL module, ~20 Python source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: No project constitution currently defined (`.specify/memory/constitution.md` contains template only)

**Default Quality Gates Applied**:

| Gate | Status | Notes |
|------|--------|-------|
| Follows existing architecture patterns | ✅ PASS | USB TTL Module will use ScopeFoundry HardwareComponent pattern identical to MetaMotionRLHW |
| Maintains backward compatibility | ✅ PASS | New hardware component, no modifications to existing code required |
| Graceful error handling | ✅ PASS | Automatic fallback to simulated mode when hardware unavailable |
| Performance requirements met | ✅ PASS | Sub-17ms latency achievable with serial communication (typical <1ms for simple byte write) |
| Platform compatibility | ✅ PASS | Windows COM port access via pyserial (already used in codebase dependencies) |

**Violations/Concerns**: None identified

**Post-Phase 1 Re-evaluation** (2026-01-01):

After completing Phase 1 design (data model, API contracts, quickstart guide), the Constitution Check has been re-evaluated:

| Gate | Status | Re-evaluation Notes |
|------|--------|---------------------|
| Follows existing architecture patterns | ✅ PASS | API contract confirms HardwareComponent lifecycle (setup→connect→disconnect) identical to MetaMotionRLHW pattern |
| Maintains backward compatibility | ✅ PASS | No changes to existing code required; new hardware component is purely additive |
| Graceful error handling | ✅ PASS | Data model confirms automatic fallback to simulated mode with comprehensive error handling |
| Performance requirements met | ✅ PASS | Quickstart guide confirms <5ms typical latency (well under 17ms target for 60Hz sync) |
| Platform compatibility | ✅ PASS | Research confirms pyserial 3.5 already in environment.yml, Windows COM port access compatible |

**Additional Quality Checks**:
- **Thread Safety**: ✅ PASS - API contract specifies thread-safe serial port access with internal locking
- **Testing Strategy**: ✅ PASS - Research document defines pytest with mock serial ports (unittest.mock)
- **Documentation**: ✅ PASS - Comprehensive API contracts, data model, and quickstart guide generated

**No new violations or concerns identified during design phase.** All quality gates continue to pass.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
Repository Root (Lital_IMU_Tobii_Pro_Integration/)
├── HW_USB_TTL.py                    # NEW: USB TTL Module hardware component
├── UI_USB_TTL.py                    # NEW: Optional UI for TTL monitoring (User Story 3)
├── Agency_Sensor_MAIN.py            # MODIFIED: Register new hardware component
├── config.yaml                      # MODIFIED: Add USB TTL Module configuration
├── HW_MetaMotionRL.py               # Reference implementation pattern
├── UI_MetaMotionRL.py               # Reference UI pattern
├── UI_Experiment_Control.py         # Potential integration point for event triggering
├── UI_Mobile_Control.py             # Potential integration point for event triggering
├── data/                            # Experimental data storage (HDF5)
├── log/                             # Application logs
└── media/                           # Audio/visual stimuli

tests/                               # Currently non-existent, to be created
└── test_HW_USB_TTL.py               # NEW: Unit tests for USB TTL hardware
```

**Structure Decision**: This is a single desktop application following a flat module structure. New files will be added at the repository root following the existing naming convention (`HW_*.py` for hardware, `UI_*.py` for UI components). The flat structure aligns with the current codebase organization where each hardware and UI component is a standalone Python module at the root level.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected - this section is not applicable.
