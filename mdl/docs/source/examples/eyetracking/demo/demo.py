#%% [markdown]
#  <title>Example setup for Eyelink 1000 Plus, using PsychoPy 3.0.</title>
#  <h5>Example setup for Eyelink 1000 Plus, using PsychoPy 3.0.</h5>
# %% [markdown]
# <a>Created on Wed Feb 13 15:37:43 2019</a><br>
# <a>@author: Semeon Risom</a><br>
# <a>@email: semeon.risom@gmail.com</a><br>
# <a>Sample code to run SR Research Eyelink eyetracking system. Code is optimized for the Eyelink 1000</a><br>
# <a>Plus (5.0), but should be compatiable with earlier systems.</a><br>
# %% [markdown]
# <ul class="list-container">
#     <li>
#         <div class="title">The sequence of operations for implementing the trial is:</div>
#         <ol class="list">
#             <li>[Import the mdl package](:ref:`demo.ipynb#A-Sub-Section`).</li>
#             <li>[Initialize the `mdl.eyetracking()` package](demo.html#import).</li>
#             <li>[Connect to the Eyelink Host](demo#import).</li>
#             <li>[Set the dominamt eye](demo#import).</li>
#             <li>[Start calibration](demo#import).</li>
#             <li>[Start recording](demo#import).</li>
#             <li>[Stop recording](demo.ipynb#import).</li>
#             <li>[Finish recording](example.ipynb#import).</li>
#         </ol>
#     </li>
#     <li>
#         <div class="title">Optional commands include:</div>
#         <ol>
#             <li>Drift correction.</li>
#             <li>Initiate gaze contigent event.</li>
#             <li>Collect real-time gaze coordinates from Eyelink.</li>
#             <li>Send messages to Eyelink.</li>
#         </ol>
#     </li>
# </ul>
# %% [markdown]
# <h5>Import packages.</h5><br>
# %%
import os, sys, time
sys.path.append(os.path.abspath(os.getcwd() + '../../../../../../..'))
from psychopy import visual, core
import mdl
# %% [markdown]
# <h5>Task parameters, either directly from PsychoPy or created manually.</h5><br>
# %%
expInfo = {u'condition': u'even', u'participant': u'001', u'dominant eye': u'left', u'corrective': u'False'}
subject = expInfo['participant']
dominant_eye = expInfo['dominant eye']
# `psychopy.core.Clock.CountdownTimer` instance
routineTimer = core.CountdownTimer()
# `psychopy.visual.window.Window` instance
window = visual.Window(size=[1920, 1080], fullscr=False, allowGUI=True, units='pix', winType='pyglet', color=[110,110,110], colorSpace='rgb255')
window.flip()
# %% [markdown]
# <h5>Initialize the mdl.eyetracking() package.</h5><br>
# Note: Before initializing, make sure code is placed after PsychoPy window instance has been created in the experiment file. 
# This window will be used in the calibration function.
# %%
# Initialize mdl.eyetracking()
eyetracking = mdl.eyetracking.run(window=window, libraries=True, subject=subject, timer=routineTimer, demo=True)
# %% [markdown]
# <h5>Connect to the Eyelink Host.</h5><br>
# This controls the parameters to be used when running the eyetracker.
# %%
param = eyetracking.connect(calibration_type=13)
# %% [markdown]
# <h5>Set the dominamt eye.</h5><br>
# This step is required for recieving gaze coordinates from Eyelink->PsychoPy.
# %%
eye_used = eyetracking.set_eye_used(eye=dominant_eye)
# %% [markdown]
# <h5>Start calibration.</h5><br>
# %%
# start calibration
calibration = eyetracking.calibration()
# %%
# Enter the key "o" on the calibration instance. This will begin the task. 
# The Calibration, Validation, 'task-start' events are controlled by the keyboard.
# Calibration ("c"), Validation ("v"), task-start ("o") respectively.
# %% [markdown]
# <h5>(Optional) Print message to console/terminal.</h5><br>
# Allows printing color coded messages to console/terminal/cmd. This may be useful for debugging issues.
# %%
eyetracking.console(c="blue", msg="eyetracking.calibration() started")
# %% [markdown]
# <h5>(Optional) Drift correction.</h5><br>
# This can be done at any point after calibration, including before and after 
# [eyetracking.start_recording()](eyetracking.rst#mdl.eyetracking.eyetracking.start_recording) has started.
# %%
drift = eyetracking.drift_correction()
# %% [markdown]
# <h5>Start recording.</h5><br>
# Note: This should be run at the start of the trial. Also, there is an intentional delay of 150 msec to 
# allow the Eyelink to buffer gaze samples that will show up in your data.
# %%
# Create stimulus (demonstration purposes only).
filename = "8380.bmp"
path = os.getcwd() + "/stimuli/" + filename
size = (1024, 768) #image size
pos = (window.size[0]/2, window.size[1]/2) #positioning image at center of screen
stimulus = visual.ImageStim(win=window, name="stimulus", units='pix', image=path, pos=(0,0), size=size,
                            flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-1.0)
