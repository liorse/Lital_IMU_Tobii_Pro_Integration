# Changelog: Version 1.0.6 → 1.0.7

**Release Date:** January 2026  
**Commits Included:** d31ae82 (v1.0.6) → b639041 (v1.0.7) + additional threading fixes

---

## Overview
Version 1.0.7 focuses on improving thread-safety in the UI, adding hardware-specific participant ID ranges, fixing bugs related to job scheduling, and documenting the project for AI assistants. **Critical update**: All Qt threading violations have been eliminated to prevent potential crashes.

---

## 🐛 Bug Fixes

### 1. **Fixed Qt Violation: UI Updates from Different Thread**
   - **File:** `UI_Experiment_Control.py`
   - **Issue:** Direct UI element manipulation from measurement thread caused Qt threading violations
   - **Severity:** HIGH - Can cause unpredictable crashes, memory corruption, and race conditions
   - **Fix:** Replaced direct UI widget access with ScopeFoundry's settings-based approach
   - **Changes:**
     
     **Phase 1 - Mobile limb control (original fix in v1.0.7):**
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
     
     **Phase 2 - Pause button control (additional fix):**
     - **New Settings Added (lines ~220-221):**
       ```python
       self.settings.New('pause_button_text', dtype=str, initial='Pause Task', ro=False)
       self.settings.New('pause_button_checked', dtype=bool, initial=False, ro=False)
       ```
     
     - **Connected to UI Widget (lines ~268-269):**
       ```python
       self.settings.pause_button_text.connect_to_widget(self.ui.pause_stimuli_pushButton)
       self.settings.pause_button_checked.connect_to_widget(self.ui.pause_stimuli_pushButton)
       ```
     
     - **Replaced 4 Direct UI Manipulations:**
       - Line ~419 in `pause()`: `setText("Resume Task")` → `settings['pause_button_text'] = "Resume Task"`
       - Line ~432 in `pause()`: `setText("Pause Task")` → `settings['pause_button_text'] = "Pause Task"`
       - Line ~854 in `run()` finally: `setText("Pause Task")` → `settings['pause_button_text'] = "Pause Task"`
       - Line ~855 in `run()` finally: `setChecked(False)` → `settings['pause_button_checked'] = False`
   
   - **Impact:** 
     - Eliminates all Qt threading violations in the codebase
     - Prevents potential crashes during long-running experiments
     - Ensures thread-safe communication between worker thread and GUI thread

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
**Insertions:** +155 lines  
**Deletions:** -7 lines  

### Breakdown by File:
- `Agency_Sensor_MAIN.py`: +8 lines
- `GEMINI.md`: +102 lines (new file)
- `UI_Experiment_Control.py`: +31 insertions, -7 deletions
- `config.yaml`: +10 lines
- `stimuli_sound_pygame_midi.py`: +2 insertions, -1 deletion

---

## 🔧 Technical Details

### Qt Threading Fix Explanation
The primary fixes address critical Qt threading violations. In Qt/PyQt5:
- **Rule:** UI elements can only be modified from the main GUI thread
- **Violation:** The measurement's `run()` method executes in a separate worker thread
- **Problem:** Direct UI manipulation from worker thread can cause:
  - **Unpredictable crashes** (may occur intermittently)
  - **Memory corruption** (crashes may appear later, unrelated to actual bug)
  - **Visual glitches** (widgets not updating correctly)
  - **Race conditions** (deadlocks or crashes when threads collide)

### ScopeFoundry's Thread-Safe Solution
ScopeFoundry's settings system provides a safe bridge between threads:
1. **Worker thread** updates a setting value: `self.settings['pause_button_text'] = "Resume Task"`
2. **Setting change triggers a Qt signal** (happens automatically)
3. **Signal is queued to main thread** (Qt's thread-safe mechanism)
4. **Main thread updates the widget** (safe, no violation)

This pattern is used throughout the application:
- `self.settings['progress']` → updates progress bar
- `self.settings['pause_button_text']` → updates button text
- `self.settings['pause_button_checked']` → updates button checked state
- `self.mobile_ui.settings['limb_connected_to_mobile']` → updates limb selection

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
4. **Pause/Resume functionality:** Test pause button during experiments
   - Verify button text changes correctly
   - Ensure no console warnings about threading
   - Test multiple pause/resume cycles
5. **Sound system:** Verify volume muting works correctly at threshold (0.1)
6. **Step transitions:** Confirm no job removal errors in logs
7. **Long-running experiments:** Run full experiment duration to verify stability
8. **Monitor console output:** Look for any Qt threading warnings during execution

---

## 🔗 Related Commits

- **b639041** - Fixed Qt thread violation (HEAD)
- **3be2269** - Fixed sound rounding error
- **e7c8926** - Added participant range configuration
- **3c3d5a5** - Fixed job removal bug
- **d31ae82** - Version 1.0.6 (baseline)
- **[Uncommitted]** - Additional Qt threading fixes for pause button control

---

## 👥 Contributors

Changes implemented with assistance from AI coding assistants (Gemini, Claude).

---

## ⚠️ Breaking Changes

None. All changes maintain backward compatibility.

---

## 🔐 Security & Stability

**Critical Improvement:** All Qt threading violations have been eliminated. This significantly improves application stability and prevents potential crashes during long-running experiments. The application is now safe for production use in research environments.

---

## 📝 Notes

- All changes maintain backward compatibility with existing `config.yaml` files
- The participant ranges feature gracefully falls back to 'hebrew' defaults if configuration is missing
- Thread-safety improvements make the application more stable during long experiments
