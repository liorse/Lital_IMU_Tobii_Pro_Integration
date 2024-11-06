from ScopeFoundry import HardwareComponent
import numpy as np
# import our low level device object class (previous section)
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from mbientlab.warble import *
from PyQt5.QtCore import pyqtSignal, QTime
import platform
import time
from threading import Event
import pdb
from time import sleep
e = Event()

class AccelerationData:
    def __init__(self, acceleration, time):
        self.acceleration = acceleration  # float for acceleration
        self.time = time  # QTime object for time

    def __repr__(self):
        return f"AccelerationData(acceleration={self.acceleration}, time={self.time.toString('HH:mm:ss')})"
    

class MetaMotionRLHW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'MetaMotionRL'
    acc_data_updated = pyqtSignal(AccelerationData)

    def __init__(self, app, name=None, debug=False, MAC="F3:F1:E2:D3:6E:A7"):
        self.debug = debug
        self.MAC = MAC
        self.name = name
        self.data_fusion_is_running = False
        HardwareComponent.__init__(self, app, name=name)
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.call_count = 0
        #self.e = Event()

    def setup(self):
        # I would need access to the following parameters
        # 1. data rate in HZ for the fusion algorithm
        # 2. choose linear acceleration in fusion algorithm - this should be chosen be default and not open to the user
        # 3. choose the range of the accelerometer in the fusion algorithm
        self.settings.New(name='MAC', initial=self.MAC, dtype=str, ro=False)
        self.settings.New(name='start_streaming', initial=False, dtype=bool, ro=False)
        self.settings.New(name='acceleration_range', initial= ('2G', "_2G"), dtype=str, ro=False, choices= [ ('2G', "_2G"), ('4G', "_4G"), ('8G', "_8G"), ('16G', "_16G") ])
        self.settings.New(name='data_rate', initial=21, dtype=int, ro=False, vmin = 1, vmax=200)
        self.settings.New(name='data_read_samples_per_second', initial=0, dtype=int, ro=True)
        self.add_operation(name='start_stream', op_func=self.start_data_fusion_stream_operation)
        self.add_operation(name='stop_stream', op_func=self.stop_data_fusion_stream_operation)
        self.add_operation(name='scan_for_devices', op_func=self.scan_for_devices)

    def scan_for_devices(self):
        print("Scanning for devices")
        BleScanner.start()
        sleep(10)
        BleScanner.stop()
        print("Scanning for devices complete")

    def data_handler(self, ctx, data):
        acc_data = parse_value(data)
        acc_data = np.sqrt(acc_data.x**2 + acc_data.y**2 + acc_data.z**2)
        self.acc_data_updated.emit(AccelerationData(acc_data, time.time()))

        #print("Linear Acceleration: ({0}, {1}, {2})".format(data.x, data.y, data.z))
        #print(parse_value(data), data.contents.epoch)
        # construct code to calculate the times per second this function is called
        current_time = time.time()
        if not hasattr(self, 'last_time'):
            self.last_time = current_time
            self.call_count = 0
        self.call_count += 1
        elapsed_time = current_time - self.last_time
        if elapsed_time >= 1.0:
            #self.settings.data_read_samples_per_second.value = self.call_count
            self.settings.data_read_samples_per_second.read_from_hardware()
            print(f"{self.name} called {self.call_count} times in the last second")
            self.call_count = 0
            self.last_time = current_time
        
        

    def start_data_fusion_stream(self, start):
        self.data_fusion_is_running = start
        if start:
            print("start Streaming")
            libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, SensorFusionData.LINEAR_ACC)
            libmetawear.mbl_mw_sensor_fusion_start(self.device.board)
        else:
            print("stop Streaming via button press")
            libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)

    def start_data_fusion_stream_operation(self):
        print("start Streaming")
        libmetawear.mbl_mw_sensor_fusion_enable_data(self.device.board, SensorFusionData.LINEAR_ACC)
        libmetawear.mbl_mw_sensor_fusion_start(self.device.board)
    
    def stop_data_fusion_stream_operation(self):
        print("stop Streaming")
        libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)
    
    def set_acceleration_range(self, range):
        if range == "_2G":
            self.app.log.info("set acceleration range to 2G")
            libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._2G)
        elif range == "_4G":
            self.app.log.info("set acceleration range to 4G")
            libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._4G)
        elif range == "_8G":
            self.app.log.info("set acceleration range to 8G")
            libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._8G)
        elif range == "_16G":
            self.app.log.info("set acceleration range to 16G")
            libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._16G)
        libmetawear.mbl_mw_sensor_fusion_write_config(self.device.board)

        # Define the callback function to process the configuration data
    def config_callback(self, context, data, something):
        print("Config readout callback was called")

    def get_acceleration_range(self):
        self.callback_config = FnVoid_VoidP_VoidP_Int(self.config_callback)
        libmetawear.mbl_mw_sensor_fusion_read_config(self.device.board, None, self.callback_config)

    def set_data_rate(self,data_rate):
        # calculate period
        period = int(1000/data_rate)
        libmetawear.mbl_mw_dataprocessor_time_modify_period(self.processor, period)    

    def read_call_count(self):
        return self.call_count
    
    def connect(self):
        # Open connection to the device:
        #BleScanner.start()

        #sleep(10.0)
        #BleScanner.stop()
        self.device = MetaWear(self.settings['MAC'])
        self.device.connect()

        print("Connected to " + self.device.address + " over " + ("USB" if self.device.usb.is_connected else "BLE"))
        print("Device information: " + str(self.device.info))

        # setup ble
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)
        # set tx power to max
        #libmetawear.mbl_mw_settings_set_tx_power(self.device.board, 4)
        
        e = Event()
        def processor_created(ctx, pointer):
            print("processor created")
            self.processor = pointer
            e.set()
        fn_wrapper = FnVoid_VoidP_VoidP(processor_created)
        # setup the device for streaming data
        print("Configuring fusion on meta device")

        libmetawear.mbl_mw_sensor_fusion_set_mode(self.device.board, SensorFusionMode.NDOF);
        libmetawear.mbl_mw_sensor_fusion_set_acc_range(self.device.board, SensorFusionAccRange._8G)
        libmetawear.mbl_mw_sensor_fusion_set_gyro_range(self.device.board, SensorFusionGyroRange._2000DPS)
        libmetawear.mbl_mw_sensor_fusion_write_config(self.device.board)

        self.signal = libmetawear.mbl_mw_sensor_fusion_get_data_signal(self.device.board, SensorFusionData.LINEAR_ACC)
        #libmetawear.mbl_mw_dataprocessor_time_create(self.signal, TimeMode.ABSOLUTE, 1000, None, FnVoid_VoidP_VoidP(self.processor_created))
        period = int(1000/self.settings.data_rate.value)
        libmetawear.mbl_mw_dataprocessor_time_create(self.signal, TimeMode.ABSOLUTE, period, None, fn_wrapper)
        e.wait()

        libmetawear.mbl_mw_datasignal_subscribe(self.processor, None, self.callback)
        #self.e.wait()

        self.settings.start_streaming.connect_to_hardware(write_func=self.start_data_fusion_stream)
        self.settings.acceleration_range.connect_to_hardware(write_func=self.set_acceleration_range, read_func=self.get_acceleration_range)
        self.settings.data_rate.connect_to_hardware(write_func=self.set_data_rate)
        self.settings.data_read_samples_per_second.connect_to_hardware(read_func=self.read_call_count)
        
        self.read_from_hardware()
  
    def disconnect(self):

        # disconnect from hardware
        try:
            
            #libmetawear.mbl_mw_sensor_fusion_start(self.device.board)
            if self.data_fusion_is_running:
                print("stop streaming via hardware disconnect")
                libmetawear.mbl_mw_sensor_fusion_stop(self.device.board)
                # this delay is necessary to allow the device to stop streaming. because if I call disconnect immediately after stopping the streaming, the device will not disconnect
                # the software breaks
                time.sleep(1)
            
            # unsubscribe from data signal
            #libmetawear.mbl_mw_datasignal_unsubscribe(self.signal)
            #libmetawear.mbl_mw_macro_erase_all(self.device.board)
            #libmetawear.mbl_mw_debug_reset_after_gc(self.device.board)
            #libmetawear.mbl_mw_debug_disconnect(self.device.board)
            #time.sleep(2)
            #libmetawear.mbl_mw_metawearboard_tear_down(self.device.board)  # deletes data processors 
            #time.sleep(1)
            #self.device.disconnect()
            e = Event()
            self.device.on_disconnect = lambda s: e.set()
            libmetawear.mbl_mw_debug_reset(self.device.board)
            e.wait()
        
        except AttributeError:
            print("called before device was connected")
            
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        #if hasattr(self, 'randgen_dev'):
        #    del self.randgen_dev
