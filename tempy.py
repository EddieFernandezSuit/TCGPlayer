import numpy as np

mu = 398600.4418  # km^3/s^2

def dydt(t, y):
    x, y_pos, vx, vy = y
    r = np.sqrt(x**2 + y_pos**2)
    ax = -mu * x / r**3
    ay = -mu * y_pos / r**3
    return np.array([vx, vy, ax, ay])

def rk4_step(f, t, y, h):
    k1 = f(t, y)
    k2 = f(t + 0.5*h, y + 0.5*h*k1)
    k3 = f(t + 0.5*h, y + 0.5*h*k2)
    k4 = f(t + h, y + h*k3)
    return y + (h/6)*(k1 + 2*k2 + 2*k3 + k4)


# Initial orbit parameters
r1 = 7000  # km (LEO)
r2 = 42164  # km (GEO)
a = 0.5 * (r1 + r2)
v1 = np.sqrt(mu / r1)
v_transfer = np.sqrt(mu * (2/r1 - 1/a))
delta_v1 = v_transfer - v1




# Initial state
y = np.array([r1, 0, 0, v1 + delta_v1])  # x, y, vx, vy

# Time settings
t = 0
h = 10  # time step in seconds
tf = np.pi * np.sqrt(a**3 / mu)  # half orbit period (time to apogee)

positions = [y[:2]]
times = [t]

while t < tf:
    y = rk4_step(dydt, t, y, h)
    t += h
    positions.append(y[:2])
    times.append(t)

import matplotlib.pyplot as plt

positions = np.array(positions)
plt.plot(positions[:,0], positions[:,1])
plt.scatter([0], [0], c='orange', label='Earth')
plt.axis('equal')
plt.xlabel("x (km)")
plt.ylabel("y (km)")
plt.title("Hohmann Transfer Orbit")
plt.legend()
plt.grid(True)
plt.show()
