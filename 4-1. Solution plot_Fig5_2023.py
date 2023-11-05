# -*- coding: utf-8 -*-
"""
Created on Sun Nov 5 12:41:49 2023

Fig.5: Real waiting times of individual trucks (for our ECC 2024 paper)

"""

f=open('Waiting_time_offline_150trucks','r') # waiting time, offline
a=f.read()
w_t_off=eval(a)
f.close()

f=open('Waiting_time_online_150trucks','r') # waiting time, online
a=f.read()
w_t_on=eval(a)
f.close()

    
#%% Show the waiting times of vehicles in two methods
import matplotlib.pyplot as plt

# sort the vehicle index according to their waiting times 
w_t_off_sorted=dict(sorted(w_t_off.items(), key=lambda item: item[1]))
wait_off=list(w_t_off_sorted.values()) # list of sorted waiting times, offline

w_t_on_sorted=dict(sorted(w_t_on.items(), key=lambda item: item[1]))
wait_on=list(w_t_on_sorted.values())
wait_on_new=[0]*(len(wait_off)-len(wait_on))+wait_on # list of sorted waiting times, online
    
v_x=range(1, len(wait_off)+1)
    
total_width, n = 2, 2
width = total_width / n

fig, ax1 = plt.subplots(figsize=(22, 17)) 
ax1.bar(v_x, wait_off, width=width, label="Offline charging strategy", fc='lightsteelblue')
ax1.bar(v_x, wait_on_new, width=width, label="Proposed charging strategy", fc ='lemonchiffon')

ax1.set_ylim(0, 80)
plt.xlim(0.5, 48)
ax1.set_xlabel("Truck index sorted", fontsize=32) 
ax1.set_xticks([1, 5, 10, 15, 20,25, 30,35, 40,45, 48])
ax1.set_xticklabels([1, 5, 10, 15, 20,25, 30,35, 40,45, 48], fontsize=30)
ax1.set_yticks([0,10,20,30,40,50,60,70,80])
ax1.set_yticklabels([0,10,20,30,40,50,60,70,80], fontsize=30)
ax1.set_ylabel("Waiting time [min]",fontsize=32)
ax1.legend(loc='upper left',fontsize=27)
plt.grid(color='gray', linestyle=':', linewidth=0.2)
plt.savefig('Fig_5.pdf', bbox_inches='tight') 
#plt.savefig('Fig_5.png', format="PNG", dpi=1000) 
plt.show()