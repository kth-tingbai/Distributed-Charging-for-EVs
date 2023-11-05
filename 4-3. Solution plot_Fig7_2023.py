# -*- coding: utf-8 -*-
"""
Created on Sun Nov 5 13:02:12 2023


"""

f=open('Stations_map_trucks_150','r')
a=f.read()
station_v_index=eval(a) # the marix showing the truck index and the corresponding station index in the route of the truck
f.close() 

f=open('Travel_times_150','r')
a=f.read()
v_tau=eval(a) # travel times on road segments for 150 trucks [minutes]
f.close()

f=open('Detour_times_150','r')
a=f.read()
v_detour=eval(a) # detoure times to reach charging stations for 150 trucks [minutes]
f.close()


f=open('Remain_battery_online_150trucks','r')
a=f.read()
E_ramp=eval(a)
f.close()


f=open('Solution_online_150trucks','r') # solution, online
a=f.read()
S_on=eval(a)
f.close()

# 1. Compute the charging time of each vehicle
N=150
t_charge={}
for i in range(N):
    t_charge[i]={}

for s in S_on.keys():
    for v in S_on[s].keys():
        t_c=S_on[s][v][0]
        # return the station index
        s_index=station_v_index[s][v]
        t_charge[v][s_index]=round(t_c,4)
        
    
Pcharging=300/60
Pbar=110/60 # energy consumption per travel time [min]
E_end={}
for i in E_ramp.keys():
    e_ramp=list(E_ramp[i].values())[-1]
    tau_last=v_tau[i][-1]
    # check if the vehicle charges at the last charging station
    s_index_last=len(v_detour[i])
    if s_index_last in t_charge[i].keys():
        t_c=t_charge[i][s_index_last]
        t_detour=v_detour[i][-1]
        E_end[i]=round((e_ramp+Pcharging*t_c-Pbar*(2*t_detour+tau_last)),4)
    else:
        E_end[i]=round((e_ramp-Pbar*tau_last),4)
        
E_safe=156
E_full=624
E_end_rate={}
for i in E_end.keys():
    E_end_rate[i]=round((E_end[i]+E_safe)*100/E_full,4)
    

# show the result
import numpy as np
import matplotlib.pyplot as plt


x= np.arange(1, 151)
y=list(E_end_rate.values())

# Plotting nodes on the x-axis and their values on the y-axis
plt.figure(figsize=(22, 17))
plt.scatter(x, y, color='cornflowerblue', marker='o', s=400, alpha=0.7, label='Residual battery of each truck')

plt.axhline(y=25, color='red', linestyle='--', linewidth=4, label='Safe Margin')

# Adding labels and title
plt.xlabel('Truck index', fontsize=32)
plt.ylabel('Battery [%]', fontsize=32)
plt.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
plt.xlim(0.5, 150.3)
plt.ylim(24, 40)

plt.xticks([1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,110,120,130,140,150], ['1','10','20','30','40','50','60','70','80','90','100', '110','120','130','140','150'], fontsize=30)
plt.yticks([24,25,26,28,30,32,34,36,38,40], ['24','25','26','28','30','32','34','36','38','40'], fontsize=30)

plt.legend(fontsize=27)
# Display the plot

plt.savefig('Fig7.pdf', bbox_inches='tight') 
#plt.savefig('Fig7.png', format="PNG", dpi=1000) 
plt.show()
    
        
    
    




