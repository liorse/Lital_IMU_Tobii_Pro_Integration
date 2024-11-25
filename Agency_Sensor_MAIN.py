import pythoncom
pythoncom.CoInitialize()

from ScopeFoundry import BaseMicroscopeApp
from HW_MetaMotionRL import MetaMotionRLHW
from UI_MetaMotionRL import MetaWearUI
from UI_Experiment_controller import ExperimentControllerUI

class AgencySensor(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'Agency Sensor'
    
    # You must define a setup function that adds all the 
    # capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        self.add_hardware(MetaMotionRLHW(self, name='LeftHandMeta', MAC="C2:26:C4:65:45:54"))
        self.add_hardware(MetaMotionRLHW(self, name='RightHandMeta', MAC="F3:F1:E2:D3:6E:A7"))
        self.add_hardware(MetaMotionRLHW(self, name='LeftLegMeta', MAC="E1:39:04:67:C2:9B"))
        self.add_hardware(MetaMotionRLHW(self, name='RightLegMeta', MAC="C7:B2:76:3D:6B:1D"))
        
        #Add measurement components
        print("Create Measurement objects")
        self.add_measurement(MetaWearUI(self))
        self.add_measurement(ExperimentControllerUI(self))
        
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys
    # set the logger to info level in FanceyMicroscopeApp
    
    app = AgencySensor(sys.argv)
    sys.exit(app.exec_())