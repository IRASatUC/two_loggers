"""
Evaluation of learned model for double_escape_task
Author: LinZHanK (linzhank@gmail.com)
"""
from __future__ import absolute_import, division, print_function

import sys
import os
import pickle
from datetime import datetime
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Dense
import rospy

from envs.double_escape_task_env import DoubleEscapeEnv
from utils import data_utils, double_utils
from utils.data_utils import bcolors
from agents.dqn import DQNAgent

if __name__ == "__main__":
    # instantiate env
    env = DoubleEscapeEnv()
    env.reset()
    # load agent models
    model_dir = os.path.dirname(sys.path[0])+"/saved_models/double_escape/dqn/2019-12-31-17-43/"
    with open(os.path.join(model_dir,"agent_0/agent_parameters.pkl"), "rb") as f:
        agent_params_0 = pickle.load(f)
    with open(os.path.join(model_dir,"agent_1/agent_parameters.pkl"), "rb") as f:
        agent_params_1 = pickle.load(f)
    # # load train parameters
    # with open(model_dir+"/train_parameters.pkl", 'rb') as f:
    #     train_params = pickle.load(f)
    # instantiate agents
    agent_0 = DQNAgent(agent_params_0)
    agent_0.load_model(os.path.join(model_dir, "agent_0"))
    agent_1 = DQNAgent(agent_params_1)
    agent_1.load_model(os.path.join(model_dir, "agent_1"))

    # evaluation params
    num_episodes = 100
    num_steps = 160
    ep = 0
    eval_params = {'wall_bonus': False,'door_bonus':False,'time_bonus':False,'success_bonus':False,'num_steps':num_steps}
    # start evaluating
    while ep <= num_episodes:
        obs, info = env.reset()
        done = False
        if info["status"][0] == "blew" or info["status"][1] == "blew":
            rospy.logerr("Model blew up, skip this episode")
            obs, info = env.reset()
            continue
        state_0 = double_utils.obs_to_state(obs, "all")
        state_1 = double_utils.obs_to_state(obs, "all")
        for st in range(num_steps):
            action_index_0 = np.argmax(agent_0.qnet_active.predict(state_0.reshape(1,-1)))
            action_0 = agent_params_0["actions"][action_index_0]
            action_index_1 = np.argmax(agent_1.qnet_active.predict(state_1.reshape(1,-1)))
            action_1 = agent_params_1["actions"][action_index_1]
            obs, rew, done, info = env.step(action_0, action_1)
            rew, done = double_utils.adjust_reward(eval_params, env)

            next_state_0 = double_utils.obs_to_state(obs, "all")
            next_state_1 = double_utils.obs_to_state(obs, "all")
            state_0 = next_state_0
            state_1 = next_state_1
            # logging
            print(
                bcolors.OKGREEN,
                "Episode: {}, Step: {} \naction0: {}->{}, action0: {}->{}, agent_0 state: {}, agent_1 state: {}, reward: {}, status: {} \nsuccess_count: {}".format(
                    ep,
                    st,
                    action_index_0,
                    action_0,
                    action_index_1,
                    action_1,
                    next_state_0,
                    next_state_1,
                    rew,
                    info["status"],
                    env.success_count
                ),
                bcolors.ENDC
            )
            if done:
                ep += 1
                break

    print("Loggers succeeded escaping {} out of {}".format(env.success_count, num_episodes))
    env.reset()
