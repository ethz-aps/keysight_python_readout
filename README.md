# keysight_python_readout
Configuration and readout of our Keysight DSOX3034T.

In our experiment the oscilloscope is triggered via a TTL signal on CH3. With every trigger a trace from CH1 is stored in the internal buffer which has a depth of 2.5M points (segmented capture). Once the buffer is full (e.g. 1000 traces, each 2500 points) all 2.5M points are read in one go over USB. During the ~17 second long readout of the 2.5M points the oscilloscope is stopped and does not acquire data.

There are certainly ways to speed things up a few percent but the main time killer is the max. USB transfer rate reached.

