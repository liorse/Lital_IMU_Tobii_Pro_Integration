"""
USB TTL Module Monitor UI
Real-time monitoring and control for USB TTL Module
"""

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets, QtCore, QtGui
import collections
import time
import logging

class USBTTLMonitorUI(Measurement):
    
    name = "USB TTL Monitor"
    
    def setup(self):
        """Initialize settings and data structures."""
        self.settings.New('max_log_entries', dtype=int, initial=1000, vmin=10)
        self.settings.New('enable_logging', dtype=bool, initial=True)
        
        # Internal buffer for log history
        self.log_buffer = collections.deque(maxlen=1000)
        
        # Reference to hardware
        self.ttl_hw = self.app.hardware['usb_ttl_module']
        
    def setup_figure(self):
        """Create UI widgets."""
        
        # Main container
        self.ui = QtWidgets.QGroupBox("USB TTL Module Monitor")
        layout = QtWidgets.QVBoxLayout()
        self.ui.setLayout(layout)
        
        # Status Indicator
        status_layout = QtWidgets.QHBoxLayout()
        status_label = QtWidgets.QLabel("Status:")
        self.status_indicator = QtWidgets.QLabel("Unknown")
        self.status_indicator.setStyleSheet("font-weight: bold; color: gray;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Activity Log
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QtGui.QFont("Consolas", 9)) # Monospace
        layout.addWidget(self.log_display)
        
        # Controls
        controls_layout = QtWidgets.QHBoxLayout()
        
        # Signal Value SpinBox
        self.signal_spinbox = QtWidgets.QSpinBox()
        self.signal_spinbox.setRange(0, 255)
        self.signal_spinbox.setDisplayIntegerBase(16) # Hex display
        self.signal_spinbox.setPrefix("0x")
        self.signal_spinbox.setValue(0x01)
        controls_layout.addWidget(QtWidgets.QLabel("Signal:"))
        controls_layout.addWidget(self.signal_spinbox)
        
        # Send Button
        self.send_btn = QtWidgets.QPushButton("Send Signal")
        self.send_btn.clicked.connect(self.on_send_test_clicked)
        controls_layout.addWidget(self.send_btn)
        
        # Reset Button
        self.reset_btn = QtWidgets.QPushButton("Reset HW")
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        controls_layout.addWidget(self.reset_btn)
        
        # Clear Log Button
        self.clear_btn = QtWidgets.QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.on_clear_log_clicked)
        controls_layout.addWidget(self.clear_btn)
        
        layout.addLayout(controls_layout)
        
        # Connect hardware status updates if available
        if self.ttl_hw:
            self.ttl_hw.settings.connection_status.add_listener(self.update_status_indicator)
            # Initial update
            self.update_status_indicator()

    def update_status_indicator(self):
        """Update status label color and text."""
        if not self.ttl_hw:
            return
            
        status = self.ttl_hw.settings['connection_status']
        self.status_indicator.setText(status)
        
        if status == 'Connected':
            self.status_indicator.setStyleSheet("font-weight: bold; color: green;")
        elif status == 'Simulated':
            self.status_indicator.setStyleSheet("font-weight: bold; color: #CCAA00;") # Dark yellow
        else:
            self.status_indicator.setStyleSheet("font-weight: bold; color: red;")

    def log_signal(self, value, status, latency_ms):
        """Log a signal transmission event."""
        if not self.settings['enable_logging']:
            return
            
        timestamp = time.strftime("%H:%M:%S")
        ms = int((time.time() % 1) * 1000)
        
        entry = f"[{timestamp}.{ms:03d}] 0x{value:02X} -> {status} ({latency_ms:.2f}ms)"
        self.log_message(entry)

    def log_message(self, message):
        """Append message to log."""
        self.log_buffer.append(message)
        self.log_display.append(message)
        
        # Scroll to bottom
        sb = self.log_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_send_test_clicked(self):
        """Handle manual signal sending."""
        if not self.ttl_hw:
            self.log_message("Error: Hardware not found")
            return
            
        value = self.signal_spinbox.value()
        start_time = time.time()
        
        try:
            success = self.ttl_hw.send_ttl_signal(value)
            latency = (time.time() - start_time) * 1000
            
            status = "SENT" if success else "FAILED"
            if self.ttl_hw.settings['simulated_mode']:
                status = "SIMULATED"
                
            self.log_signal(value, status, latency)
            
        except Exception as e:
            self.log_message(f"Error sending signal: {e}")

    def on_reset_clicked(self):
        """Handle hardware reset."""
        if not self.ttl_hw:
            return
            
        self.log_message("Resetting hardware...")
        success = self.ttl_hw.reset_hardware()
        if success:
            self.log_message("Hardware reset successful")
        else:
            self.log_message("Hardware reset failed")

    def on_clear_log_clicked(self):
        """Clear the log display."""
        self.log_display.clear()
        self.log_buffer.clear()

    def run(self):
        """Run loop (not used for this UI-only component)."""
        time.sleep(0.1)
