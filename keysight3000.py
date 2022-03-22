####################################               
# Author: Christian Dorfer
# Email: dorfer@aps.ee.ethz.ch                                
####################################

import pyvisa as visa
from time import sleep, time
from configobj import ConfigObj
import numpy as np


class Keysight:
    """ Readout class for the Keysight DSOX3034T Oscilloscope.
        The maximum storage is 2.5M points in WORD data format.
        If segment_count = 1000, each wf is 2500 pts long.
   
    """

    def __init__(self, conf):
        self.conf = conf
        rm = visa.ResourceManager('@py')
        self._inst = rm.open_resource(self.conf['address'], timeout=self.conf.as_int('timeout_ms'))
        self.write("*rst")
        sleep(2)
        print("Connected to: ", self.query("*idn?").rstrip())

        self.segment_count = self.conf.as_int('segment_count')


    def write(self, command):
        self._inst.write(command)
        err = self.get_full_error_queue()
        if err:
            print(f"Errors while writing {command} to instrument")
            for e in err:
                print(e)


    def query(self, command):
        try:
            return self._inst.query(command).strip()
        except visa.Error as err:
            msg = f"query '{command}'"
            print(f"\n\nVisaError: {err}\n  When trying {msg}  (full traceback below).")
            print(f"  Have you checked that the timeout (currently "
                  f"{self.timeout:,d} ms) is sufficently long?")
            try:
                self.get_full_error_queue(verbose=True)
                print("")
            except Exception as excep:
                print("Could not retrieve errors from the oscilloscope:")
                print(excep)
                print("")
            raise
        

    def get_full_error_queue(self, verbose=False):
        """All the latest errors from the oscilloscope, upto 30 errors
        (and store to the attribute ``errors``)"""
        errors = []
        for i in range(30):
            err = self._inst.query(":SYSTem:ERRor?").strip()
            if err[:2] == "+0":  # No error
                # Stop querying
                break
            else:
                # Store the error
                errors.append(err)
        if verbose:
            if not errors:
                print("Error queue empty")
            else:
                print("Latest errors from the oscilloscope (FIFO queue, upto 30 errors)")
                for i, err in enumerate(errors):
                    print(f"{i:>2}: {err}")
        return errors


    def close(self):
        self._inst.close()


    def read_premable(self):
        pre = self.query("WAVeform:PREamble?").split(',')
        formatting = {'+0':'BYTE', '+1':'WORD', '+4':'ASCII'}
        format_descriptor = {'+0':'b', '+1':'h', '+4':'standard'}
        acq_type = {'+0':'NORMAL', '+2':'AVERAGE', '+3':'HRESOLUTION'}
        res = {}
        res['format'] = formatting[pre[0]]
        res['format_descriptor'] = format_descriptor[pre[0]]
        res['type'] = acq_type[pre[1]]
        res['npoints'] = int(pre[2]) #in each segment
        res['x_increment'] = float(pre[4]) #time difference between data points on x-axis
        res['x_origin'] = float(pre[5]) #first data point in memory
        res['x_reference'] = float(pre[6]) #first data point associated with x-origin
        res['y_increment'] = float(pre[7])
        res['y_origin'] = float(pre[8])
        res['y_reference'] = float(pre[9])
        res['x_axis'] = ((np.linspace(0, res['npoints']-1, res['npoints'])-res['x_reference'])*res['y_increment'])+res['x_origin']

        return res
        

    def configure(self):

        #set up trigger (trigger on rising edge signal (threshold: 2V) on channel 2 with an amplitude)
        self.write("channel3:display ON")
        self.write("trigger:edge:source channel3")
        self.write(f"channel3:offset {self.conf['ch3_offset']}")
        self.write(f"trigger:mode {self.conf['ch3_trigger_mode']}")
        self.write(f"trigger:edge:slope {self.conf['ch3_trigger_slope']}")
        self.write(f"channel3:coupling {self.conf['ch3_coupling']}")
        self.write(f"trigger:edge:level {self.conf['ch3_trigger_level']}")
        self.write("trigger:sweep normal")

        #set up data taking channel 1
        self.write("waveform:source channel1")
        self.write(f"channel1:coupling {self.conf['ch1_coupling']}")
        self.write(f"channel1:impedance {self.conf['ch1_impedance']}")
        self.write(f"channel1:scale {self.conf['ch1_scale']}")
        
        self.write(f"timebase:scale {self.conf['tax_scale']}")

        self.write("waveform:points max")
        self.write("waveform:format word")
        self.write("waveform:points:mode raw")
        #self.write('waveform:points MAX')

        #self.write('acquire:digitizer 1')
        self.write("acquire:type normal")
        self.write(f"acquire:srate:analog {self.conf['sampling_rate']}")
        #sleep(1)

        self.write("acquire:mode segmented") #rtime
        self.write(f"acquire:segmented:count {self.segment_count}")
        self.write("waveform:segmented:all on") #return all segments at once


  

    def read_data(self, channel=1):
        print('Acquiring Triggers..', flush=True)
        seg_count = int(self.query("waveform:SEGMented:COUNt?"))
        while seg_count != self.segment_count:
            sleep(0.2)
            seg_count = int(self.query("waveform:SEGMented:COUNt?"))          


        t0 = time()
        res = self.read_premable()
        print(f"Collected {self.segment_count} waveforms. Transfer to PC..", flush=True)

        try:
            raw = self._inst.query_binary_values(":WAVeform:DATA?", datatype=res['format_descriptor'], container=np.array)
        except visa.Error as err:
            print(f"\n\nVisaError: {err}\n  When trying to obtain the waveform (full traceback below).")
            pass
        
        t1 = time()

        y_axis = (raw - res['y_reference'])*res['y_increment'] + res['y_origin']
        y_axis = np.split(y_axis, self.segment_count)

        print(f"Transferred  {self.segment_count} waveforms in {t1-t0:.2f} seconds.")

        self.write("run")
        return res['x_axis'], y_axis




if __name__ == '__main__':
    config = ConfigObj('config.ini')['ScopeConfig']
    scope = Keysight(config)
    scope.configure()
    
    xax, yax = scope.read_data()
    
    print('len xax: ', len(xax))
    print('nr of wfs: ',len(yax))

    for i in range(scope.segment_count):
        plt.plot(xax, yax[i], lw=0.1, label=f"{i}")
    plt.legend()   
    plt.show()
    #print(metadata)
    scope.close()