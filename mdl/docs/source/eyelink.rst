.. _eyelink:

.. currentmodule:: mdl

How Eyelink works
-----------------

.. raw:: html

   <div class="col-md-12">

The EyeLink trackers use a velocity-based method for eye event parsing. Saccade onset is detected when the eye movement 
velocity or acceleration exceeds a pre-set threshold, whereas saccade offset is detected when the velocity and acceleration
fall below the thresholds. The end of a saccade is the start of a fixation and the start of a saccade is the end of a 
previous fixation. Since this velocity-based method detects the onset and offset of saccades, it is usually known as a 
"saccade-picker" (`Eyelink forum <https://www.sr-support.com/forum/eyelink/eyelink-usage/53415-official-documentation-of-how-eyelink-calculates-fixations-and-saccades>`_).

heuristic filtering algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The eye movement data recorded in the data file, by default, has been filtered with a heuristic algorithm (Stampe, 1993).
For more information on the heuristic filtering algorithm, see (`Stampe, 1993 <https://doi.org/10.3758/BF03204486>`_).::

    Stampe, D. (1993). Heuristic filtering and reliable calibration methods for video-based pupil-tracking
    systems. Behavior Research Methods, Instruments, & Computers, 25(2), 137–142. doi:10.3758/BF03204486

velocity and acceleration thresholds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the velocity and acceleration thresholds see the `EyeLink 1000 Plus User Manual <_static/pdf//Eyelink%201000%20Plus%20User%20Manual%201.0.12.pdf>`_.::

    EyeLink 1000 Plus User Manual (2013). EyeLink 1000 Plus. SR Research Ltd., Mississauga, Ontario, Canada.

.. raw:: html

   </div>
