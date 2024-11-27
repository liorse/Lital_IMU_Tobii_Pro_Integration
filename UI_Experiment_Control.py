from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import zmq
import subprocess

class ExperimentControllerUI(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "Task Management"
    
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
        self.ui_filename = sibling_path(__file__, "Experiment.UI")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        
        # Experiment Specific Settings
        self.settings.New('acceleration_threshold', dtype=float, unit='g', initial=0.6, vmin=0.0, vmax=16.0)
        # participants settings
        self.settings.New('participant', dtype=int, unit='', initial=5000, vmin=5000, vmax=5999)
        self.settings.New('age', dtype=int, unit='months', initial=4, vmin=0, vmax=96)

        self.settings.New('task_name', initial= ('Mobile', "Mobile"), dtype=str, choices= [ ('Mobile', "Mobile")])
        self.settings.New('trial_number', dtype=int, initial=1 ,vmin=1, vmax=100)
        self.settings.New('task_ID', dtype=str, initial='', ro=True)
        
        # Define how often to update display during a run
        self.display_update_period = 1/60
        
        # Convenient reference to the hardware used in the measurement
        self.LeftHandMeta = self.app.hardware['LeftHandMeta']
        self.RightHandMeta = self.app.hardware['RightHandMeta']
        self.LeftLegMeta = self.app.hardware['LeftLegMeta']
        self.RightLegMeta = self.app.hardware['RightLegMeta']

        DataLength = 500
        self.buffer = np.zeros(DataLength)


    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        self.settings.participant.connect_to_widget(self.ui.Participant_spinBox)
        self.settings.age.connect_to_widget(self.ui.age_spinBox)
        self.settings.task_name.connect_to_widget(self.ui.task_name_ComboBox)
        self.settings.trial_number.connect_to_widget(self.ui.trial_number_spinBox)
        self.settings.task_ID.connect_to_widget(self.ui.Task_ID_QLine_edit)

        self.ui.Participant_spinBox.valueChanged.connect(self.update_task_ID)
        self.ui.age_spinBox.valueChanged.connect(self.update_task_ID)
        self.ui.task_name_ComboBox.currentIndexChanged.connect(self.update_task_ID)
        self.ui.trial_number_spinBox.valueChanged.connect(self.update_task_ID)

        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # connect to data update signal
        self.ui.start_stimuli_pushButton.clicked.connect(self.start)
        self.ui.stop_stimuli_pushButton.clicked.connect(self.interrupt)
        
    def update_task_ID(self):
        # construct task ID according to the following format:
        # task_name.YYYY.MM.DD.participant.age.trial_number
        task_name = self.settings['task_name']
        participant = self.settings['participant']
        age = f"{self.settings['age']:02d}"
        trial_number = f"{self.settings['trial_number']:03d}"
        current_date = time.strftime("%Y.%m.%d")
        task_ID = f"{task_name}.{current_date}.{participant}.{age}.{trial_number}"
        self.settings['task_ID'] = task_ID


    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        pass

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
                    break

        finally:            

            print("Experiment is finished")
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
