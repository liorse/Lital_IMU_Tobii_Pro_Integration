from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import zmq
import subprocess
import atexit

class MobileControllerUI(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "Mobile Control"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "Mobile.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        
        # mobile settings
        self.settings.New('acceleration_threshold', dtype=float, unit='g', initial=0.6, vmin=0.0, vmax=16.0)
        self.settings.New('min_movie_speed', dtype=float, unit='fps', initial=60, vmin=0, vmax=70)
        self.settings.New('max_movie_speed', dtype=float, unit='fps', initial=90, vmin=0, vmax=151)
        self.settings.New('min_sound_speed', dtype=float, unit='', initial=1.0, vmin=1.0, vmax=5.0)
        self.settings.New('max_sound_speed', dtype=float, unit='', initial=2.0, vmin=1.0, vmax=5.0)
        self.settings.New('min_sound_volume', dtype=float, unit='', initial=0.1, vmin=0.1, vmax=1.5)
        self.settings.New('max_sound_volume', dtype=float, unit='', initial=1.5, vmin=0.1, vmax=1.5)
        self.settings.New('max_acceleration', dtype=float, unit='g', initial=1.0, vmin=1.0, vmax=8)
        self.settings.New('min_acceleration', dtype=float, unit='g', initial=0.0, vmin=0.0, vmax=0.99)

        self.settings.New(name='limb_connected_to_mobile', initial= ('Left Hand', "_left_hand"), dtype=str, ro=False, choices= [ ('Left Hand', "_left_hand"), ('Right Hand', "_right_hand"), ('Left Leg', "_left_leg"), ('Right Leg', "_right_leg"), ('None', "_none")])
        self.settings.limb_connected_to_mobile.connect_to_hardware(write_func=self.set_limb_mobile_connection)
        
        # Define how often to update display during a run
        self.display_update_period = 1/60
        
        # Convenient reference to the hardware used in the measurement
        self.LeftHandMeta = self.app.hardware['LeftHandMeta']
        self.RightHandMeta = self.app.hardware['RightHandMeta']
        self.LeftLegMeta = self.app.hardware['LeftLegMeta']
        self.RightLegMeta = self.app.hardware['RightLegMeta']
        DataLength = 500
        self.buffer = np.zeros(DataLength)

        self.mapped_value_sound_speed = 0
        self.mapped_value_sound_volume = 0

        

    def set_limb_mobile_connection(self, limb_connected_to_mobile):

        if self.current_limb_connected_to_mobile == "_left_hand":
            self.LeftHandMeta.acc_data_updated.disconnect(self.update_mobile_with_acc)
            self.LeftHandMeta.acc_data_updated.disconnect(self.update_sound_with_acc)
        elif self.current_limb_connected_to_mobile == "_right_hand":
            self.RightHandMeta.acc_data_updated.disconnect(self.update_mobile_with_acc)
            self.RightHandMeta.acc_data_updated.disconnect(self.update_sound_with_acc)
        elif self.current_limb_connected_to_mobile == "_left_leg":
            self.LeftLegMeta.acc_data_updated.disconnect(self.update_mobile_with_acc)
            self.LeftLegMeta.acc_data_updated.disconnect(self.update_sound_with_acc)
        elif self.current_limb_connected_to_mobile == "_right_leg":
            self.RightLegMeta.acc_data_updated.disconnect(self.update_mobile_with_acc)
            self.RightLegMeta.acc_data_updated.disconnect(self.update_sound_with_acc)
        elif self.current_limb_connected_to_mobile == "_none":
            pass

        if limb_connected_to_mobile == "_left_hand":
            self.LeftHandMeta.acc_data_updated.connect(self.update_mobile_with_acc)
            self.LeftHandMeta.acc_data_updated.connect(self.update_sound_with_acc)
        elif limb_connected_to_mobile == "_right_hand":
            self.RightHandMeta.acc_data_updated.connect(self.update_mobile_with_acc)
            self.RightHandMeta.acc_data_updated.connect(self.update_sound_with_acc)
        elif limb_connected_to_mobile == "_left_leg":
            self.LeftLegMeta.acc_data_updated.connect(self.update_mobile_with_acc)
            self.LeftLegMeta.acc_data_updated.connect(self.update_sound_with_acc)
        elif limb_connected_to_mobile == "_right_leg":
            self.RightLegMeta.acc_data_updated.connect(self.update_mobile_with_acc)
            self.RightLegMeta.acc_data_updated.connect(self.update_sound_with_acc)
        elif limb_connected_to_mobile == "_none":
            pass

        self.current_limb_connected_to_mobile = limb_connected_to_mobile
    
    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def update_mobile_with_acc(self, acc_data):
        # control the speed of the movie based on the acceleration of the left hand
        mapped_value = int(self.map_value(acc_data.acceleration, 
                                          self.ui.min_acceleration_spinBox.value(), 
                                          self.ui.max_acceleration_spinBox.value(), 
                                          self.ui.min_movie_speed_spinBox.value(), 
                                          self.ui.max_movie_speed_spinBox.value()))
        capped_value = max(self.ui.min_movie_speed_spinBox.value(), min(mapped_value, self.ui.max_movie_speed_spinBox.value()))  # Cap the value between 0 and 200
        if acc_data.acceleration < self.ui.acceleration_threshold_spinBox.value():
            capped_value = 0
        #self.socket.send_string(str(int(capped_value)))
        if hasattr(self, 'socket'):
            try:
                self.socket.send_multipart([b"mobile_movie", str(int(capped_value)).encode('utf-8')])
            except zmq.error.ZMQError as e:
                pass

        #print(f"Left Hand Acceleration: {acc_data.acceleration}, Mapped Value: {capped_value}")

    def update_sound_with_acc(self, acc_data):
        # control the speed and volume of the sound based on the acceleration of the left hand
        mapped_value_sound_speed = self.map_value(acc_data.acceleration, 
                                                  self.ui.min_acceleration_spinBox.value(), 
                                                  self.ui.max_acceleration_spinBox.value(), 
                                                  self.ui.min_sound_speed_spinBox.value(), 
                                                  self.ui.max_sound_speed_spinBox.value())
        mapped_value_sound_volume = self.map_value(acc_data.acceleration, 
                                                   self.ui.min_acceleration_spinBox.value(), 
                                                   self.ui.max_acceleration_spinBox.value(), 
                                                   self.ui.min_sound_volume_spinBox.value(), 
                                                   self.ui.max_sound_volume_spinBox.value())
        
        if mapped_value_sound_speed > self.ui.max_sound_speed_spinBox.value():
            mapped_value_sound_speed = self.ui.max_sound_speed_spinBox.value()
        if mapped_value_sound_volume > self.ui.max_sound_volume_spinBox.value():
            mapped_value_sound_volume = self.ui.max_sound_volume_spinBox.value()
    
        if acc_data.acceleration < self.ui.acceleration_threshold_spinBox.value():
            # make it silent but keep the speed of the sound @ 1.0 to maintain the speed of reacting to the acceleration
            mapped_value_sound_speed = 1.0
            mapped_value_sound_volume = 0.1
        
        # round to 1 decimal place both mapped values and send value only if it has changed
        mapped_value_sound_speed = round(mapped_value_sound_speed, 1)
        mapped_value_sound_volume = round(mapped_value_sound_volume, 1)
        
        if self.mapped_value_sound_speed != mapped_value_sound_speed and self.mapped_value_sound_volume != mapped_value_sound_volume:
            message = f"{mapped_value_sound_speed},{mapped_value_sound_volume}"
            if hasattr(self, 'socket_sound'):
                try:
                    self.socket_sound.send_string(message)
                except zmq.error.ZMQError as e:
                    pass
            self.mapped_value_sound_speed = mapped_value_sound_speed
            self.mapped_value_sound_volume = mapped_value_sound_volume
            #print(f"Left Hand Acceleration: {acc_data.acceleration}, Mapped Value Sound Speed: {mapped_value_sound_speed}, Mapped Value Sound Volume: {mapped_value_sound_volume}")

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)

        # Set up limb connected to mobile
        self.settings.limb_connected_to_mobile.connect_to_widget(self.ui.Limb_connected_to_mobile_ComboBox)
        self.current_limb_connected_to_mobile = "_left_hand"
        self.LeftHandMeta.acc_data_updated.connect(self.update_mobile_with_acc)
        self.LeftHandMeta.acc_data_updated.connect(self.update_sound_with_acc)

        self.settings.max_acceleration.connect_to_widget(self.ui.max_acceleration_spinBox)
        self.settings.min_acceleration.connect_to_widget(self.ui.min_acceleration_spinBox)

        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # connect to data update signal
        self.ui.start_stimuli_pushButton.clicked.connect(self.start)
        self.ui.stop_stimuli_pushButton.clicked.connect(self.interrupt)
        self.ui.fps_spinBox.valueChanged.connect(self.update_fps)
        self.ui.sound_volume_spinBox.valueChanged.connect(self.update_sound_volume_and_speed)
        self.ui.sound_speed_spinBox.valueChanged.connect(self.update_sound_volume_and_speed)
        self.settings.acceleration_threshold.connect_to_widget(self.ui.acceleration_threshold_spinBox)
        self.settings.min_movie_speed.connect_to_widget(self.ui.min_movie_speed_spinBox)
        self.settings.max_movie_speed.connect_to_widget(self.ui.max_movie_speed_spinBox)
        self.settings.min_sound_speed.connect_to_widget(self.ui.min_sound_speed_spinBox)
        self.settings.max_sound_speed.connect_to_widget(self.ui.max_sound_speed_spinBox)
        self.settings.min_sound_volume.connect_to_widget(self.ui.min_sound_volume_spinBox)
        self.settings.max_sound_volume.connect_to_widget(self.ui.max_sound_volume_spinBox)

        #self.RightHandMeta.acc_data_updated.connect(self.update_right_hand_data)
        #self.LeftLegMeta.acc_data_updated.connect(self.update_left_leg_data)
        #self.RightLegMeta.acc_data_updated.connect(self.update_right_leg_data)

    def update_sound_volume_and_speed(self):
        message = f"{self.ui.sound_speed_spinBox.value()},{self.ui.sound_volume_spinBox.value()}"
        if hasattr(self, 'socket_sound'):
            self.socket_sound.send_string(message)

    def update_fps(self):
         if hasattr(self, 'socket'):
            self.socket.send_multipart([b"mobile_movie", str(int(self.ui.fps_spinBox.value())).encode('utf-8')])

    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        pass

    def terminate_stimuli_process(self):
        try:
            self.stimuli_process.terminate()
            self.stimuli_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.stimuli_process.kill()
    
    def terminate_stimuli_sound_process(self):
        try:
            self.stimuli_sound_process.terminate()
            self.stimuli_sound_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.stimuli_sound_process.kill()
        
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        

        # first, create a data file
        if self.settings['save_h5']:
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file
            
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
            
            
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        
        # setup the zeromq server to both visual and sound servers
        print("setup zmq server for visuals")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://localhost:5555")  # Bind to the port to allow connections

        print("setup zmq server for sound")
        self.context_sound = zmq.Context()
        self.socket_sound = self.context_sound.socket(zmq.PUB)
        self.socket_sound.bind("tcp://localhost:5556")  # Bind to the port to allow connections

        # run the stimuli visualizer in a seperate process using the shell
        self.stimuli_process = subprocess.Popen(["python", "stimuli_visualizer.py"])
        atexit.register(self.terminate_stimuli_process)

        # run the stimuli sound in a seperate process using the shell
        self.stimuli_sound_process = subprocess.Popen(["python", "stimuli_sound_pygame_midi.py"])
        atexit.register(self.terminate_stimuli_sound_process)

        #self.LeftHandMeta.acc_data_updated.connect(self.update_mobile_with_acc)
        #self.LeftHandMeta.acc_data_updated.connect(self.update_sound_with_acc)

        try:
            i = 0
            
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                i %= len(self.buffer)
                
                # Set progress bar percentage complete
                self.settings['progress'] = i * 100./len(self.buffer)
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                time.sleep(self.settings['sampling_period'])
                
                i += 1

                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    break

        finally:            

            # close the stimuli visualizer
            print("close down stimuli visualizer")
            self.stimuli_process.terminate()
            print("close down stimuli sound")
            self.stimuli_sound_process.terminate()

            #self.LeftHandMeta.acc_data_updated.disconnect(self.update_mobile_with_acc)
            #self.LeftHandMeta.acc_data_updated.disconnect(self.update_sound_with_acc)
            print("Experiment is finished")
            print("close down zmq server visual")
            self.socket.close()
            self.context.term()
            print("close down zmq server sound")
            self.socket_sound.close()
            self.context_sound.term()
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
