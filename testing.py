from keysight_dsox3034t import KeysightDSOX3034T
from configobj import ConfigObj

import matplotlib
matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
plt.ion()


config = ConfigObj('config.ini')['KeysightDSOX3034T']
scope = KeysightDSOX3034T(config)
scope.configure()


for i in range(2):
	xax, yax = scope.read_data()


scope.close()


'''
for i in range(scope.segment_count):
    plt.plot(xax, yax[i], lw=0.1, label=f"{i}")
plt.legend()   
plt.show()
#print(metadata)

'''
