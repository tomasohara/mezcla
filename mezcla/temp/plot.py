#!/usr/bin/env python3

## 2023-12-30 19:09 (+05:45 GMT)
## plot.py was created to get statistics about the time consumed on CPU instances (JarvisLabs.ai)

import matplotlib.pyplot as plt

USE_GPU = True
time_consumed_cpu = [39.2, 40.2, 40.3, 39.6, 39.5, 39.4, 40.1, 39.5, 37.9, 38.6, 38.8, 38.8, 38.9, 39.6, 39.6]
time_consumed_gpu = [28.212, 25.740, 27.163, 25.947, 27.393, 28.302, 26.352, 26.979, 27.7, 26.36, 29.95, 26.941, 27.5, 27.5, 27.046]
time_arr = time_consumed_gpu if USE_GPU else time_consumed_cpu

# # For boxplot
def box_plot(time_consumed, title:str="Time Consumed"):
    plt.boxplot(time_consumed)
    plt.xlabel('Test Number')
    plt.ylabel('Consumption (sec.)')
    plt.title(title)
    plt.show()

# For bar plot
def bar_plot(time_consumed, title:str="Time Consumed"):
    plt.bar(range(len(time_consumed)), time_consumed, color='skyblue')
    plt.xlabel('Test Number')
    plt.xticks(range(len(time_consumed)))
    plt.ylabel('Consumption (sec.)')
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

bar_plot(time_arr, "Time Consumed by JarvisLabs (GPU): RTX A5000 16GB")