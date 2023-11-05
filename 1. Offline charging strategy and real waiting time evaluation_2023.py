# -*- coding: utf-8 -*-
"""
Created on Nov 5 2023

1. Charging strategy of each truck computed offline;
2. 150 trucks, 24 physical charging stations, where each station is indexed via a unique coordinate
3. Offline solution, online evaluation 

"""

f=open('Travel_times_150','r')
a=f.read()
v_tau=eval(a) # travel times on road segments for 150 trucks [minutes]
f.close()

f=open('Detour_times_150','r')
a=f.read()
v_detour=eval(a) # detoure times to reach charging stations [minutes]
f.close()

f=open('Departure_times_150','r')
a=f.read()
t_departure=eval(a) # deparutre times
f.close()

f=open('Ini_battery_bound_150','r')
a=f.read()
eini_lbound=eval(a) # lowerbound of the initial battery [kWh]
f.close()

f=open('Stations_map_trucks_150','r')
a=f.read()
station_v_index=eval(a) # the matrix showing the truck index and the corresponding station index in the route of the truck
f.close()               # Format: {(station coordinate):{truck index1: station index (i.e.,k),}{truck index2: station index (i.e., k')},...}
              

station_capacity_new={}
for s in station_v_index.keys():
    station_capacity_new[s]=3
    
#P=300kW at every charging station, electricity price is 0.36 EUR/kWh

import numpy as np
import time
from Rollout_individual_vehicle_2023 import road_charge, regulation_market, EV_charge

# 1. Parameter settings
Pmax = 375/60  #P_max=375kWh
Pbar=110/60 # i.e., 1.83kWh/min energy consumption of every truck 
tp = 0
Tbard = 9*60 #[min] the maximum daily driving time
DeltaT = 160 # the upper bound on the extra time spent due to charging and rest (i.e., waiting budget)
price = 0.36/0.4 # price of the electricity
overdue = 5 # cost for violating the delivery deadline
eusable = 468 # 624-156=468


# 2. Main function: Open-loop, compute once for each vehicle
N=150 # number of vehicles
S_openloop={} # open-loop solution
from tqdm import tqdm # used to show the progress bar

for v in tqdm(range(N)):
    S_openloop[v]={}
    tau=np.array(v_tau[v])
    #detour_list=[round(i,4) for i in v_detour[v]] # change the detour time as hour
    detour_list=v_detour[v]
    detour=np.array(detour_list)
    e_ini=eini_lbound[v]
    Pcharging=np.array([300/60]*len(detour))
    road=road_charge(tau, detour, Pcharging)
    regulation=regulation_market(Tbard, DeltaT, price, overdue)
    ev=EV_charge(Pmax, eusable, e_ini, Pbar, tp)
    
    # compute the base policy
    ev.base_policies(road, regulation)
    
    #% The linearization solution (LS)
    start_t=time.perf_counter()
    cost, b_charge, t_charge, b_violate=ev.best_linearization(road, regulation)
    end_t=time.perf_counter()
    interval_t= round((end_t-start_t)/4,4) 
    
    
    S_openloop[v]['op']=[cost,b_charge,t_charge,b_violate,interval_t] #optimal linearization solution
    

#%%
# 3. Open-loop performance (Upper bound, i.e., the worest case without coordination)
# Considering local limitations on the number of charging ports, recompute the real travel time and utility for every truck
# That is, compute the extra waiting time due to the limited charging resource


# 3.1 For each station, collect vehicles that will charge at the station, and their charging time.
v_plan_charge={} # trucks planning to charge at a station
q='op'
for s in station_v_index.keys():
    # check whether the potential trucks will drop by for charging
        
    v_plan_charge[s]={}
    for v in station_v_index[s].keys():
        k=station_v_index[s][v]
        if S_openloop[v][q][1][k-1]==1:
            v_plan_charge[s][v]=k #{(coordinate of station):{vehicle index: {index of the station in the route of the vehicle}, ...}}
            
# 3.2 Compute stations that need to assign ports to vehicles based on their capacities and the charging requirements
s_with_q={} # stations where trucks may need to wait for having access to a port
for s in station_capacity_new.keys():
    port_max=station_capacity_new[s]
    if len(v_plan_charge[s])>station_capacity_new[s]:
        s_with_q[s]=v_plan_charge[s] # stations that trucks have decided to visit 

        
