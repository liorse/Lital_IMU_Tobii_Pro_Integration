# Changelog: Version 1.0.6 → 1.0.7

**Release Date:** January 2026  
**Commits Included:** d31ae82 (v1.0.6) → b639041 (v1.0.7)

---

## Overview
Version 1.0.7 focuses on improving thread-safety in the UI, adding hardware-specific participant ID ranges, fixing bugs related to job scheduling, and documenting the project for AI assistants.

---

## 🐛 Bug Fixes

### 1. **Fixed Qt Violation: UI Updates from Different Thread**
   - **File:** `UI_Experiment_Control.py`
   - **Issue:** Direct UI element manipulation from measurement thread caused Qt threading violations
   - **Fix:** Replaced direct UI widget access with ScopeFoundry's settings-based approach
   - **Details:**
     - Changed from: `self.mobile_ui.ui.Limb_connected_to_mobile_ComboBox.setCurrentText(...)`
     - Changed to: `self.mobile_ui.settings['limb_connected_to_mobile'] = ...`
     - Applied in 3 locations:
       - Line ~668: Fixation step (disconnect all limbs)
       - Line ~709: Other steps (connect specific limb)
       - Line ~831: Cleanup after experiment ends
     - Added limb mapping dictionary to convert UI-friendly names to settings values:
       ```python
       limb_map = {
           "Left Hand": "_left_hand",
           "Right Hand": "_right_hand",
           "Left Leg": "_left_leg",
           "Right Leg": "_right_leg",
           "None": "_none"
       }
       ```

### 2. **Fixed Scheduler Job Removal Bug**
   - **File:** `UI_Experiment_Control.py` (line ~510)
   - **Issue:** Attempted to manually remove `mobile_music_timer` job that was already auto-removed
   - **Fix:** Removed the manual `scheduler.remove_job(job_id='mobile_music_timer')` call
   - **Reason:** Jobs with `trigger='date'` are automatically removed after execution
   - **Comment Added:** `# Job is automatically removed after execution with date trigger, no need to remove manually`

### 3. **Fixed Floating-Point Rounding Error in Sound System**
   - **File:** `stimuli_sound_pygame_midi.py` (lines ~41-43)
   - **Issue:** Floating-point precision caused values like `0.10000000000000003` instead of `0.1`
   - **Fix:** Added rounding to 1 decimal place:
     ```python
     speed = round(speed, 1)
     volume round(volume, 1)
     ```
   - **Impact:** Prevented sound from being muted due to precision errors when checking `if current_volume <= 0.1`

### 4. **Code Cleanup: Removed Empty Line**
   - **File:** `stimuli_sound_pygame_midi.py` (line ~136)
   - **Change:** Removed unnecessary blank line before volume check

---

## ✨ Features & Enhancements

### 1. **Participant Range Configuration Based on Hardware Type**
   - **Files:** `Agency_Sensor_MAIN.py`, `UI_Experiment_Control.py`, `config.yaml`
   - **Feature:** Dynamic participant ID ranges based on hardware configuration
   - **Implementation:**
     
     **config.yaml:**
     ```yaml
     participant_ranges:
       shiba:
         min: 6000
         max: 6999
         initial: 6000
       hebrew:
         min: 5000
         max: 5999
         initial: 5000
     ```
     
     **Agency_Sensor_MAIN.py:**
     - Loads `participant_ranges` from config
     - Sets `self.hardware_type` based on command-line argument ('shiba' or 'hebrew')
     - Makes both available to measurement components
     
     **UI_Experiment_Control.py:**
     - Reads `hardware_type` from app
     - Reads `participant_ranges` from app with fallback defaults
     - Dynamically sets participant spinbox range based on hardware type
     - Defaults to 'hebrew' configuration if type not specified
   
   - **Benefit:** Prevents ID collisions between different study groups/locations

---

## 📚 Documentation

### 1. **Added GEMINI.md - AI Assistant Project Guide**
   - **File:** `GEMINI.md` (new file, 102 lines)
   - **Purpose:** Comprehensive project documentation for AI assistants (Gemini, Claude, etc.)
   - **Contents:**
     - **Project Overview:** Research application for infant agency studies
     - **Environment Setup:** Prerequisites, installation steps, Conda environment
     - **Running the Application:** CLI usage, VS Code launch configs
     - **Project Architecture:**
       - Key files and their purposes
       - Hardware components (MetaWear sensors, USB TTL)
       - Measurement/UI components
       - Subprocess architecture (ZMQ communication)
     - **Configuration Guide:** Detailed `config.yaml` structure
     - **Development Notes:** Conventions, threading, data persistence
     - **Troubleshooting:** Common issues (Bluetooth, COM ports, latency)
   
   - **Impact:** Enables AI coding assistants to better understand and contribute to the project

---

## 📊 Statistics

**Files Changed:** 5  
**Insertions:** +146 lines  
**Deletions:** -7 lines  

### Breakdown by File:
- `Agency_Sensor_MAIN.py`: +8 lines
- `GEMINI.md`: +102 lines (new file)
- `UI_Experiment_Control.py`: +22 insertions, -7 deletions
- `config.yaml`: +10 lines
- `stimuli_sound_pygame_midi.py`: +2 insertions, -1 deletion

---

## 🔧 Technical Details

### Qt Threading Fix Explanation
The primary fix addresses a critical Qt threading violation. In Qt/PyQt5:
- **Rule:** UI elements can only be modified from the main GUI thread
- **Violation:** The measurement's `run()` method executes in a separate thread
- **Solution:** Use ScopeFoundry's settings system, which safely bridges threads:
  - Settings changes trigger signals
  - Signals are queued to the main thread
  - Widget updates happen safely in the main thread

### APScheduler Job Management
- **Date-triggered jobs** (`trigger='date'`) execute once at a specific time and are automatically removed
- **Interval-triggered jobs** require manual removal
- The fix prevents `JobLookupError` when trying to remove already-removed jobs

---

## 🧪 Testing Recommendations

Before deploying version 1.0.7, test:
1. **Hardware configurations:** Run with both `shiba` and `hebrew` arguments
2. **Participant ID ranges:** Verify spinbox constraints match hardware type
3. **Mobile limb control:** Ensure all limb connections work without Qt warnings
4. **Sound system:** Verify volume muting works correctly at threshold (0.1)
5. **Step transitions:** Confirm no job removal errors in logs
6. **Multi-step experiments:** Test pause/resume functionality

---

## 🔗 Related Commits

- **b639041** - Fixed Qt thread violation (HEAD)
- **3be2269** - Fixed sound rounding error
- **e7c8926** - Added participant range configuration
- **3c3d5a5** - Fixed job removal bug
- **d31ae82** - Version 1.0.6 (baseline)

---

## 👥 Contributors

Changes implemented with assistance from AI coding assistants (Gemini).

---

## 📝 Notes

- All changes maintain backward compatibility with existing `config.yaml` files
- The participant ranges feature gracefully falls back to 'hebrew' defaults if configuration is missing
- Thread-safety improvements make the application more stable during long experiments
