#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  4 15:35:23 2018

@author: Ian

This creates a class for training session with the following methods:
    - start()
    - train_operator()
    - get_timestamp()
    - cal_performance()
    - save_session_results()
    - reset_episode_action_history()

"""

import numpy as np
import matplotlib.pyplot as plt
from env import env
from rl_brain import agent
import datetime
import os

class trainer():
    
    def __init__(self):
        
        # Session Properties
        self.episodes = []
        self.stock_type = ""
        self.logging = False
        self.env_debug = False
        self.rl_debug = False
        self.bike_station = None
        self.operator = None
        
        # Performance Metric
        self.success_ratio = 0
        self.rewards = []  # [[r from session 1], [r from session 2] ...]
        self.final_stocks = [] # [[stock from session 1], [stock from session 2] ...]
        self.episode_action_history = []
        self.session_action_history = []
        self.q_tables = []
        
    
    def start(self, episodes, stock_type, logging, env_debug, rl_debug):
        
        self.episodes = episodes
        self.stock_type = stock_type
        self.logging = logging
        self.env_debug = env_debug
        self.rl_debug = rl_debug
        
        for eps in self.episodes:
        
            # Initiate new evironment and RL agent
            self.bike_station = env(self.stock_type, debug = self.env_debug)
            self.operator = agent(epsilon = 0.9, lr = 0.01, gamma = 0.9, 
                                  current_stock = self.bike_station.current_stock(), 
                                  debug = self.rl_debug)
            
            # Train the RL agent and collect performance stats
            rewards, final_stocks = self.train_operator(eps, logging = self.logging)
            
            # Log the results from this training session
            self.rewards.append(rewards)
            self.final_stocks.append(final_stocks)
            self.q_tables.append(self.operator.get_q_table())
            self.session_action_history.append(self.episode_action_history)
            self.reset_episode_action_history()
            
            # Destroy the environment and agent objects
            self.bike_station = None
            self.operator = None
        
        if logging == True:
            
            self.save_session_results(self.get_timestamp(replace = True))
            
        return
    
    
    def train_operator(self, episodes, logging):
    
        '''
        This function trains an RL agent by interacting with the bike station 
        environment. It also tracks and reports performance stats.
        Input:
            - episodes: a int of episode to be trained in this session (e.g. 500)
        Output:
            - reward_list: a list of reward per episode in this sesison
            - final_stocks: a list of final stocks per episode in this session
        '''
        
        print("Start training the Agent ...")
        rewards = 0
        reward_list = []
        final_stocks = []
        
        for eps in range(episodes):
            
            self.bike_station.reset()
                
            while True:
                
                # Agent picks an action (number of bikes to move)
                # Agent sends the action to bike station environment
                # Agent gets feedback from the environment (e.g. reward of the action, new bike stock after the action, etc.)
                # Agent "learn" the feedback by updating its Q-Table (state, action, reward)
                # Repeat until end of day (23 hours)
                # Reset bike station environment to start a new day, repeat all
                
                action = self.operator.choose_action(self.bike_station.get_old_stock())
                current_hour, old_stock, new_stock, reward, done = self.bike_station.ping(action)
                self.operator.learn(old_stock, action, reward, new_stock)
                
                rewards += reward
                
                # Log hourly action history by each episode
                
                if done == True:
                    
                    print("Episode: {} | Final Stock: {} |Final Reward: {:.2f}".format(eps, 
                          old_stock, rewards))
                    
                    reward_list.append(rewards)
                    final_stocks.append(old_stock)
                    rewards = 0
                    
                    # Log session action history by episode
                    self.episode_action_history.append(self.operator.get_hourly_actions())
                    self.operator.reset_hourly_action()
                                    
                    break
                            
        return reward_list, final_stocks
    
    def get_timestamp(self, replace):
        
        if replace == True:
        
            return str(datetime.datetime.now()).replace(" ", "").replace(":", "").\
                        replace(".", "").replace("-", "")
        
        else:
            
            return str(datetime.datetime.now())
    
    
    def reset_episode_action_history(self):
        
        self.episode_action_history = []
        
    
    def cal_performance(self):
        
        successful_stocking = []
        
        print("===== Performance =====")
        
        for session in range(len(self.final_stocks)):
            
            num_overstock = np.count_nonzero(np.array(self.final_stocks[session]) > 50)
            num_understock = np.count_nonzero(np.array(self.final_stocks[session]) <= 50)
            ratio = num_understock*100 / (num_overstock + num_understock)
            
            print("Session {} | Overstock {} Times | Understock {} Times | {}% Successful".format(session, num_overstock, 
                  num_understock, ratio))
            
            successful_stocking.append(ratio)
        
        return successful_stocking
    
    
    def save_session_results(self, timestamp):
        
        '''
        This function logs the following: 
            - overall success ratio of each session
            - line chart of success ratio by session
            - line chart of reward history by session
            - Q Table of each session
            - Comparison Line Chart of First and Last Episode Hourly Actions
        '''
        
        # --- create a session folder ---
        dir_path = "./performance_log/" + timestamp
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        successful_stocking = self.cal_performance()
        
        # --- Write Success Rate to File ---
        fname = dir_path + "/success_rate - " + timestamp + ".txt"
        
        with open(fname, 'w') as f:
            
            f.write("Logged at {}".format(self.get_timestamp(replace = False)))
            f.write("\n")
            f.write("This training session ran episodes: {}".format(self.episodes))
            f.write("\n")
        
            for session in range(len(successful_stocking)):
                f.write("Session {} | Episodes: {} | Success Rate: {:.2f}%".format(session, 
                        self.episodes[session], successful_stocking[session]))
                f.write("\n")
        
        # --- Plot Overall Success Rate by Episode ---
        
        title = "% of Successful Rebalancing - " + timestamp
        
        fig1 = plt.figure()
        plt.plot(self.episodes, successful_stocking)
        plt.xlabel("Episodes")
        plt.ylabel("% Success Rate")
        plt.title(title)
        fig1.savefig(dir_path + "/session_success_rate_" + timestamp)
        
        # --- Plot Reward History by Training Session ---
        
        for session in range(len(self.rewards)):
            
            fig = plt.figure()
            
            title = "Reward History by Training Session " + str(session) + " - " + timestamp
            
            x_axis = [x for x in range(self.episodes[session])]
            plt.plot(x_axis, self.rewards[session], label = "Session "+str(session))
            plt.legend()
            plt.xlabel("Episode")
            plt.ylabel("Reward")
            plt.title(title)
            fig.savefig(dir_path + "/reward_history_session_" + \
                        str(session) + timestamp)
            
        # --- Save Q tables --- 
        
        for session in range(len(self.q_tables)):
            
            self.q_tables[session].to_csv(dir_path + "/q_table_session_" + \
                        str(session) + timestamp + ".csv")
        
        # --- Comparison Line Chart of First and Last Episode for each Session ---
        
        file_path = dir_path + "/action_history"
        
        if not os.path.exists(file_path):
            os.makedirs(file_path)       
        
        
        for session in range(len(self.session_action_history)):
            
            first_eps_idx = 0
            last_eps_idx = len(self.session_action_history[session])-1
            
            fig = plt.figure()
            title = "Session " + str(session) + " - Hourly Action of Eps " + str(first_eps_idx) + " and Eps " + str(last_eps_idx)
            
            x_axis = [x for x in range(len(self.session_action_history[session][0]))]
            plt.plot(x_axis, self.session_action_history[session][0], label = "Eps 0")
            plt.plot(x_axis, self.session_action_history[session][-1], 
                     label = "Eps " + str(last_eps_idx))
            
            plt.legend()
            plt.xlabel("Hours")
            plt.ylabel("Number of Bikes Moved")
            plt.title(title)
            
            fig.savefig(file_path + "/action_history_" + str(session) + timestamp)
            
        return
    
    
