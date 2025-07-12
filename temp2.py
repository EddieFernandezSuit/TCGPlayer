import rebound
sim = rebound.Simulation()
sim.add(m=1)
sim.add(m=0.1, e=0.041, a=0.4, inc=0.2, f=0.43, Omega=0.82, omega=2.98)
sim.add(m=1e-3, e=0.24, a=1.0, pomega=2.14)
sim.add(m=1e-3, e=0.24, a=1.5, omega=1.14, l=2.1)
sim.add(a=-2.7, e=1.4, f=-1.5,omega=-0.7) # hyperbolic orbit