stimulus.setAutoDraw(True)
window.flip()
window.flip()
# %%
# start recording
eyetracking.start_recording(trial=1, block=1)
# %% [markdown]
# <h5>(Optional) Initiate gaze contigent event.</h5><br>
# This is used for realtime data collection from Eyelink->PsychoPy.
# %%
# In the example, a participant is qto look at the bounding cross for a duration
# of 2000 msec before continuing the task. If this doesn't happen and a maxinum maxinum duration of 
# 10000 msec has occured first drift correction will start.
bound = dict(left=448, top=156, right=1472, bottom=924)
eyetracking.gc(bound=bound, t_min=5000, t_max=20000)
# %% [markdown]
# <h5>(Optional) Collect real-time gaze coordinates from Eyelink.</h5><br>
# Note: Samples need to be collected at an interval of 1000/(sampling rate) msec to prevent oversampling.
# %%
gxy, ps, sample = eyetracking.sample() # get gaze coordinates, pupil size, and sample
# %% [markdown]
# <h5>(Optional) Example use of `eyetracking.sample()`.</h5><br>
# Note: Samples need to be collected at an interval of 1000/(sampling rate) msec to prevent oversampling.
# %%
# In our example, the sampling rate of our device (Eyelink 1000 Plus) is 500Hz.
s1 = 0 # set current time to 0
lgxy = [] # create list of gaze coordinates (demonstration purposes only)
s0 = time.clock() # initial timestamp
# repeat
while True:
    # if difference between starting and current time is greater than > 2.01 msec, collect new sample
    diff = (s1 - s0)
    if diff >= .00201:
        gxy, ps, sample = eyetracking.sample() # get gaze coordinates, pupil size, and sample
        lgxy.append(gxy) # store in list (not required; demonstration purposes only)
        s0 = time.clock() # update starting time
    #else set current time
    else: 
        s1 = time.clock()

    #break `while` statement if list of gaze coordiantes >= 20 (not required; demonstration purposes only)
    if len(lgxy) >= 200: break
# %% [markdown]
# <h5>(Optional) Send messages to Eyelink.</h5><br>
# This allows post-hoc processing of event markers (i.e. "stimulus onset").
# %%
# Sending message "stimulus onset".
eyetracking.send_message(msg="stimulus onset")
# %% [markdown]
# <h5>Stop recording.</h5><br>
# Also (optional) provides trial-level variables to Eyelink.
# Note: Variables sent are optional. If they being included, they must be in `python dict` format.
# %%
# Prepare variables to be sent to Eyelink
variables = dict(stimulus=filename, trial_type='encoding', race="black")
# Stop recording
eyetracking.stop_recording(trial=1, block=1, variables=variables)
# %% [markdown]
# <h5>Finish recording.</h5><br>
# %%
eyetracking.finish_recording()
# %% [markdown]
# <h5>Close PsychoPy.</h5><br>
# %%
 window.close()