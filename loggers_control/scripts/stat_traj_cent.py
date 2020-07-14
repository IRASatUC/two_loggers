import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.patches as mpatches
import tensorflow as tf

# Physical Params
M_LOGGER = 3.6
R_LOGGER = 0.25
M_ROD = 0.04
R_ROD = 0.02
L_ROD = 2
J_LOGGER = 1./2*M_LOGGER*R_LOGGER**2
J_ROD = 1/12*M_ROD*(3*R_ROD**2+L_ROD**2)
# load trajectory
traj_path = os.path.join(sys.path[0], 'saved_trajectories', 'cent_8', 'traj.npy')
traj = np.load(traj_path)
traj_diff = traj[1:] - traj[:-1]
dist = 0
ke = 0
# travel distance
for td in traj_diff:
    dist += np.linalg.norm(td[:2]) + np.linalg.norm(td[-6:-4])
# kinetic energy
for t in traj:
    ke += .5*M_LOGGER*np.linalg.norm(t[2:4])**2 \
        + .5*M_LOGGER*np.linalg.norm(t[-4:-2])**2 \
        + .5*M_ROD*np.linalg.norm(t[8:10])**2 \
        + .5*J_LOGGER*t[5]**2 \
        + .5*J_LOGGER*t[-1]**2 \
        + .5*J_ROD*t[11]**2
# canceled acc
acc_cancel = np.zeros(traj_diff.shape[0])
for i in range(traj_diff.shape[0]):
    a0_vec = traj_diff[i,2:4]
    a1_vec = traj_diff[i,-4:-2]
    rod_vec = traj[i+1,-6:-4] - traj[i+1,0:2]
    proj_a0 = np.dot(a0_vec, rod_vec)/np.linalg.norm(rod_vec)
    proj_a1 = np.dot(a1_vec, rod_vec)/np.linalg.norm(rod_vec)
    unit_proj_a0 = proj_a0/np.linalg.norm(proj_a0)
    unit_proj_a1 = proj_a1/np.linalg.norm(proj_a1)
    angle = np.arccos(np.dot(unit_proj_a0, unit_proj_a1))
    print("angle: {}".format(angle))
    if np.isclose(angle, np.pi):
        acc_cancel[i] = np.min([np.linalg.norm(proj_a0), np.linalg.norm(proj_a1)])
mean_acc_cancel = np.mean(acc_cancel)
# elapsed time
time = len(traj_diff)

# save stats
with open(os.path.join(os.path.dirname(traj_path), 'travel_distance.txt'), 'w') as f:
    f.write("{}".format(dist))
with open(os.path.join(os.path.dirname(traj_path), 'kinetic_energy.txt'), 'w') as f:
    f.write("{}".format(ke))
with open(os.path.join(os.path.dirname(traj_path), 'canceled_acc.txt'), 'w') as f:
    f.write("{}".format(mean_acc_cancel))
with open(os.path.join(os.path.dirname(traj_path), 'time_elapsed.txt'), 'w') as f:
    f.write("{}".format(time))

