from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time

# this class is used to store the acceleration data buffer and its corresponding time buffer
class AccelerationDataBuffer(object):
    def __init__(self, buffer_size):
        self.buffer_size = buffer_size
        self.acceleration_data = np.zeros(buffer_size, dtype=float)
        self.time_data = np.zeros(buffer_size, dtype=float)

    def add_data(self, acc_data, time_data):
        self.acceleration_data = np.roll(self.acceleration_data, 1)
        self.acceleration_data[0] = acc_data
        self.time_data = np.roll(self.time_data, 1)
        self.time_data[0] = time_data

    def get_data(self):
        return self.acceleration_data, self.time_data


class MetaWearUI(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "MetaWearControl"
    
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
        self.ui_filename = sibling_path(__file__, "Agency.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        
        # Define how often to update display during a run
        self.display_update_period = 1/60
        
        # Convenient reference to the hardware used in the measurement
        self.LeftHandMeta = self.app.hardware['LeftHandMeta']
        self.RightHandMeta = self.app.hardware['RightHandMeta']
        self.LeftLegMeta = self.app.hardware['LeftLegMeta']
        self.RightLegMeta = self.app.hardware['RightLegMeta']

        # data
        DataLength = 500
        self.buffer = np.zeros(DataLength)
        self.lefthand_data = AccelerationDataBuffer(DataLength)
        self.righthand_data = AccelerationDataBuffer(DataLength)
        self.leftleg_data = AccelerationDataBuffer(DataLength)
        self.rightleg_data = AccelerationDataBuffer(DataLength)

    def connect(self):
        self.LeftHandMeta.settings['connected'] = True
        self.RightHandMeta.settings['connected'] = True
        #self.LeftLegMeta.settings['connected'] = True
        #self.RightLegMeta.settings['connected'] = True

    def disconnect(self):
        self.LeftHandMeta.settings['connected'] = False
        self.RightHandMeta.settings['connected'] = False
        #self.LeftLegMeta.settings['connected'] = False
        #self.RightLegMeta.settings['connected'] = False

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        # start and interrupt methods are predefined in Measurement class
        self.ui.connect_pushButton.clicked.connect(self.connect)
        self.ui.disconnect_pushButton.clicked.connect(self.disconnect)
        self.ui.start_stream_pushButton.clicked.connect(self.start)
        self.ui.stop_stream_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
       
        # Connect settings to hardware operations
        self.LeftHandMeta.settings.data_rate.connect_to_widget(self.ui.datarate_spinBox)
        self.RightHandMeta.settings.data_rate.connect_to_widget(self.ui.datarate_spinBox)
        self.LeftLegMeta.settings.data_rate.connect_to_widget(self.ui.datarate_spinBox)
        self.RightLegMeta.settings.data_rate.connect_to_widget(self.ui.datarate_spinBox)

        self.LeftHandMeta.settings.start_streaming.connect_to_widget(self.ui.LeftArmStreamCheckBox)
        self.RightHandMeta.settings.start_streaming.connect_to_widget(self.ui.RightArmStreamCheckBox)
        self.LeftLegMeta.settings.start_streaming.connect_to_widget(self.ui.LeftLegStreamCheckBox)
        self.RightLegMeta.settings.start_streaming.connect_to_widget(self.ui.RightLegStreamCheckBox)

        self.LeftHandMeta.settings.connected.connect_to_widget(self.ui.LeftArmConnectCheckBox)
        self.RightHandMeta.settings.connected.connect_to_widget(self.ui.RightArmConnectCheckBox)
        self.LeftLegMeta.settings.connected.connect_to_widget(self.ui.LeftLegConnectCheckBox)
        self.RightLegMeta.settings.connected.connect_to_widget(self.ui.RightLegConnectCheckBox)          

        self.LeftHandMeta.settings.data_read_samples_per_second.connect_to_widget(self.ui.left_hand_spinbox)
        self.RightHandMeta.settings.data_read_samples_per_second.connect_to_widget(self.ui.right_hand_spinbox)
        self.LeftLegMeta.settings.data_read_samples_per_second.connect_to_widget(self.ui.left_leg_spinbox)
        self.RightLegMeta.settings.data_read_samples_per_second.connect_to_widget(self.ui.right_leg_spinbox)

        
        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # Create PlotItem object (a set of axes)  
        self.plot = self.graph_layout.addPlot(title="Acceleration Data", axisItems={'bottom': pg.DateAxisItem()})
        self.plot.enableAutoRange('y', False) # allow manual y-axis range adjustment
        self.plot.setYRange(0, 2) # set initial y-axis range

        # Create PlotDataItem object ( a scatter plot on the axes )
        self.lefthand_plot = self.plot.plot(pen='r', name = "left hand acc")  # a line in the plot for the data
        # anothe line in the plot for all the other data
        self.righthand_plot = self.plot.plot(pen='g', name = "right hand acc")

        # connect to data update signal
        self.LeftHandMeta.acc_data_updated.connect(self.update_left_hand_data)
        self.RightHandMeta.acc_data_updated.connect(self.update_right_hand_data)
        self.LeftLegMeta.acc_data_updated.connect(self.update_left_leg_data)
        self.RightLegMeta.acc_data_updated.connect(self.update_right_leg_data)

    def update_left_leg_data(self, acc_data):
        #print(f"Acceleration of {self.LeftLegMeta.MAC}: {acc_data}")
        # add acc_data to the buffer to left leg data
        self.lefthand_data.add_data(acc_data.acceleration, acc_data.time)

    def update_right_leg_data(self, acc_data):
        #print(f"Acceleration of {self.RightLegMeta.MAC}: {acc_data}")
        # add acc_data to the buffer to right leg data
        self.righthand_data.add_data(acc_data.acceleration, acc_data.time)

    def update_left_hand_data(self, acc_data):
        #print(f"Acceleration of {self.LeftHandMeta.MAC}: {acc_data}")
        # add acc_data to the buffer to left hand data
        self.lefthand_data.add_data(acc_data.acceleration, acc_data.time)
        
    def update_right_hand_data(self, acc_data):
        #print(f"Acceleration of {self.RightHandMeta.MAC}: {acc_data}")
        # add acc_data to the buffer to right hand data
        self.righthand_data.add_data(acc_data.acceleration, acc_data.time)

    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.lefthand_plot.setData(self.lefthand_data.time_data, self.lefthand_data.acceleration_data)
        self.righthand_plot.setData(self.righthand_data.time_data, self.righthand_data.acceleration_data) 

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
            
            # create an h5 dataset to store the data
            self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
                                                          shape = self.buffer.shape,
                                                          dtype = self.buffer.dtype)
        
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        self.LeftHandMeta.settings['start_streaming'] = True
        self.RightHandMeta.settings['start_streaming'] = True
        self.LeftLegMeta.settings['start_streaming'] = True
        self.RightLegMeta.settings['start_streaming'] = True
        #self.LeftHandMeta.operations['start_stream']()
        #self.RightHandMeta.operations['start_stream']()
        #self.LeftLegMeta.operations['start_stream']()
        #self.RightLegMeta.operations['start_stream']()

        try:
            i = 0
            
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                i %= len(self.buffer)
                
                # Set progress bar percentage complete
                self.settings['progress'] = i * 100./len(self.buffer)
                
                # Fills the buffer with sine wave readings from func_gen Hardware
                #self.buffer[i] = self.func_gen.settings.sine_data.read_from_hardware()
                
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.buffer_h5[i] = self.buffer[i]
                    # flush H5
                    self.h5file.flush()
                
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
                    # an interrupt request
                    self.RightHandMeta.settings['start_streaming'] = False
                    self.LeftHandMeta.settings['start_streaming'] = False
                    self.RightLegMeta.settings['start_streaming'] = False
                    self.LeftLegMeta.settings['start_streaming'] = False
                    #self.RightHandMeta.operations['stop_stream']()
                    #self.LeftHandMeta.operations['stop_stream']()
                    #self.RightLegMeta.operations['stop_stream']()
                    #self.LeftLegMeta.operations['stop_stream']()
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()