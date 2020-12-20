import numpy as np
import matplotlib.pyplot as plt
from time import sleep

plt.axis([-1.1, 1.1, -1.1, 1.1])
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')
ax.spines['right'].set_color('none')
ax.add_artist(plt.Circle((0, 0), 1, color='b', fill=False))
ax.set_aspect("equal")


while(True):
    y = np.random.rand(3, 2)
    points = plt.scatter(y[:, 0], y[:, 1], color="r")
    plt.pause(0.05)
    sleep(0.1)
    points.remove()

plt.show()