import pytest
from unittest.mock import Mock, MagicMock, patch, call
import serial
from HW_USB_TTL import USBTTLHardware

def test_connect_to_hardware(mock_serial, mock_app):
    """Test successful hardware connection"""
    hw = USBTTLHardware(app=mock_app, port='COM3')
    hw.setup()
    
    # Mock settings dictionary behavior
    hw.settings = MagicMock()
    hw.settings.__getitem__.side_effect = lambda k: 'COM3' if k == 'port' else None
    
    result = hw.connect()

    assert result == True
    
    # Verify serial port opened with correct params
    serial.Serial.assert_called_once_with(
        port='COM3',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=5.0,
        write_timeout=0.1,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False
    )

    # Verify initialization command sent
    assert mock_serial.write.call_count >= 1
    # Check if 'RR' was sent. Note: write takes bytes
    mock_serial.write.assert_any_call(b'RR')

def test_send_ttl_signal(mock_serial, mock_app):
    """Test sending TTL signal"""
    hw = USBTTLHardware(app=mock_app, port='COM3')
    hw.setup()
    
    # Mock settings
    hw.settings = MagicMock()
    hw.settings.__getitem__.side_effect = lambda k: 'COM3' if k == 'port' else None
    
    hw.connect()

    # Send signal
    result = hw.send_ttl_signal(0x42)

    assert result == True
    mock_serial.write.assert_called_with(b'42')

@pytest.mark.parametrize("value,expected", [
    (0, b'00'),
    (1, b'01'),
    (255, b'FF'),
    (0x42, b'42'),
])
def test_value_encoding(mock_serial, mock_app, value, expected):
    """Test hex value encoding"""
    hw = USBTTLHardware(app=mock_app, port='COM3')
    hw.setup()
    
    # Mock settings
    hw.settings = MagicMock()
    hw.settings.__getitem__.side_effect = lambda k: 'COM3' if k == 'port' else None
    
    hw.connect()
    hw.send_ttl_signal(value)

    mock_serial.write.assert_called_with(expected)

def test_simulated_mode_fallback(mock_app):
    """Test automatic fallback to simulated mode"""
    with patch('serial.Serial', side_effect=serial.SerialException("Port not found")):
        hw = USBTTLHardware(app=mock_app, port='COM99')
        hw.setup()
        
        # Mock settings
        hw.settings = MagicMock()
        hw.settings.__getitem__.side_effect = lambda k: 'COM99' if k == 'port' else None
        
        result = hw.connect()

        assert result == False  # Connection failed
        
        # Verify settings updated (mocked)
        hw.settings.__setitem__.assert_any_call('connection_status', 'Simulated')
        hw.settings.__setitem__.assert_any_call('simulated_mode', True)

        # Should still accept commands in simulated mode
        # We need to manually set simulated_mode on the instance if connect failed to set it on the real object
        # But here we are mocking settings, so we rely on implementation logic.
        # The implementation sets self.serial_handle = None
        
        assert hw.send_ttl_signal(0x01) == True

def test_invalid_values(mock_app):
    """Test validation of signal values"""
    hw = USBTTLHardware(app=mock_app)
    
    with pytest.raises(ValueError):
        hw.send_ttl_signal(-1)
        
    with pytest.raises(ValueError):
        hw.send_ttl_signal(256)
        
    with pytest.raises(ValueError):
        hw.send_ttl_signal("invalid")