# 3.3 Online Evaluaiton (compute the waiting time of every vehicle at those stations in s_with_q)

# Initialization to vehicle dynamics
Dynamics_v={} # dynamics of every vehicle
# 3.3.1 initialize the dynamics
for s in s_with_q.keys():
    Dynamics_v[s]={}
    for v in s_with_q[s].keys():
        Dynamics_v[s][v]={}
        v_charge=[]
        for c in range(len(S_openloop[v][q][1])):
            if S_openloop[v][q][1][c]==1:
                v_charge.append(c+1) # the index of charging stations that vehicle v will visit
        if v_charge[0]==s_with_q[s][v]:
            Dynamics_v[s][v]['d']=[v_charge[0],0,S_openloop[v][q][2][v_charge[0]-1],0] #'d' means that it is the current station with deterministic arrival time
            # [station index, the initial arrival time, charging time, waiting time at the first charging station]
                

# 3.3.2 compute the arrival time at the first charging station, which is deterministic
from datetime import timedelta
from dateutil.parser import parse
Dynamics_v_0={} # the deterministic arrival time, charging time of each vehicle at its first charging station
for s in Dynamics_v.keys():
    Dynamics_v_0[s]={}
    for v in Dynamics_v[s].keys():
        if Dynamics_v[s][v]!={}:
            Dynamics_v_0[s][v]={}
            t_dep=t_departure[v] # deperture time from the origin
            h_index=Dynamics_v[s][v]['d'][0]
            t_travel=(sum(v_tau[v][:h_index])+v_detour[v][h_index-1])*60 # seconds
            t_arr=(parse(t_dep)+timedelta(seconds=t_travel)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            Dynamics_v_0[s][v]['d']=[h_index,t_arr,Dynamics_v[s][v]['d'][2],0] # the last two elements are charging time and waiting time
            
                
# Initialize the occupancy of the ports
p_occupy_0={}
for s in s_with_q.keys():
    p_occupy_0[s]={}
    for p in range(station_capacity_new[s]):
        p_occupy_0[s][p]=[]      

        
# Initialize the solution of each vehicle
S_vehicles_0={}
for v in S_openloop.keys():
    S_vehicles_0[v]={}
    b_charge=list(S_openloop[v][q][1])
    t_charge=list(S_openloop[v][q][2])
    t_wait=[0]*len(b_charge)
    S_vehicles_0[v]['b_c']=b_charge
    S_vehicles_0[v]['t_c']=t_charge
    S_vehicles_0[v]['t_w']=t_wait
    

#%%                                

from Realtime_evaluation import v_assign, Assign_port, Dynamics_Solution_update

# The main loop
delta_t=1 #min
for t_sys in tqdm(range(0,800,delta_t)): #required: 10h, 600min
    
    # 1. determine which vehicle needs to assign a port to
    v_ass=v_assign(Dynamics_v_0,t_sys)
    
    if v_ass!={}:
        # 2. assign the port to vehicles, update p_occupy and compute waiting time of each vehicle at the port
        p_occupy, v_ass_wait=Assign_port(p_occupy_0, v_ass) # v_ass_wait is the updated v_ass where the waiting time of each vehicle is determined
        # 3. update Dynamics_v_0 and S_vehicles_0 (compute the deterministic arrival time at the next charging station based on the port assignment)
        Dynamics_v, S_vehicles=Dynamics_Solution_update(v_ass_wait, Dynamics_v_0, S_vehicles_0, v_tau, v_detour, station_v_index)


wait_v={}
for i in S_vehicles.keys():
    t=S_vehicles[i]['t_w']
    if sum(t)!=0:
        wait_v[i]=sum(t)
len(wait_v)
sum(wait_v.values())/60


# Dynamics_v: {(station):{vehicle:{'ass':[s_index, t_arr_s, t_charge, t_wait]}}}
f=open('Dynamics_offline_150trucks','w') # the dynamics of 150 trucks, offline
f.write(str(Dynamics_v))
f.close()

f=open('Solution_offline_150trucks','w') # solution of 150 trucks, offline
f.write(str(S_vehicles))
f.close()

f=open('Waiting_time_offline_150trucks','w') # waiting time of 150 trucks, offline
f.write(str(wait_v))
f.close()


