#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
| Created on Wed Feb 13 15:37:43 2019
| @author: Semeon Risom
| @email: semeon.risom@gmail.com.
| Sample code to run SR Research Eyelink eyetracking system. Code is optimized for the Eyelink 1000 Plus (5.0),
| but should be compatiable with earlier systems.
"""

#----debug
from pdb import set_trace as breakpoint
from IPython.display import display

#----main
import time
import os
import re
import platform
import pandas as pd
from pathlib import Path

#psychopy
from psychopy import visual, core, event
from psychopy.constants import (NOT_STARTED, STARTED, FINISHED)
#----bridging
import pylink
from calibration import calibration
#---------------------------------------------start
class eyetracking():
    """
    Module allowing communcation to the SR Research Eyelink eyetracking system. Code is optimized for the 
    Eyelink 1000 Plus (5.0), but should be compatiable with earlier systems.
    
    Notes
    -----
    According to [Pylink.chm](\_static\pdf\Pylink.chm), the sequence of operations for implementing a trial is:
        1) Perform a DRIFT CORRECTION, which also serves as the pre-trial fixation target.
        2) Start recording, allowing 100 milliseconds of data to accumulate before the trial display starts.
        3) Draw the subject display, recording the time that the display appeared by placing a message in the EDF file.
        4) Loop until one of these events occurs RECORDING halts, due to the tracker ABORT menu or an error, the maximum 
        trial duration expires 'ESCAPE' is pressed, the program is interrupted, or abutton on the EyeLink button box is pressed.
        5) Add special code to handle gaze-contingent display updates.
        6) Blank the display, stop recording after an additional 100 milliseconds of data has been collected.
        7) Report the trial result, and return an appropriate error code.
    """
    def __init__(self, window, timer, isPsychopy=True, libraries=False, subject=None):
        """
        Initialize eyetracker.

        Parameters
        ----------
        window : :obj:`psychopy.visual.window.Window`
            PsychoPy window instance.
        timer : :obj:`psychopy.clock.CountdownTimer`
            Psychopy timer instance.
        isPsychopy : :obj:`bool`
            Is Psychopy being used.
        libraries : :obj:`bool`
            Should the code check if required libraries are available.
        subject : :obj:`int`
            Subject number.

        Examples
        --------
        >>> eytracking = mdl.eyetracking(libraries=False, window=window, subject=subject)  
        """

        #----screen size
        if isPsychopy:
            self.w = int(window.size[0])
            self.h = int(window.size[1])
        else:
            if platform.system() == "Windows":
                from win32api import GetSystemMetrics
                self.w = int(GetSystemMetrics(0))
                self.h = int(GetSystemMetrics(1))
            elif platform.system() == 'Darwin':
                from AppKit import NSScreen
                self.w = int(NSScreen.mainScreen().frame().size.width)
                self.h = int(NSScreen.mainScreen().frame().size.height)
        
        #----parameters
        # instants
        self.window = window
        # flags
        self.isStarted = False
        self.isCalibration = False
        self.isRecording = False
        self.isDriftCorrection = False
        self.isFinished = False
        # counters
        self.drift_count = 0
        # metadata
        self.trial = ''
        self.block = ''
        # pupil
        self.eye_used = None
        self.left_eye = 0
        self.right_eye = 1
        # status
        self.status = {}
        
        #----timing
        self.routineTimer = timer
        
        #----drift correction
        #clock
        self.drift_message_clock = core.Clock()
        self.drift_clock = core.Clock()
        #screen
        text = '\n'.join([
            "On the next screen a fixation dot will appear.",
            "Please look at the fixation dot until it disappears.",
            "\nPress any key to continue."
        ])
        self.drift_text = visual.TextStim(win=window, name='drift_message', font='Helvetica',
        text=text, height=0.1, wrapWidth=1.5, ori=0, pos=(0, 0), alignVert='center', color='black', 
        colorSpace='rgb', opacity=1, languageStyle='LTR', depth=0.0)
        
        # check if subject number has been entered
        if subject == None:
            self.console(
                c='red', msg='Subject number not entered. Please enter the subject number.'
            )
        else:
            self.subject = subject
    
        # generate file path
        self.path = "%s/data/edf/" % (os.getcwd())
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
        #----check if required libraries are available
        if libraries == True:
            self.libraries()

        #----edf filename
        self.subject = os.path.splitext(str(subject))[0]
        # check if integer
        if re.match(r'\w+$', self.subject):
            pass
        else:
            self.window.close()
            raise AssertionError('Name must only include A-Z, 0-9, or _')
        # check length
        if len(self.subject) <= 8:
            pass
        else:
            self.window.close()
            raise AssertionError('Name must be <= 8 characters.')
        # store name
        self.fname = str(self.subject) + '.edf'

    def libraries(self):
        """Check if required libraries to run eyelink and Psychopy are available."""

        self.console(msg="eyetracking.libraries()")
        # check libraries for missing
        from distutils.version import StrictVersion
        import importlib
        import pkg_resources
        import pip

        # list of possibly missing packages to install
        required = ['psychopy', 'importlib', 'glfw']

        # for geting os variables
        if platform.system() == "Windows":
            required.append('win32api')
        elif platform.system() == 'Darwin':
            required.append('pyobjc')

        # try installing and/or importing packages
        try:
            # if pip >= 10.01
            pip_ = pkg_resources.get_distribution("pip").version
            if StrictVersion(pip_) > StrictVersion('10.0.0'):
                from pip._internal import main as _main
                # for required packages check if package exists on device
                for package in required:
                    # if missing, install
                    if importlib.util.find_spec(package) is None:
                        _main(['install', package])

            # else pip < 10.01
            else:
                # for required packages check if package exists on device
                for package in required:
                    # if missing
                    if importlib.util.find_spec(package) is None:
                        pip.main(['install', package])
        except Exception as e:
            return e
            
    def console(self, c='green', msg=''):
        """
        Allows printing color coded messages to console/terminal/cmd. This may be useful for debugging issues.

        Parameters
        ----------
        color : :obj:`str`
            Color to use (black, red, green, orange, purple, blue, grey).
        msg : :obj:`str`
            Message to be color printed.
        
        Examples
        --------
        >>> eyetracking.console(c="green", msg="eyetracking.calibration() started")
        """

        color = dict(
            black='\33[40m',
            red='\33[41m',
            green='\33[42m',
            orange='\33[43m',
            purple='\33[45m',
            blue='\33[46m',
            grey='\33[47m',
            ENDC='\033[0m')

        return print(color[c] + msg + color['ENDC'])

    def connect(self, calibration_type=13, automatic_calibration_pacing=1000, saccade_velocity_threshold=35,
                saccade_acceleration_threshold=9500, sound=True, select_parser_configuration=0,
                recording_parse_type="GAZE", enable_search_limits=True, ip='100.1.1.1'):
        """
        Connect to Eyelink.

        Parameters
        ----------
        ip : :obj:`string`
            Host PC ip address.
        calibration_type : :obj:`int`
            Calibration type. Default is 13-point. [see Eyelink 1000 Plus User Manual, 3.7 Calibration]
        automatic_calibration_pacing : :obj:`int`
            Select the delay in milliseconds, between successive calibration or validation targets 
            if automatic target detection is activeSet automatic calibration pacing. [see pylink.chm]
        saccade_velocity_threshold : :obj:`int`
            Sets velocity threshold of saccade detector: usually 30 for cognitive research, 22 for 
            pursuit and neurological work. Default is 35. Note: EyeLink II and EyeLink 1000,
            select select_parser_configuration should be used instead. [see EyeLink Programmer’s Guide, 
            Section 25.9: Parser Configuration; Eyelink 1000 Plus User Manual, Section 4.3.5 
            Saccadic Thresholds]
        saccade_acceleration_threshold : :obj:`int`
            Sets acceleration threshold of saccade detector: usually 9500 for cognitive research, 5000 
            for pursuit and neurological work. Default is 9500. Note: For EyeLink II and EyeLink 1000,
            select select_parser_configuration should be used instead. [see EyeLink Programmer’s Guide,
            Section 25.9: Parser Configuration; Eyelink 1000 Plus User Manual, Section 4.3.5 
            Saccadic Thresholds]
        select_parser_configuration : :obj:`int`
            Selects the preset standard parser setup (0) or more sensitive (1). These are equivalent
            to the cognitive and psychophysical configurations. Default is 0. [see EyeLink Programmer’s 
            Guide, Section 25.9: Parser Configuration]
        sound : :obj:`bool`
            Should sound be used for calibration/validation/drift correction.
        recording_parse_type : :obj:`str`
            Sets how velocity information for saccade detection is to be computed.
            Enter either 'GAZE' or 'HREF'. Default is 'GAZE'. [see Eyelink 1000 Plus User Manual, 
            Section 4.4: File Data Types]
        enable_search_limits : :obj:`bool`
            Enables tracking of pupil to global search limits. Default is True. [see Eyelink 1000 Plus 
            User Manual, Section 4.4: File Data Types]
        
        Returns
        ----------
        param : :class:`pandas.DataFrame`
            Returns dataframe of parameters for subject.
        
        Examples
        --------
        >>> param = eyetracking.connect(calibration_type=13)
        """
        #----initiate connection with eyetracker
        self.ip = ip
        try:
            self.tracker = pylink.EyeLink(self.ip)
            self.connected = True
            self.console(c='blue', msg="Eyelink Connected")
        except RuntimeError:
            self.tracker = pylink.EyeLink(None)
            self.connected = False
            self.console(c='red', msg="Eyelink RuntimeError")
            
        #----tracker metadata
        # get eyelink version
        self.tracker_version = self.tracker.getTrackerVersion()

        # get host tracking software version
        self.host_version = 0
        if self.tracker_version == 3:
            tvstr = self.tracker.getTrackerVersionString()
            vindex = tvstr.find("EYELINK CL")
            self.host_version = int(
                float(tvstr[(vindex + len("EYELINK CL")):].strip()))

        #----preset
        self.select_parser_configuration = select_parser_configuration
        self.saccade_acceleration_threshold = saccade_acceleration_threshold
        self.saccade_velocity_threshold = saccade_velocity_threshold
        self.recording_parse_type = recording_parse_type
        self.enable_search_limits = "YES" if enable_search_limits else "NO"
        # calibration
        self.calibration_type = calibration_type  # []-point calibration
        self.automatic_calibration_pacing = automatic_calibration_pacing
        # specify the EVENT and SAMPLE data that are stored in EDF or retrievable from the Link
        # [see Section 4.6 Data Files of the  EyeLink 1000 Plus user manual]
        self.fef = "LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT"
        self.lef = "LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT"
        if self.host_version >= 4:
            self.fsd = "LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET,INPUT"
            self.lsd = "LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,HTARGET,INPUT"
        else:
            self.fsd = "LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS"
            self.lsd = "LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS"

        #---store param for export
        self.param = dict(
            tracker_version=self.tracker_version, 
            host_version=self.host_version,
            select_parser_configuration=self.select_parser_configuration,
            saccade_acceleration_threshold=self.saccade_acceleration_threshold,
            saccade_velocity_threshold=self.saccade_velocity_threshold,
            recording_parse_type=self.recording_parse_type,
            enable_search_limits=self.enable_search_limits,
            automatic_calibration_pacing=self.automatic_calibration_pacing,
            file_event_filter=self.fef,
            file_sample_data=self.fsd,
            link_event_filter=self.lef,
            link_sample_data=self.lsd,
            calibration_type=self.calibration_type
        )

        #----open edf
        self.tracker.openDataFile(self.fname)
        pylink.flushGetkeyQueue()

        #----send settings to eyelink
        # place EyeLink tracker in offline (idle) mode before changing settings
        self.tracker.setOfflineMode()
        # Set the tracker to parse events using either GAZE or HREF
        # note: [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
        self.tracker.sendCommand("recording_parse_type = %s" %
                                 (self.recording_parse_type))
        # inform the tracker the resolution of the subject display
        # note: [see Eyelink Installation Guide, Section 8.4: Customizing Your PHYSICAL.INI Settings]
        self.tracker.sendCommand(
            "screen_pixel_coords = 0 0 %d %d" % (self.w - 1, self.h - 1))
        # save display resolution in EDF data file for Data Viewer integration purposes
        # note: [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
        self.tracker.sendMessage(
            "DISPLAY_COORDS = 0 0 %d %d" % (self.w - 1, self.h - 1))
        # set calibration type
        self.tracker.sendCommand("calibration_type = HV%d" %
                                 (self.calibration_type))
        # set automatic calibraiton pacing interval
        self.tracker.sendCommand("automatic_calibration_pacing = %d" % (
            self.automatic_calibration_pacing))

        # if using tracker version 2 or greater
        if self.tracker_version >= 2:
            self.tracker.sendCommand("select_parser_configuration %d" % (
                self.select_parser_configuration))
            # turn of scene link
            if self.tracker_version == 2:
                self.tracker.sendCommand("scene_camera_gazemap = NO")
        else:
            self.tracker.sendCommand("saccade_velocity_threshold = %s" % (
                self.saccade_velocity_threshold))
            self.tracker.sendCommand("saccade_acceleration_threshold = %s" % (
                self.saccade_acceleration_threshold))

        # if using tracker version 3 or above
        if self.tracker_version >= 3:
            self.tracker.sendCommand(
                "enable_search_limits=%s" % (self.enable_search_limits))
            self.tracker.sendCommand("track_search_limits=YES")
            self.tracker.sendCommand("autothreshold_click=YES")
            self.tracker.sendCommand("autothreshold_repeat=YES")
            self.tracker.sendCommand("enable_camera_position_detect=YES")

        # set content of edf file
        # edf filters #event types
        self.tracker.sendCommand('file_event_filter = %s' % (self.fef))
        self.tracker.sendCommand('file_sample_data = %s' % (self.fsd))
        self.tracker.sendCommand('link_event_filter = %s' % (self.lef))
        self.tracker.sendCommand('link_sample_data = %s' % (self.lsd))

        # program button '5' for drift correction
        self.tracker.sendCommand("button_function 5 'accept_target_fixation'")

        # select sound for calibration and drift correct
        # "" = sound, "off" = no sound
        pylink.setCalibrationSounds("", "", "")
        pylink.setDriftCorrectSounds("", "", "")
        
        # export param to txt file
        param = pd.DataFrame(list(self.param.items()),columns=['category', 'value'])
        param.to_csv(path_or_buf=self.path + str(self.subject) + ".txt", index=True, index_label='index')

        #if ipython
        display(param)
        
        return param

    def set_eye_used(self, eye):
        """
        Set dominant eye. This step is required for recieving gaze coordinates from Eyelink->Psychopy.

        Parameters
        ----------
        eye : :obj:`str`
            Dominant eye (left, right). This will be used for outputting Eyelink gaze samples.
        
        Examples
        --------
        >>> dominant_eye = 'left'
        >>> eye_used = eyetracking.set_eye_used(eye=dominant_eye)
        """
        self.console(msg="eyetracking.set_eye_used()")
        eye_entered = str(eye)
        if eye_entered in ('Left', 'LEFT', 'left', 'l', 'L'):
            self.console(c="blue", msg="eye_entered = %s('left')" %(eye_entered))
            self.eye_used = self.left_eye
        else:
            self.console(c="blue", msg="eye_entered = %s('right')" %(eye_entered))
            self.eye_used = self.right_eye

        return self.eye_used

    def calibration(self):
        """
        Start calibration procedure.
        
        Returns
        -------
        isCalibration : :obj:`bool`
            Message indicating status of calibration.
        
        Examples
        --------
        >>> eyetracking.calibration()
        """
        self.console(msg="eyetracking.calibration()")
        
        #----if connected to eyetracker
        if self.connected:
            # put the tracker in offline mode before we change its configurations
            self.tracker.setOfflineMode()
            # Generate custom calibration stimuli
            self.genv = calibration(w=self.w, h=self.h, tracker=self.tracker, window=self.window)
            # execute custom calibration display
            pylink.openGraphicsEx(self.genv)
            # calibrate
            self.tracker.doTrackerSetup(self.w, self.h)
            #flip screen after finishing
            self.window.flip()
            
        #----finished
        self.isCalibration = True
        self.console(c="blue", msg="eyetracking.calibration() finished")

        return self.isCalibration
    
    def _drift_message(self):
        #----prepare to start Routine 'drift_message'
        endExpNow = False  # flag for 'escape' or other condition => quit the exp
        t = 0
        self.drift_message_clock.reset()  # clock
        frameN = -1
        continueRoutine = True
        # update component parameters for each repeat
        drift_response = event.BuilderKeyResponse()
        # keep track of which components have finished
        drift_message_components = [drift_response, self.drift_text]
        for thisComponent in drift_message_components:
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        
        # -------Start Routine "drift_message"-------
        while continueRoutine:
            # get current time
            t = self.drift_message_clock.getTime()
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *drift_response* updates
            if t >= 0.0 and drift_response.status == NOT_STARTED:
                # keep track of start time/frame for later
                drift_response.tStart = t
                drift_response.frameNStart = frameN  # exact frame index
                drift_response.status = STARTED
                # keyboard checking is just starting
                event.clearEvents(eventType='keyboard')
            if drift_response.status == STARTED:
                theseKeys = event.getKeys()
                
                # check for quit:
                if "escape" in theseKeys:
                    endExpNow = True
                if len(theseKeys) > 0:  # at least one key was pressed
                    # a response ends the routine
                    continueRoutine = False
            
            # *drift_text* updates
            if t >= 0.0 and self.drift_text.status == NOT_STARTED:
                # keep track of start time/frame for later
                self.drift_text.tStart = t
                self.drift_text.frameNStart = frameN  # exact frame index
                self.drift_text.setAutoDraw(True)
            
            # check for quit (typically the Esc key)
            if endExpNow or event.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in drift_message_components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                self.window.flip()
        
        # -------Ending Routine "drift_message"-------
        for thisComponent in drift_message_components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
                
        # the Routine "drift_message" was not non-slip safe, so reset the non-slip timer
        self.routineTimer.reset()
        
    def drift_correction(self, source='manual'):
        """
        Starts drift correction. This can be done at any point after calibration, including before 
        and after eyetracking.start_recording has already been initiated.
        
        Parameters
        ----------
        source : :obj:`str`
            Origin of call, either `manual` (default) or from gaze contigent event (`gc`).
        
        Returns
        -------
        isDriftCorrection : :obj:`bool`
            Message indicating status of drift correction.
        
        Notes
        -----
        Running drift_correction will end any start_recording event to function properly. Once drift
        correction has occured, it is safe to run start_recording.
        
        Examples
        --------
        >>> eyetracking.drift_correction()
        """
        self.console(msg="eyetracking.drift_correction()")
        
        #----present drift correction message (only if manually accessing)
        if source=='manual':
            self._drift_message()
            self.window.clearBuffer()
            self.window.flip()
        
        #check if recording
        if self.isRecording:
            # end of trial message
            self.tracker.sendMessage('drift correction')

            # end realtime mode
            pylink.endRealTimeMode()
            pylink.msecDelay(100)

            # send trial-level variables
            #if running from self.gc
            if source=='gc':
                self.send_variable(variables=dict(trial=self.trial, block=self.block, issues='gc window failed'))

            # specify end of trial
            self.tracker.sendMessage("TRIAL_RESULT 1")

            # stop recording eye data
            self.tracker.stopRecording()
        
        # flag isRecording
        self.isRecording = False
        
        # initiate drift correction, flag isDriftCorrection
        self.isDriftCorrection = True
        try:
           self.tracker.doDriftCorrect(int(self.w/2), int(self.h/2), 1, 1)
        except:
           self.tracker.doTrackerSetup()
        

        #----finished
        self.console(c="blue", msg="eyetracking.drift_correction() finished")
        
        return self.isDriftCorrection
    
    def start_recording(self, trial, block):
        """
        Starts recording of Eyelink.

        Parameters
        ----------
        trial : :obj:`str`
            Trial Number.
        block : :obj:`str`
            Block Number.
        
        Returns
        -------
        isRecording : :obj:`bool`
            Message indicating status of Eyelink recording.

        Notes
        -----
        tracker.beginRealTimeMode():
            To ensure that no data is missed before the important part of the trial starts. The EyeLink 
            tracker requires 10 to 30 milliseconds after the recording command to begin writing data. 
            This extra data also allows the detection of blinks or saccades just before the trial start, 
            allowing bad trials to be discarded in saccadic RT analysis. A "SYNCTIME" message later 
            in the trial marks the actual zero-time in the trial's data record for analysis.
            [see pylink.chm]
        TrialID:
            The "TRIALID" message is sent to the EDF file next. This message must be placed 
            in the EDF file before the drift correction and before recording begins, and is critical 
            for data analysis. The viewer will not parse any messages, events, or samples that exist
            in the data file prior to this message. The command identifier can be changed in the data
            loading preference settings.
            [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]
        SYNCTIME:
            Marks the zero-time in a trial. A number may follow, which is interpreted as the delay of 
            the message from the actual stimulus onset. It is suggested that recording start 100 
            milliseconds before the display is drawn or unblanked at zero-time, so that no data at the 
            trial start is lost.
            [see pylink.chm]

        Examples
        --------
        >>> eyetracking.start_recording(trial=1, block=1)
        """
        self.console(msg="eyetracking.start_recording()")
        
        # indicates start of trial
        self.tracker.sendMessage('TRIALID %s' % (str(trial)))
    
        # Message to post to Eyelink display Monitor
        self.tracker.sendCommand("record_status_message 'Trial %s Block %s'" % (str(trial), str(block)))

        # start recording, parameters specify whether events and samples are
        # stored in file, and available over the link
        self.tracker.startRecording(1, 1, 1, 1)

        # buffer to prevent loss of data
        pylink.beginRealTimeMode(100)

        # indicates zero-time of trial
        self.tracker.sendMessage('SYNCTIME')
        self.tracker.sendMessage('start recording')
            
        # flag isDriftCorrection, isRecording, trial, block
        self.isDriftCorrection = False
        self.isRecording = True
        self.trial = trial
        self.block = block

        return self.isRecording
    
    def gc(self, bound, t_min, t_max=None):
        """
        Creates gaze contigent event. This function needs to be run while recording.
        
        Parameters
        ----------
        bound : :obj:`dict` [:obj:`str`, :obj:`int`]:
            Dictionary of the bounding box for each region of interest. Keys are each side of the 
            bounding box and values are their corresponding coordinates in pixels.
        t_min : :obj:`int`
            Mininum duration (msec) in which gaze contigent capture is collecting data before allowing
            the task to continue.
        t_max : :obj:`int` or :obj:`None`
            Maxinum duration (msec) before task is forced to go into drift correction. 

        Examples
        --------
        >>> # Collect samples within the center of the screen, for 2000 msec, 
        >>> # with a max limit of 10000 msec.
        >>> region = dict(left=860, top=440, right=1060, bottom=640)
        >>> eyetracking.gc(bound=bound, t_min=2000, t_max=10000)
        """
        
        #if eyetracker is recording
        if self.isRecording:
            # draw box
            self.tracker.sendCommand('draw_box %d %d %d %d 6'%\
                                     (bound['left'],bound['top'],bound['right'],bound['bottom']))
            
            #get start time
            start_time = time.clock()
            #get current time
            current_time = time.clock()
            
            #----check gc window
            while True:
                #get gaze sample
                gxy, ps, s = self.sample(self.eye_used)
                
                #is gaze with gaze contigent window for t_min time
                if ((bound['left'] < gxy[0] < bound['right']) and (bound['top'] < gxy[1] < bound['bottom'])):
                    # has mininum time for gc window occured
                    duration = (time.clock() - current_time) * 1000
                    if duration > t_min:
                        self.console(c='blue', msg="eyetracking.gc() success in %d"%((time.clock() - start_time) * 1000))
                        self.send_message(msg='gc window success')
                        break
                else:
                    print('out of window')
                    #reset current time
                    current_time = time.clock()
                
                # if reached maxinum time
                if t_max is not None:
                    # has maxinum time for gc window occured
                    duration = (time.clock() - start_time) * 1000
                    if duration > t_max:
                        self.console(c='blue', msg="eyetracking.gc() failed, drift correction started")
                        self.send_message(msg='gc window failed')
                        self.drift_correction()
                        break
        else:
            self.console(c='red', msg="eyetracker not recording")
                     
    def sample(self, eye_used):
        """
        Collects new gaze coordinates from Eyelink.

        Parameters
        ----------
        eye_used : :obj:`str`
            Checks if eye used is available.
        
        Returns
        -------
        gxy : :class:`tuple`
            Gaze coordiantes.
        ps : :obj:`tuple`
            Pupil size (area).
        s : :class:`EyeLink.getNewestSample`
            Eyelink newest sample.

        Examples
        --------
        >>> eyetracking.sample(eye_used=eye_used)
        """
        # check for new sample update
        s = self.tracker.getNewestSample()
        if(s != None):
            # gaze coordinates, pupil area
            if eye_used == self.right_eye:
                gxy = s.getRightEye().getGaze()
                ps = s.getRightEye().getPupilSize()
            else:
                gxy = s.getLeftEye().getGaze()
                ps = s.getLeftEye().getPupilSize()
            return gxy, ps, s

    def send_message(self, msg):
        """
        Send message to Eyelink. This allows post-hoc processing of event markers (i.e. "stimulus onset").

        Parameters
        ----------
        msg : :obj:`str`
            Message to be recieved by eyelink.

        Examples
        --------
        >>> eyetracking.console(c="blue", msg="eyetracking.calibration() started")
        """
        self.tracker.sendMessage(msg)

    def send_variable(self, variables):
        """
        send trial variable to eyelink at the end of trial.

        Parameters
        ----------
        variable : :obj:`dict` or `None`
            Trial-related variables to be read by eyelink.          
        """
        if variables is not None:
            for key, value in variables.items():
                msg = "!V TRIAL_VAR %s %s" % (key, value)
                self.tracker.sendMessage(msg)
                pylink.msecDelay(1)
            # finished
            self.console(msg="variables sent")
        else:
            self.console(c="red", msg="no variables entered")

    def stop_recording(self, trial=None, block=None, variables=None):
        """
        Stops recording of Eyelink. Also allows transmission of trial-level variables to Eyelink.

        Parameters
        ----------
        trial : :obj:`int`
            Trial Number.
        block : :obj:`int`
            Block Number.
        variables : :obj:`dict` or `None`
            Dict of variables to send to eyelink (variable name, value).
        
        Returns
        -------
        isRecording : :obj:`bool`
            Message indicating status of Eyelink recording.

        Notes
        -----
        pylink.pumpDelay():
            Does a unblocked delay using currentTime(). This is the preferred delay function 
            when accurate timing is not needed.
            [see pylink.chm]
        pylink.msecDelay():
            During calls to pylink.msecDelay(), Windows is not able to handle messages. One result of 
            this is that windows may not appear. This is the preferred delay function when accurate 
            timing is needed.
            [see pylink.chm]
        tracker.endRealTimeMode():
            Returns the application to a priority slightly above normal, to end realtime mode. This 
            function should execute rapidly, but there is the possibility that Windows will allow other 
            tasks to run after this call, causing delays of 1-20 milliseconds. This function is equivalent 
            to the C API void end_realtime_mode(void).
            [see pylink.chm]
        TRIAL_VAR: 
            Lets users specify a trial variable and value for the given trial. One
            message should be sent for each trial condition variable and its corresponding value. If
            this command is used there is no need to use TRIAL_VAR_LABELS. The default command identifier 
            can be changed in the data loading preference settings. Please note that the eye tracker 
            can handle about 20 messages every 10 milliseconds. So be careful not to send too many 
            messages too quickly if you have many trial condition messages to send. Add one millisecond 
            delay between message lines if this is the case.
            [see pylink.chm]
        TRIAL_RESULT: 
            Defines the end of a trial. The viewer will not parse any messages, events, or samples that 
            exist in the data file after this message. The command identifier can be changed in the 
            data loading preference settings.
            [see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration]

        Examples
        --------
        >>> variables = dict(stimulus='face.png', event='stimulus')
        >>> eyetracking.stop_recording(trial=trial, block=block, variables=variables)
        """
        self.console(msg="eyetracking.stop_recording()")
        
        # end of trial message
        self.tracker.sendMessage('end recording')

        # end realtime mode
        pylink.endRealTimeMode()
        pylink.msecDelay(100)

        # send trial-level variables
        variables['trial'] = trial
        variables['block'] = block
        variables['issues'] = 'none'
        self.send_variable(variables=variables)

        # specify end of trial
        self.tracker.sendMessage("TRIAL_RESULT 1")

        # stop recording eye data
        self.tracker.stopRecording()

        # flag isRecording
        self.isRecording = False

        return self.isRecording

    def finish_recording(self, path=None):
        """
        Ending Eyelink recording.

        Parameters
        ----------
        path : :obj:`str` or :obj:`None`
            Path to save data. If None, path will be default from PsychoPy task.
        
        Returns
        -------
        isFinished : :obj:`bool`
            Message indicating status of Eyelink recording.

        Notes
        -----
        pylink.pumpDelay():
            Does a unblocked delay using currentTime(). This is the preferred delay function 
            when accurate timing is not needed.
            [see pylink.chm]
        pylink.msecDelay():
            During calls to pylink.msecDelay(), Windows is not able to handle messages. One result of 
            this is that windows may not appear. This is the preferred delay function when accurate 
            timing is needed.
            [see pylink.chm]
        tracker.setOfflineMode():
            Places EyeLink tracker in offline (idle) mode. Wait till the tracker has finished the 
            mode transition.
            [see pylink.chm]
        tracker.endRealTimeMode():
            Returns the application to a priority slightly above normal, to end realtime mode. This 
            function should execute rapidly, but there is the possibility that Windows will allow other 
            tasks to run after this call, causing delays of 1-20 milliseconds. This function is 
            equivalent to the C API void end_realtime_mode(void).
            [see pylink.chm]
        tracker.receiveDataFile():
            This receives a data file from the EyeLink tracker PC. Source filename and destination 
            filename should be given.
            [see pylink.chm]

        Examples
        --------
        >>> #end recording session
        >>> eyetracking.finish_recording()
        """
        self.console(msg="eyetracking.finish_recording()")
        
        #clear host display
        self.tracker.sendCommand('clear_screen 0') 
        
        # double check realtime mode has ended
        pylink.endRealTimeMode()
        pylink.pumpDelay(500)

        # rlaces eyeLink tracker in offline (idle) mode
        self.tracker.setOfflineMode()

        # allow buffer to prepare data for closing
        pylink.msecDelay(500)

        # closes any currently opened EDF file on the EyeLink tracker computer's hard disk
        self.tracker.closeDataFile()

        # This receives a data file from the eyelink tracking computer
        #if no path entered, use psychopy destination
        if path is None:
            destination = self.path + self.fname
        else:
            destination = path
        self.tracker.receiveDataFile(self.fname, destination)
        self.console(c="blue", msg="File saved at: %s"%(Path(destination)))

        # sends a disconnect message to the EyeLink tracker
        self.tracker.close()

        # flag isFinished
        self.isFinished = True

        #---finish
        return self.isFinished