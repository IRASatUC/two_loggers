#! /usr/bin/env python
"""
Training two logger robots escaping a cell with Deep Q-network (DQN)
DQN is a model free, off policy, reinforcement learning algorithm (https://deepmind.com/research/dqn/)
Author: LinZHanK (linzhank@gmail.com)

Train new models example:
    python double_escape_dqn_train.py --num_episodes 20000 --num_steps 400 --normalize --update_step 10000 --time_bonus -0.0025 --wall_bonus -0.025 --door_bonus 0 --success_bonus 1
Continue training models example:
    python double_escape_dqn_train.py --source '2019-07-17-17-57' --num_episodes 100
"""
from __future__ import absolute_import, division, print_function

import sys
import os
import time
from datetime import datetime
import numpy as np
import tensorflow as tf
import rospy
import pickle

from envs.double_escape_task_env import DoubleEscapeEnv
from utils import data_utils, double_utils
from agents.dqn import DQNAgent

import pdb


if __name__ == "__main__":
    # create argument parser
    args = double_utils.get_args()
    # make an instance from env class
    env = DoubleEscapeEnv()
    obs, info = env.reset()
    # create training parameters
    if not args.source: # source is empty, create new params
        rospy.logerr("no source: {}".format(args.source))
        # pre-extracted params
        date_time = datetime.now().strftime("%Y-%m-%d-%H-%M")
        dim_state = len(double_utils.obs_to_state(env.observation, "all"))
        actions = np.array([np.array([1, -1]), np.array([1, 1])])
        state_0 = double_utils.obs_to_state(obs, "all")
        state_1 = double_utils.obs_to_state(obs, "all")
        # train parameters
        train_params = double_utils.create_train_params(complete_episodes=0, complete_steps=0, success_count=0, source=args.source, normalize=args.normalize, num_episodes=args.num_episodes, num_steps=args.num_steps, time_bonus=args.time_bonus, wall_bonus=args.wall_bonus, door_bonus=args.door_bonus, success_bonus=args.success_bonus)
        # agent parameters
        agent_params_0 = double_utils.create_agent_params(dim_state=dim_state, actions=actions, ep_returns=[], ep_losses=[], mean=state_0, std=np.zeros(dim_state)+1e-15, layer_sizes=args.layer_sizes, discount_rate=args.gamma, learning_rate=args.lr, batch_size=args.batch_size, memory_cap=args.mem_cap, update_step=args.update_step, decay_period=train_params['num_episodes']*4/5, init_eps=args.init_eps, final_eps=args.final_eps)
        agent_params_1 = agent_params_0
        # instantiate new agents
        agent_0 = DQNAgent(agent_params_0)
        model_path_0 = os.path.dirname(sys.path[0])+"/saved_models/double_escape/dqn/"+date_time+"/agent_0/model.h5"
        agent_1 = DQNAgent(agent_params_1)
        model_path_1 = os.path.dirname(sys.path[0])+"/saved_models/double_escape/dqn/"+date_time+"/agent_1/model.h5"
    else: # source is not empty, load params
        rospy.logerr("source is: {}".format(args.source))
        # instantiate loaded agents
        model_path_0 = os.path.dirname(sys.path[0])+"/saved_models/double_escape/dqn/"+args.source+"/agent_0/model.h5"
        model_path_1 = os.path.dirname(sys.path[0])+"/saved_models/double_escape/dqn/"+args.source+"/agent_1/model.h5"
        # load train parameters
        with open(os.path.dirname(os.path.dirname(model_path_0))+ "/train_parameters.pkl", 'rb') as f:
            train_params = pickle.load(f)
        # load agents parameters
        with open(os.path.dirname(model_path_0)+'/agent_parameters.pkl', 'rb') as f:
            agent_params_0 = pickle.load(f) # load agent_0 model
        with open(os.path.dirname(model_path_1)+'/agent_parameters.pkl', 'rb') as f:
            agent_params_1 = pickle.load(f) # load agent_0 model
        # load dqn models & memory buffers
        agent_0 = DQNAgent(agent_params_0)
        agent_0.load_model(model_path_0)
        agent_1 = DQNAgent(agent_params_1)
        agent_1.load_model(model_path_1)
        # init robots from loaded pose buffer
        state_0 = double_utils.obs_to_state(obs, "all")
        state_1 = double_utils.obs_to_state(obs, "all")
        env.success_count = train_params['success_count']

    # learning
    start_time = time.time()
    mean_0 = agent_params_0['mean']
    std_0 = agent_params_0['std']
    mean_1 = agent_params_1['mean']
    std_1 = agent_params_1['std']
    ep = 0
    while ep <= train_params['num_episodes']:
        # check simulation crash
        if sum(np.isnan(state_0)) >= 1 or sum(np.isnan(state_1)) >= 1:
            rospy.logfatal("Simulation Crashed")
            train_params['complete_episodes'] = ep
            break # terminate main loop if simulation crashed
        if info["status"][0] == "blew" or info["status"][1] == "blew":
            rospy.logerr("Model blew up, skip this episode")
            obs, info = env.reset()
            state_0 = double_utils.obs_to_state(obs, "all")
            state_1 = double_utils.obs_to_state(obs, "all")
            continue
        epsilon_0 = agent_0.linearly_decaying_epsilon(episode=ep)
        epsilon_1 = agent_1.linearly_decaying_epsilon(episode=ep)
        rospy.logdebug("epsilon_0: {}, epsilon_1: {}".format(epsilon_0, epsilon_1))
        rospy.logdebug("epsilon_0: {}, epsilon_1: {}".format(epsilon_0, epsilon_1))
        done, ep_rewards, loss_vals_0, loss_vals_1 = False, [], [], []
        for st in range(train_params["num_steps"]):
            # check simulation crash
            if sum(np.isnan(state_0)) >= 1 or sum(np.isnan(state_1)) >= 1:
                logging.critical("Simulation Crashed")
                break # tbreakout loop if gazebo crashed
            # normalize states
            if train_params['normalize']:
                norm_state_0 = data_utils.normalize(state_0, mean_0, std_0)
                norm_state_1 = data_utils.normalize(state_1, mean_1, std_1)
                rospy.logdebug("\nagent_0 states normalize: {}\nagent_1 states normalize: {}".format(norm_state_0, norm_state_1))
            else:
                norm_state_0 = state_0
                norm_state_1 = state_1
            action_index_0 = agent_0.epsilon_greedy(norm_state_0)
            action_0 = agent_0.actions[action_index_0]
            action_index_1 = agent_1.epsilon_greedy(norm_state_1)
            action_1 = agent_1.actions[action_index_1]
            obs, rew, done, info = env.step(action_0, action_1)
            next_state_0 = double_utils.obs_to_state(obs, "all")
            next_state_1 = double_utils.obs_to_state(obs, "all")
            # compute incremental mean and std
            inc_mean_0 = data_utils.increment_mean(mean_0, next_state_0, (ep+1)*(st+1)+1)
            inc_std_0 = data_utils.increment_std(std_0, mean_0, inc_mean_0, next_state_0, (ep+1)*(st+1)+1)
            inc_mean_1 = data_utils.increment_mean(mean_1, next_state_1, (ep+1)*(st+1)+1)
            inc_std_1 = data_utils.increment_std(std_1, mean_1, inc_mean_1, next_state_1, (ep+1)*(st+1)+1)
            # update mean and std
            mean_0, std_0, mean_1, std_1 = inc_mean_0, inc_std_0, inc_mean_1, inc_std_1
            agent_params_0['mean'] = mean_0
            agent_params_0['std'] = std_0
            agent_params_0['mean'] = mean_1
            agent_params_1['std'] = std_1
            # normalize next states
            if train_params['normalize']:
                norm_next_state_0 = data_utils.normalize(next_state_0, mean_0, std_0)
                norm_next_state_1 = data_utils.normalize(next_state_1, mean_1, std_1)
                rospy.logdebug("\nagent_0 next states normalized: {}\nagent_1 next states normalized: {}".format(norm_next_state_0, norm_next_state_1))
            else:
                norm_next_state_0 = next_state_0
                norm_next_state_1 = next_state_1
            # adjust reward based on bonus options
            rew, done = double_utils.adjust_reward(train_params, env)
            ep_rewards.append(rew)
            train_params['success_count'] = env.success_count
            train_params['complete_steps'] += 1
            # store transitions
            if not info["status"][0] == "blew" or info["status"][1] == "blew":
                agent_0.replay_memory.store((norm_state_0, action_index_0, rew, done, norm_next_state_0))
                agent_1.replay_memory.store((norm_state_1, action_index_1, rew, done, norm_next_state_1))
                rospy.logwarn("transition saved to memory")
            else:
                rospy.logerr("model blew up, transition not saved")
            # log step
            rospy.loginfo(
                "Episode: {}, Step: {}, Complete episodes: {}, Complete steps: {}, epsilon_0: {}, epsilon_0: {} \nstate_0: {}, state_1: {}, \naction_0: {}, action_1: {}, \nnext_state_0: {}, next_state_1: {} \nreward/episodic_return: {}/{}, \nstatus: {}, \nnumber of success: {}".format(
                    ep+1,
                    st+1,
                    train_params['complete_episodes'],
                    train_params['complete_steps'],
                    agent_0.epsilon,
                    agent_1.epsilon,
                    state_0,
                    state_1,
                    action_0,
                    action_1,
                    next_state_0,
                    next_state_1,
                    rew,
                    sum(ep_rewards),
                    info["status"],
                    env.success_count
                )
            )
            # train one epoch
            agent_0.train()
            loss_vals_0.append(agent_0.loss_value)
            agent_1.train()
            loss_vals_1.append(agent_1.loss_value)
            state_0 = next_state_0
            state_1 = next_state_1
            # update q-statble net
            if not train_params['complete_steps'] % agent_params_0['update_step']:
                agent_0.qnet_stable.set_weights(agent_0.qnet_active.get_weights())
                rospy.logerr("agent_0 Q-net weights updated!")
            if not train_params['complete_steps'] %  agent_params_1['update_step']:
                agent_1.qnet_stable.set_weights(agent_1.qnet_active.get_weights())
                rospy.logerr("agent_1 Q-net weights updated!")
            if done:
                rospy.logerr("Current episode done!")
                break
        agent_params_0['ep_returns'].append(sum(ep_rewards))
        agent_params_1['ep_returns'].append(sum(ep_rewards))
        agent_params_0['ep_losses'].append(sum(loss_vals_0)/len(loss_vals_0))
        agent_params_1['ep_losses'].append(sum(loss_vals_1)/len(loss_vals_1))
        agent_0.save_model(model_path_0)
        agent_1.save_model(model_path_1)
        train_params['complete_episodes'] += 1
        ep += 1
        # reset env
        obs, _ = env.reset()
        state_0 = double_utils.obs_to_state(obs, "all")
        state_1 = double_utils.obs_to_state(obs, "all")

    # time training
    end_time = time.time()
    train_dur = end_time - start_time
    env.reset()

    # save replay buffer memories
    agent_0.save_memory(model_path_0)
    agent_1.save_memory(model_path_1)
    # save agent parameters
    data_utils.save_pkl(content=agent_params_0, fdir=os.path.dirname(model_path_0), fname="agent_parameters.pkl")
    data_utils.save_pkl(content=agent_params_1, fdir=os.path.dirname(model_path_1), fname="agent_parameters.pkl")
    # create train info
    train_info = train_params
    train_info["train_dur"] = train_dur
    train_info['success_count'] = env.success_count
    train_info["agent0_learning_rate"] = agent_params_0["learning_rate"]
    train_info["agent0_state_dimension"] = agent_params_0["dim_state"]
    train_info["agent0_action_options"] = agent_params_0["actions"]
    train_info["agent0_layer_sizes"] = agent_params_0["layer_sizes"]
    train_info["agent1_learning_rate"] = agent_params_1["learning_rate"]
    train_info["agent1_state_dimension"] = agent_params_1["dim_state"]
    train_info["agent1_action_options"] = agent_params_1["actions"]
    train_info["agent1_layer_sizes"] = agent_params_1["layer_sizes"]
    # save train info
    data_utils.save_csv(content=train_info, fdir=os.path.dirname(os.path.dirname(model_path_0)), fname="train_information.csv")
    data_utils.save_pkl(content=train_params, fdir=os.path.dirname(os.path.dirname(model_path_0)), fname="train_parameters.pkl")
    # save results
    np.save(os.path.join(os.path.dirname(model_path_0), 'ep_returns.npy'), agent_params_0['ep_returns'])
    np.save(os.path.join(os.path.dirname(model_path_1), 'ep_returns.npy'), agent_params_1['ep_returns'])
    np.save(os.path.join(os.path.dirname(model_path_0), 'ep_losses.npy'), agent_params_0['ep_losses'])
    np.save(os.path.join(os.path.dirname(model_path_1), 'ep_losses.npy'), agent_params_1['ep_losses'])

    # plot episodic returns
    data_utils.plot_returns(returns=agent_params_0['ep_returns'], mode=0, save_flag=True, fdir=os.path.dirname(os.path.dirname(model_path_0)))
    # plot accumulated returns
    data_utils.plot_returns(returns=agent_params_0['ep_returns'], mode=1, save_flag=True, fdir=os.path.dirname(os.path.dirname(model_path_0)))
    # plot averaged return
    data_utils.plot_returns(returns=agent_params_0['ep_returns'], mode=2, save_flag=True,
    fdir=os.path.dirname(os.path.dirname(model_path_0)))
