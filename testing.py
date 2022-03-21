from keysight3000 import Keysight
from configobj import ConfigObj

import matplotlib
matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
plt.ion()


config = ConfigObj('config.ini')['ScopeConfig']
scope = Keysight(config)
scope.configure()


for i in range(10):
	xax, yax = scope.read_data()


scope.close()


'''
for i in range(scope.segment_count):
    plt.plot(xax, yax[i], lw=0.1, label=f"{i}")
plt.legend()   
plt.show()
#print(metadata)

'''