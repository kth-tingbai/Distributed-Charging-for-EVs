# -*- coding: utf-8 -*-
"""
Created on Sun Nov  5 12:59:09 2023

Show Fig.6 of our ECC 2024 paper

@author: tingbai
"""

f=open('Online_charing_waiting_time_2023','r')
a=f.read()
c_w_station_on=eval(a)
f.close()

f=open('Offline_charing_waiting_time_2023','r')
a=f.read()
c_w_station_off=eval(a)
f.close()

c_s_on=[]
w_s_on=[]
w_rate_on=[]

for i in c_w_station_on.keys():
    c_s_on.append(c_w_station_on[i][0])
    w_s_on.append(c_w_station_on[i][1])
    if c_w_station_on[i][2]!=0:
        w_rate_on.append(round(c_w_station_on[i][1]/c_w_station_on[i][2],4))
    else:
        w_rate_on.append(0)
average_rate1=round(sum(w_rate_on)/len(w_rate_on),3)       
 
#average_rate1=round(sum(w_s_on)/sum(c_s_on),4)

c_s_off=[]
w_s_off=[]
w_rate_off=[]

for i in c_w_station_off.keys():
    c_s_off.append(c_w_station_off[i][0])
    w_s_off.append(c_w_station_off[i][1])
    if c_w_station_off[i][2]!=0:
        w_rate_off.append(round(c_w_station_off[i][1]/c_w_station_off[i][2],4))
    else:
        w_rate_off.append(0)
        
average_rate2=round(sum(w_rate_off)/len(w_rate_off),3)
    

    
#%% 
import matplotlib.pyplot as plt
import numpy as np
#import matplotlib.ticker as mticker

# Sample data for charging time and waiting time at 24 stations (in minutes)
charging_times1 = c_s_on
waiting_times1 = w_s_on
charging_times2 = c_s_off
waiting_times2 = w_s_off

# Station indices (x-axis)
station_indices = np.arange(1, 25)

# Width of each bar
bar_width = 0.35

# Create subplots for charging and waiting times
fig, ax1 = plt.subplots(figsize=(22, 17))

# Plot bars for charging time
charging_bars2 = ax1.bar(station_indices - bar_width/2, charging_times2, bar_width, label='Charging time in OS', color='mediumaquamarine')
charging_bars1 = ax1.bar(station_indices + bar_width/2, charging_times1, bar_width, label='Charging time in PS', color='palegreen')


# Plot bars for waiting time
waiting_bars2 = ax1.bar(station_indices - bar_width/2, waiting_times2, bar_width, label='Waiting time in OS', color='crimson')
waiting_bars2 = ax1.bar(station_indices + bar_width/2, waiting_times1, bar_width, label='Waiting time in PS', color='pink')


# Set labels and title
ax1.set_xlabel('Station index',fontsize=32)
ax1.set_ylabel('Time [min]',fontsize=32)
ax1.set_xticks(station_indices)
ax1.legend(loc='upper left',fontsize=28)
ax1.set_ylim(0,900)
# Set font size for x-axis tick labels
ax1.set_xticklabels(station_indices, fontsize=30)  # <-- Set the font size here
y_ticks = ax1.get_yticks()
ax1.set_yticks(y_ticks)
ax1.set_yticklabels(y_ticks.astype(int), fontsize=30)

# Create a secondary y-axis for the usage rate
ax2 = ax1.twinx()

# Plot the average usage rate as a horizontal line
ax2.axhline(y=average_rate2, color='crimson', linestyle='--', linewidth=3, label='Average waiting time in OS')
ax2.axhline(y=average_rate1, color='palevioletred', linestyle='--', linewidth=3, label='Average waiting time in PS')


# Set labels and title for the secondary y-axis
ax2.set_ylabel('Time [min]', color='darkred', fontsize=32)
ax2.legend(loc='upper right', fontsize=28)
# Set y-axis limits for the secondary y-axis from 0 to 1.5
ax2.set_ylim(4, 22)
y_ticks2 = ax2.get_yticks()
ax2.set_yticks(y_ticks2)
ax2.set_yticklabels(y_ticks2.astype(int), color='darkred', fontsize=30)

# Display the average usage rate value as text on the plot
ax2.text(24.55, average_rate1, f'{average_rate1:.1f}', color='darkred', va='center',fontsize=30)
ax2.text(24.55, average_rate2, f'{average_rate2:.1f}', color='darkred', va='center',fontsize=30)

# Set x-axis limits from 1 to 24
plt.xlim(0.5, 24.5)

plt.savefig('Fig6.pdf', bbox_inches='tight') 
#plt.savefig('Fig6.png', format="PNG", dpi=1000) 

# Show the plot
plt.show()
