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
            try:
                # Reset all outputs before disconnect
                self.serial_handle.write(b'RR')
                time.sleep(0.05)
                self.serial_handle.close()
                log.info("USBTTLHardware: Serial port closed")
            except Exception as e:
                log.error(f"USBTTLHardware: Error during disconnect: {e}")

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
