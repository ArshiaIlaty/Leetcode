import ipyvolume
import numpy as np
from collections import Mapping

#x, y, z, u, v, w = np.random.random((6, 1000))*2-1
#ipv.quickquiver(x, y, z, u, v, w, size=5)

x, y, z = np.random.random((3, 10000)) 
ipyvolume.quickscatter(x, y, z, size=1, marker="sphere")