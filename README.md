
Version 1.0.1

1. cleanly exiting the application by terminating the mobile subprocess if the exist. thereby allowing for a clean rerun of the application

version 1.0.2

1. fixed saved file name bug

version 1.0.3
1. added two new models for controling the mobile speed and music
    1a. according to this paper: https://doi.org/10.1016/j.dcn.2020.100760 from Zaadnoordijk et al. mobile starts to move after c
        crossing a specific threshold and then stops after a specific amount of time. it can be retriggered after a specific dead time
    1b. my simple physical model. in which I add to the speed of the mobile according to the acceleration plus there is 
        a stable friction force which always move to reduce the speed.
    1c. There is a specific launcher now for the shiba and hebrew setups (different metawear sensors) termed: shiba.bat and hebrew.bat

2. changed to mobile music in baseline step which starts after a specific amount of time that is settable in the config.yaml file

version 1.0.4
1. added the feature of loading video files from the media folder. these video files can be used instead of live camera feed
2. the video restarts from the beginning after a step is over


To install run:
install 
1. miniconda 64 bit 
2. visual code
3. github desktop
4. git for windows
5. ffmpeg

 clone this repository
 https://github.com/liorse/Lital_IMU_Tobii_Pro_Integration


The following conda command takes a while (more than 5 minutes)
conda env create --file environment.yml

conda activate lital
open anaconda prompt
go to the project folder


python Agency_Sensor_MAIN.py
