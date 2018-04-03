#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  4 15:54:01 2018

@author: Ian

This is the main workflow of the RL program.

"""

from training import trainer

if __name__ == "__main__":
    
    
    # Train an Agent
    episode_list = [eps for eps in range(100, 150, 100)]
    
    trainer = trainer()
    
    # ---- Bike Stock Parameters ----
    # linear: a linear increasing bike stock with 3 additional bikes per hour
    # random: a linear increasing bike stock with random fluctuation
    # actual_1: randomly pick traffic from one citibike stations
    # -------------------------------
    
    trainer.start(episode_list, "actual_1", logging  = 
                  True, env_debug = False, rl_debug = False)
    
    
    # Run an Agent
    
    # TO BE DEVELOPED
    # Run an agent on some new environments with Q Table learned from above
    # Measure performance on operating in new environment