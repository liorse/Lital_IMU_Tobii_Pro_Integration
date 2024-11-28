from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import zmq
import subprocess
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex
from PyQt5.QtWidgets import (
    QComboBox, QCheckBox, QWidget, QStyleOptionComboBox, QStyleOptionButton, QStyle,
    QStyledItemDelegate, QTableView, QVBoxLayout, QHeaderView, QApplication, QSizePolicy
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
# add QEvent to the list of imports
from PyQt5.QtCore import QEvent
from typing import Optional

# add relevent imports
from PyQt5.QtCore import QRect, QSize, QEvent
from PyQt5.QtCore import QAbstractItemModel, QEvent, QModelIndex
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QStyleOptionViewItem
import yaml
import pygame
from apscheduler.schedulers.background import BackgroundScheduler


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.items)
        combo.setStyleSheet("QComboBox { text-align: center; }")
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            editor.setCurrentText(value)
        editor.setStyleSheet("QComboBox { text-align: center; }")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

'''
class CheckBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # No editor for checkboxes
        return None

    def paint(self, painter, option, index):
        pass
        
        # Get the checkbox state from the model
        value = index.data(Qt.CheckStateRole)

        # Create and configure a QStyleOptionButton for the checkbox
        checkbox_style = QStyleOptionButton()
        checkbox_style.state = QStyle.State_Enabled
        checkbox_style.state |= QStyle.State_On if value == Qt.Checked else QStyle.State_Off

        # Determine the size of the checkbox
        checkbox_size = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, checkbox_style).size()

        # Center the checkbox within the cell
        checkbox_rect = option.rect
        checkbox_rect.setWidth(checkbox_size.width())
        checkbox_rect.setHeight(checkbox_size.height())
        checkbox_rect.moveCenter(option.rect.center())

        checkbox_style.rect = checkbox_rect

        # Draw the checkbox
        QApplication.style().drawControl(QStyle.CE_CheckBox, checkbox_style, painter)
        

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            current_value = index.data(Qt.CheckStateRole)
            new_value = Qt.Unchecked if current_value == Qt.Checked else Qt.Checked
            model.setData(index, new_value, Qt.CheckStateRole)
            return True
        return False
'''
class CheckBoxDelegate(QStyledItemDelegate):

    def __init__(self, alignment: Qt.Alignment, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.alignment: Qt.Alignment = alignment
        self.parent = parent

        if self.parent:
            self.style = self.parent.style()
        else:
            self.style = QApplication.style()

    def editorEvent(self, event: QMouseEvent, model: QAbstractItemModel, option: QStyleOptionViewItem,
                    index: QModelIndex) -> bool:
        checkbox_data = index.data(Qt.CheckStateRole)
        flags = index.flags()
        if not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled) or checkbox_data is None:
            return False
        else:
            if event.type() == QEvent.MouseButtonRelease:
                mouseover_checkbox: bool = self.get_checkbox_rect(option).contains(event.pos())
                if not mouseover_checkbox:
                    return False
            elif event.type() == QEvent.KeyPress and event.key() != Qt.Key_Space:
                return False
            else:
                return False
            if checkbox_data == Qt.Checked:
                checkbox_toggled: int = Qt.Unchecked
            else:
                checkbox_toggled: int = Qt.Checked
            return model.setData(index, checkbox_toggled, Qt.CheckStateRole)

    def get_checkbox_rect(self, option: QStyleOptionViewItem) -> QRect:
        widget = option.widget
        if widget:
            style = widget.style()
        else:
            style = self.style()
        checkbox_size: QSize = style.subElementRect(QStyle.SE_CheckBoxIndicator, option, widget).size()
        return QStyle.alignedRect(option.direction, Qt.AlignCenter, checkbox_size, option.rect)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        try:
            self.initStyleOption(option, index)
            painter.save()

            flags: Qt.ItemFlags = index.model().flags(index)
            widget: Optional[QWidget] = option.widget
            checkbox_data = index.data(Qt.CheckStateRole)
            if widget:
                style = widget.style()
            else:
                style = self.style()

            if option.HasCheckIndicator and checkbox_data is not None:
                option_checkbox = option
                self.initStyleOption(option_checkbox, index)
                option_checkbox.state = option_checkbox.state & ~QStyle.State_HasFocus
                option_checkbox.features = option_checkbox.features & ~QStyleOptionViewItem.HasDisplay
                option_checkbox.features = option_checkbox.features & ~QStyleOptionViewItem.HasDecoration
                option_checkbox.features = option_checkbox.features & ~QStyleOptionViewItem.HasCheckIndicator
                style.drawControl(QStyle.CE_ItemViewItem, option_checkbox, painter, widget)

                # Then just draw the a checkbox centred in the cell
                option_checkbox.rect = self.get_checkbox_rect(option_checkbox)
                if option_checkbox.checkState == Qt.Checked:
                    state_flag = QStyle.State_On
                else:
                    state_flag = QStyle.State_Off

                option_checkbox.state = option_checkbox.state | state_flag
                style.drawPrimitive(QStyle.PE_IndicatorViewItemCheck, option_checkbox, painter, widget)

            else:
                QStyledItemDelegate.paint(self, painter, option, index)
        
            painter.restore()

        except Exception as e:
            print(repr(e))

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

        # setup a easy interface to metawear UI
        self.metawear_ui = self.app.measurements["MetaWear Sensors Control"]
        self.mobile_ui = self.app.measurements["Mobile Control"]

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

        # create a table to display task structure
        # Sample data
        # Step Number, Step Description, Step Duration [sec], Limb Connected to Mobile, Background Music
        # read the data from a yaml configuration file
        # Load the YAML configuration file
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        # Extract the step structure data from the configuration
        self.step_structure_data = [
            [
                task['step_number'],
                task['step_description'],
                task['step_duration_sec'],
                task['limb_connected_to_mobile'],
                task['background_music']
            ]
            for task in config['tasks']
        ]
        '''
        step_structure_data = [
            [1, "Fixation", 2, "None", False],
            [2, "Base Line", 150, "None", True],
            [3, "Connect", 180, "Left Hand", False],
            [4, "Disconnect",200, "None", False],
            [5, "Reconnect", 220, "Right Leg", False]   
        ]
        '''

        # Create the model
        # Create TableView and Model
        self.task_table = QTableView()
        self.task_table_model = QStandardItemModel(4, 5)  # 5 rows, 3 columns
        self.task_table_model.setHorizontalHeaderLabels(["Step Number", "Step Description","Step Duration [sec]", "Limb Connected to Mobile", "Background Music"])
        
        # add sample data
        for row in range(len(self.step_structure_data)):
            for col in range(len(self.step_structure_data[row])):
                if isinstance(self.step_structure_data[row][col], bool):
                    item = QStandardItem()
                    item.setCheckable(True)
                    item.setCheckState(Qt.Checked if self.step_structure_data[row][col] else Qt.Unchecked)
                    # set check box alignment to center, it is not text alignment
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item = QStandardItem(str(self.step_structure_data[row][col]))
                item.setTextAlignment(Qt.AlignCenter)
                self.task_table_model.setItem(row, col, item)

        self.task_table.setModel(self.task_table_model)

        self.task_table.setItemDelegateForColumn(1, ComboBoxDelegate(["Fixation", "Base Line", "Connect", "Disconnect", "Reconnect"], self))
        self.task_table.setItemDelegateForColumn(3, ComboBoxDelegate(["Left Hand", "Right Hand", "Left Leg", "Right Leg", "None"], self))
        self.task_table.setItemDelegateForColumn(4, CheckBoxDelegate(Qt.AlignCenter))

        def adjust_table_size(table_view, model):
            table_view.resizeColumnsToContents()
            table_view.resizeRowsToContents()

            # Calculate the width and height required to show all rows and columns
            total_width = sum([table_view.columnWidth(c) for c in range(model.columnCount())])
            total_height = sum([table_view.rowHeight(r) for r in range(model.rowCount())])

            # Add header sizes
            total_width += table_view.verticalHeader().width()
            total_height += table_view.horizontalHeader().height()

            # Apply the calculated size
            table_view.setFixedSize(total_width, total_height)

        
        adjust_table_size(self.task_table, self.task_table_model)
        # Set the table view to stretch
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # remove the autonumbering of rows
        self.task_table.verticalHeader().setVisible(False)
     
     
        # Add the table to the existing layout of Task_structure_group
        task_structure_layout = self.ui.Task_structure_group.layout()
        if task_structure_layout is None:
            task_structure_layout = QVBoxLayout()
            self.ui.Task_structure_group.setLayout(task_structure_layout)
        task_structure_layout.addWidget(self.task_table)

        # set the width of the columns to fit the content of the headers
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # connect to data update signal
        self.ui.start_stimuli_pushButton.clicked.connect(self.start)
        self.ui.stop_stimuli_pushButton.clicked.connect(self.interrupt)
        self.task_table_model.itemChanged.connect(self.on_item_changed)
        self.update_task_ID()

    def on_item_changed(self, item):
        # Step Number, Step Description, Step Duration [sec], Limb Connected to Mobile, Background Music
        row = item.row()
        col = item.column()
        if col == 1:
            self.step_structure_data[row][col] = item.text()
        elif col == 3:
            self.step_structure_data[row][col] = item.text()
        elif col == 4:
            self.step_structure_data[row][col] = item.checkState() == Qt.Checked

        # udpate self.step_structure_data with the remaining array columns
        self.step_structure_data[row][0] = int(self.task_table_model.item(row, 0).text())
        self.step_structure_data[row][2] = int(self.task_table_model.item(row, 2).text())
        
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

    def step_timer(self):
        self.timer_expired = True
        

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
            self.current_step = 0
            self.previous_step = -1
            self.timer_expired = False

            # Will run forever until interrupt is called.
            # Start Streaming Sensor Data and initiate saving the data
            self.metawear_ui.start()
            while not self.interrupt_measurement_called:
                i %= len(self.buffer)
                
                # Set progress bar percentage complete
                self.settings['progress'] = i * 100./len(self.buffer)
                
                
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.buffer_h5[i] = self.buffer[i]
                    # flush H5
                    self.h5file.flush()
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                time.sleep(self.settings['sampling_period'])
                
                i += 1

                # start consuming the steps in self.step_structure_data
                # let self.current_step be the current step
                # first time entering a step
                if self.current_step != self.previous_step:
                    # get all the step data from self.step_structure_data
                    step_number = self.step_structure_data[self.current_step][0]
                    step_description = self.step_structure_data[self.current_step][1]
                    step_duration = self.step_structure_data[self.current_step][2]
                    limb_connected_to_mobile = self.step_structure_data[self.current_step][3]
                    background_music = self.step_structure_data[self.current_step][4]

                    # Initialize Hardware 
                    if step_description == "Fixation":

                        # disconnect all limbs from mobile
                        #self.mobile_ui.ui.Limb_connected_to_mobile_ComboBox = "None"
                        self.mobile_ui.ui.Limb_connected_to_mobile_ComboBox.setCurrentText("None")

                        # Send to mobile the start of fixation step
                        if hasattr(self.mobile_ui, 'socket'):
                            try:
                                self.mobile_ui.socket.send_multipart([b"fixation_movie", str(int(30)).encode('utf-8')])
                            except zmq.error.ZMQError as e:
                                pass

                        # Stop the audio server from playing the mobile music
                        message = f"{0},{0.1}" # sound speed , sound volume
                        if hasattr(self.mobile_ui, 'socket_sound'):
                            try:
                                self.mobile_ui.socket_sound.send_string(message)
                            except zmq.error.ZMQError as e:
                                pass

                        # Play the the relevant fixation sound
                        # Initialize pygame mixer
                        pygame.mixer.init()

                        # Load the WAV file
                        pygame.mixer.music.load('./media/Fixation_resized_standard.wav')

                        # Play the WAV file
                        pygame.mixer.music.play()
                        
                        # start a timer for the duration of the fixation step
                        self.scheduler = BackgroundScheduler()
                        self.scheduler.add_job(self.step_timer, 'interval', seconds=step_duration)
                        self.scheduler.start()
                    
                    else:
                        # disconnect all limbs from mobile
                        #self.mobile_ui.ui.Limb_connected_to_mobile_ComboBox = "None"
                        
                        self.mobile_ui.ui.Limb_connected_to_mobile_ComboBox.setCurrentText(limb_connected_to_mobile)

                        # Send to mobile the start of fixation step
                        if hasattr(self.mobile_ui, 'socket'):
                            try:
                                self.mobile_ui.socket.send_multipart([b"mobile_movie", str(int(0)).encode('utf-8')])
                            except zmq.error.ZMQError as e:
                                pass

                        # Stop the audio server from playing the mobile music
                        message = f"{1},{0.1}" # sound speed , sound volume
                        if hasattr(self.mobile_ui, 'socket_sound'):
                            try:
                                self.mobile_ui.socket_sound.send_string(message)
                            except zmq.error.ZMQError as e:
                                pass

                        # Play the the relevant fixation sound
                        # Initialize pygame mixer
                        if background_music:
                            pygame.mixer.init()
                            # Load the WAV file for the background music
                            pygame.mixer.music.load('./media/Fixation_resized_standard.wav')
                            # Play the WAV file
                            pygame.mixer.music.play()
                        
                        # start a timer for the duration of the fixation step
                        self.scheduler = BackgroundScheduler()
                        self.scheduler.add_job(self.step_timer, 'interval', seconds=step_duration)
                        self.scheduler.start()
                        
                    self.previous_step = self.current_step

                # if the timer expired, move to the next step
                if self.timer_expired:
                    self.scheduler.shutdown()
                    self.current_step += 1
                    self.timer_expired = False
                    if self.current_step >= len(self.step_structure_data):
                        self.interrupt_measurement_called = True
                        # this will break the run

                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    break

        finally:            

            print("Experiment is finished")
            print("stop streaming sensor data")
            self.metawear_ui.interrupt()
            print("show dark screen on mobile")
            self.mobile_ui.socket.send_multipart([b"dark", b"0"])

            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
