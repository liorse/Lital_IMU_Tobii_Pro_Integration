from ScopeFoundry import HardwareComponent
# import our low level device object class (previous section)
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import * 
import platform
import time

class MetaMotionRLHW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'MetaMotionRL'

    def __init__(self, app, name=None, debug=False, MAC="F3:F1:E2:D3:6E:A7"):
        self.debug = debug
        self.MAC = MAC
        self.data_fusion_is_running = False
        HardwareComponent.__init__(self, app, name=name)

    def setup(self):
        # I would need access to the following parameters
        # 1. data rate in HZ for the fusion algorithm
        # 2. choose linear acceleration in fusion algorithm - this should be chosen be default and not open to the user
        # 3. choose the range of the accelerometer in the fusion algorithm
        self.settings.New(name='MAC', initial=self.MAC, dtype=str, ro=True)
        self.settings.New(name='start_streaming', initial=False, dtype=bool, ro=False)
        
        
    def data_handler(self, ctx, data):
        #print("Linear Acceleration: ({0}, {1}, {2})".format(data.x, data.y, data.z))
        print(parse_value(data))

    def start_data_fusion_stream(self, start):
        self.data_fusion_is_running = start
        if start:
            print("start Streaming")
            libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, SensorFusionData.LINEAR_ACC)
            libmetawear.mbl_mw_sensor_fusion_start(self.device.board)
        else:
            print("stop Streaming via button press")
            libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)

    def connect(self):
        # Open connection to the device:
        self.device = MetaWear(self.settings['MAC'])
        self.device.connect()

        print("Connected to " + self.device.address + " over " + ("USB" if self.device.usb.is_connected else "BLE"))
        print("Device information: " + str(self.device.info))

        # Set the linear acceleration in the fusion algorithm
        #self.set_linear_acc_in_fusion()
        # Set the fusion algorithm to linear acceleration
        #self.set_fusion_to_LinAcc()
        
        # setup the device for streaming data
        self.callback = FnVoid_VoidP_DataP(self.data_handler)

        print("Configuring fusion on meta device")

        libmetawear.mbl_mw_sensor_fusion_set_mode(self.device.board, SensorFusionMode.NDOF);
        libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._8G)
        libmetawear.mbl_mw_sensor_fusion_set_gyro_range(self.device.board, SensorFusionGyroRange._2000DPS)
        libmetawear.mbl_mw_sensor_fusion_write_config(self.device.board)

        self.signal = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, SensorFusionData.LINEAR_ACC)
        libmetawear.mbl_mw_datasignal_subscribe(self.signal, None, self.callback)
        
        self.settings.start_streaming.connect_to_hardware(write_func=self.start_data_fusion_stream)
   
    
    def disconnect(self):

        # disconnect from hardware
        self.settings.disconnect_all_from_hardware()
        try:
            
            #libmetawear.mbl_mw_sensor_fusion_start(self.device.board)
            if self.data_fusion_is_running:
                print("stop streaming via hardware disconnect")
                libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)
                # this delay is necessary to allow the device to stop streaming. because if I call disconnect immediately after stopping the streaming, the device will not disconnect
                # the software breaks
                time.sleep(1)
            libmetawear.mbl_mw_datasignal_unsubscribe(self.signal)
            self.device.disconnect()
            # unsubscribe from data signal
            

        except AttributeError:
            print("called before device was connected")
            
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        #if hasattr(self, 'randgen_dev'):
        #    del self.randgen_dev
