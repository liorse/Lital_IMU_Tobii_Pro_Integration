import pytest
from unittest.mock import Mock, MagicMock, patch
from HW_USB_TTL import USBTTLHardware
import time

def test_full_workflow(mock_app, mock_serial):
    """
    Integration test simulating a full experimental workflow:
    Connect -> Send Signals -> Disconnect
    """
    # 1. Setup
    hw = USBTTLHardware(app=mock_app, port='COM3')
    hw.setup()
    
    # Mock settings
    hw.settings = MagicMock()
    hw.settings.__getitem__.side_effect = lambda k: 'COM3' if k == 'port' else None

    # 2. Connect
    assert hw.connect() == True
    mock_serial.write.assert_any_call(b'RR') # Verify reset on connect
    
    # 3. Send Signals (Simulate Experiment)
    
    # Experiment Start
    hw.send_ttl_signal(0x01)
    mock_serial.write.assert_called_with(b'01')
    
    # Mobile Stimulus On
    hw.send_ttl_signal(0x10)
    mock_serial.write.assert_called_with(b'10')
    
    # Mobile Stimulus Off
    hw.send_ttl_signal(0x11)
    mock_serial.write.assert_called_with(b'11')
    
    # Experiment Stop
    hw.send_ttl_signal(0x02)
    mock_serial.write.assert_called_with(b'02')
    
    # 4. Disconnect
    hw.disconnect()
    
    # Verify reset sent before close
    # We expect b'RR' to be called at least twice (connect and disconnect)
    assert mock_serial.write.call_count >= 6 # RR, 01, 10, 11, 02, RR
    mock_serial.close.assert_called_once()

def test_error_recovery_workflow(mock_app):
    """
    Integration test simulating hardware failure during experiment
    """
    # 1. Setup & Connect (Success initially)
    with patch('serial.Serial') as mock_serial_cls:
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_instance.write.return_value = 2
        mock_serial_cls.return_value = mock_instance
        
        hw = USBTTLHardware(app=mock_app, port='COM3')
        hw.setup()
        
        # Mock settings
        hw.settings = MagicMock()
        hw.settings.__getitem__.side_effect = lambda k: 'COM3' if k == 'port' else None
        
        hw.connect()
        
        # 2. Send Signal (Success)
        hw.send_ttl_signal(0x01)
        
        # 3. Hardware Failure (Simulate unplug/error)
        # Make write raise exception
        mock_instance.write.side_effect = Exception("Device disconnected")
        
        # 4. Send Signal (Should fail gracefully but not crash)
        result = hw.send_ttl_signal(0x10)
        assert result == False
        
        # 5. Disconnect (Should handle error)
        hw.disconnect()
        mock_instance.close.assert_called()
