import pythoncom
pythoncom.CoInitialize()
import yaml
import sys
from ScopeFoundry import BaseMicroscopeApp
from HW_MetaMotionRL import MetaMotionRLHW
from UI_MetaMotionRL import MetaWearUI
from UI_Mobile_Control import MobileControllerUI
from UI_Experiment_Control import ExperimentControllerUI

class AgencySensor(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'Agency Sensor'
    
    def __init__(self, argv, dark_mode=False):
        
        # Load MAC addresses from config.yaml file
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        if len(argv) > 1:
            if argv[1] == 'shiba':
                hardware_configs = {item['name']: item['MAC'] for item in config['hardware_shiba']}
            elif argv[1] == 'hebrew':
                hardware_configs = {item['name']: item['MAC'] for item in config['hardware_hebrew']}
            
        self.left_hand_mac = hardware_configs['LeftHandMeta']
        self.right_hand_mac = hardware_configs['RightHandMeta']
        self.left_leg_mac = hardware_configs['LeftLegMeta']
        self.right_leg_mac = hardware_configs['RightLegMeta']
        # run the BaseMicroscopeApp __init__ function
        BaseMicroscopeApp.__init__(self, argv, dark_mode=dark_mode)

    # You must define a setup function that adds all the 
    # capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        self.settings.New('Version', dtype=str, initial='1.0.4')

        # the version number to App name
        self.name = 'Agency Sensor v{}'.format(self.settings['Version'])
        
        #Add hardware components
        print("Adding Hardware Components")
        
        self.add_hardware(MetaMotionRLHW(self, name='LeftHandMeta', MAC=self.left_hand_mac))
        self.add_hardware(MetaMotionRLHW(self, name='RightHandMeta', MAC=self.right_hand_mac))
        self.add_hardware(MetaMotionRLHW(self, name='LeftLegMeta', MAC=self.left_leg_mac))
        self.add_hardware(MetaMotionRLHW(self, name='RightLegMeta', MAC=self.right_leg_mac))
        
        #Add measurement components
        print("Create Measurement objects")
        self.add_measurement(MetaWearUI(self))
        self.add_measurement(MobileControllerUI(self))
        self.add_measurement(ExperimentControllerUI(self))
        
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
  
    
    # set the logger to info level in FanceyMicroscopeApp
    
    app = AgencySensor(sys.argv, dark_mode=True)
    sys.exit(app.exec_())