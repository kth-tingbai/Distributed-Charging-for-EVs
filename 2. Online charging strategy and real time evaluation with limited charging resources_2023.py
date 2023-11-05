# -*- coding: utf-8 -*-
"""
Created on Sun Nov 5 12:17:52 2023

1. Real-time ramp-based charging strategy considering limited charging resources at each station 
2. 150 trucks, 24 charging stations

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
station_v_index=eval(a) # the martix showing the truck index and the corresponding station index in the route of the truck
f.close()               # Format: {(station coordinate):{truck index1: station index (i.e.,k),}{truck index2: station index (i.e., k')},...}

station_capacity_new={}
for s in station_v_index.keys():
    station_capacity_new[s]=3
    

#%% 1. For each vehicle arriving at a ramp, recompute its charging strategy

# 1.1 Parameter settings

#P_max=375kWh, bar_P=1.83kWh/min, P=300kW at every charging station, electricity price is 0.36 EUR/kWh

import numpy as np
import time


# 1.2. Main function: compute the charging strategy for each vehicle once it arrives at a ramp
N=150 # number of vehicles

# online solution initialization
from datetime import timedelta
from dateutil.parser import parse
S_online={} #solution of each vehicle made at each ramp in the route
for v in range(N):
    S_online[v]={}
    S_online[v]['s']={}
    for r in range(len(v_detour[v])):
        S_online[v]['s'][r+1]={}

# Deterministic arrival time of vehicles at a ramp and a charging station
Det_arr_ramp={}
for v in range(N):
    Det_arr_ramp[v]={}
    for r in range(len(v_detour[v])):
        t_start=t_departure[v]
        if r==0:
            t_tra=v_tau[v][r]*60
            Det_arr_ramp[v][r+1]=(parse(t_start)+timedelta(seconds=t_tra)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
        else:
            Det_arr_ramp[v][r+1]=0
        
# Remaining battery at each ramp
E_ramp={}
T_delta={}
Pbar=110/60

for v in range(N):
    E_ramp[v]={}
    T_delta[v]={}
    e_ini=eini_lbound[v] # change the initial battery slightly
    DeltaT=160 # initial extra time budget
    for r in range(len(v_detour[v])):
        if r==0:
            t_tra=v_tau[v][r]
            E_ramp[v][r+1]=round(e_ini-Pbar*t_tra,4)
            T_delta[v][r+1]=DeltaT
        else:
            E_ramp[v][r+1]=0
            T_delta[v][r+1]=0
    
# Initialize the occupancy of the ports at each station
p_occupy={}
for s in station_v_index.keys():
    p_occupy[s]={}
    for p in range(station_capacity_new[s]):
        p_occupy[s][p]=[]  
    
# Initialize the queue at each station
station_queue={}
for s in station_v_index.keys():
    station_queue[s]={}
    
# Real charging and waiting time of a vehicle at each station
t_charge_wait={}
for s in station_v_index.keys():
    t_charge_wait[s]={}
    

#%%
# Functions used 

# Function 1: At each time instant, determine which vehicle arrives at a ramp and needs to recompute its optimal charging strategy
def v_ramp_arrival(Det_arr_ramp, t_sys):
    t_start='2023-07-01 08:00:00'
    
    v_arr_ramp={}
    for v in Det_arr_ramp.keys():
        for r in Det_arr_ramp[v].keys():
            if Det_arr_ramp[v][r]!=0:
                t=Det_arr_ramp[v][r]
                t_diff=np.array([(parse(t)-parse(t_start)).total_seconds()-t_sys*60])
                t_diff_norm=np.linalg.norm(t_diff, ord=None)
                if (t_diff_norm<30):
                    v_arr_ramp[v]={}
                    v_arr_ramp[v][r]=Det_arr_ramp[v][r]
                    
    return v_arr_ramp

# Function 2: At each time instant, determine which station needs to update the occupancy of the ports based on the vehicles arrived at the station
import copy
def station_need_update(station_queue, t_sys):
    t_start='2023-07-01 08:00:00'
    
    s_need_update={}
    for s in station_queue.keys():
        if station_queue[s]!={}:
            s_need_update[s]={}
            for v in station_queue[s].keys():
                t_arr_v=station_queue[s][v][0]
                t_diff=np.array([(parse(t_arr_v)-parse(t_start)).total_seconds()-t_sys*60])
                t_diff_norm=np.linalg.norm(t_diff, ord=None)
                if (t_diff_norm<30):
                    s_need_update[s][v]=station_queue[s][v]
            if s_need_update[s]=={}:
                del s_need_update[s]
                    
    s_need_update_sorted={}
    if s_need_update!={}:
        for s in s_need_update.keys():
            s_need_update_sorted[s]=dict(sorted(s_need_update[s].items(), key=lambda item: item[1][0])) # sort the vehicle index based on their arrival times at the station
    else:
        s_need_update_sorted=copy.deepcopy(s_need_update)
        
    return s_need_update_sorted
    
        
# Function 3: Assign ports to vehicles at stations in s_need_update, based on the arrival time of vehicles
def Assign_port_online_new(s_coor, v, t_arr_s, t_charge, p_occupy, t_charge_wait):
    # given the current system time, and the occupancy of the ports
    # return the waiting time, port assignment, and the updated occupancy of the ports
    
    label=0
    for p in p_occupy[s_coor].keys():
        if p_occupy[s_coor][p]==[]:
            t_n_available=(parse(t_arr_s)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            p_occupy[s_coor][p]=t_n_available
            t_charge_wait[s_coor][v]=[t_charge, 0, p] # p: port index 
            label=1
            break
    if label==0:
        t_ava=[]
        for p in p_occupy[s_coor].keys():
            t_ava.append(p_occupy[s_coor][p])
        t_min=min(t_ava)
        if t_min<=t_arr_s:
            t_n_available=(parse(t_arr_s)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            t_charge_wait[s_coor][v]=[t_charge, 0, [k for k,v in p_occupy[s_coor].items() if v==t_min][0]]
            p_occupy[s_coor][[k for k,v in p_occupy[s_coor].items() if v==t_min][0]]=t_n_available
            label=1
        else:
            t_n_available=(parse(t_min)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            t_charge_wait[s_coor][v]=[t_charge, round(((parse(t_min)-parse(t_arr_s)).total_seconds())/60,4), [k for k,v in p_occupy[s_coor].items() if v==t_min][0]]
            p_occupy[s_coor][[k for k,v in p_occupy[s_coor].items() if v==t_min][0]]=t_n_available
            label=1
                    
    return p_occupy, t_charge_wait  

# Function 4: The feedback waiting time from the station
def Feedback_from_station(p_occupy, s_coor, t_arr_s):
    label=0
    for p in p_occupy[s_coor].keys():
        if p_occupy[s_coor][p]==[]:
            t_wait=0
            label=1
            break
    if label==0:
        t_ava=[]
        for p in p_occupy[s_coor].keys():
            t_ava.append(p_occupy[s_coor][p])
        t_min=min(t_ava)
        if t_min<=t_arr_s:
            t_wait=0
            label=1
        else:
            t_wait=round(((parse(t_min)-parse(t_arr_s)).total_seconds())/60,4)
            label=1
        
    return t_wait
    
    
# Function 4: Compute the charging strategy for a vehicle that arrived at a ramp
def charging_solution_at_ramp(v, r_index, r_detour, r_tau, e_ini_r, DeltaT_r, t_wait_s):
#def charging_solution_at_ramp(v, r_index, r_detour, r_tau, e_ini_r, DeltaT_r, wait_r): wait_r in minutes
    
    S_v={}
    S_v[v]={}
    S_v[v][r_index]={}
    
    from Rollout_individual_vehicle_new2023 import road_charge, regulation_market, EV_charge

    Pmax = 375/60  #P_max=375kWh
    Pbar=110/60 # i.e., 1.83kWh/min energy consumption of every truck 
    Tbard = 9*60 #[min] the maximum daily driving time !!!! should consider later if it is needed
    price = 0.36/0.4 # price of the electricity
    overdue = 5 # cost for violating the delivery deadline
    eusable = 468
    
    
    tau=np.array(r_tau)
    detour=np.array(r_detour)
    Pcharging=np.array([300]*len(detour))/60
    #road=road_charge(tau, detour, Pcharging, [0]+[0]*(len(r_detour)-1)) #C1
    #road=road_charge(tau, detour, Pcharging, [t_wait_s]+[0]*(len(r_detour)-1)) #C2
    road=road_charge(tau, detour, Pcharging, [t_wait_s]+[12]*(len(r_detour)-1)) #C3, road=road_charge(tau, detour, Pcharging, wait)
    regulation=regulation_market(Tbard, DeltaT_r, price, overdue)
    ev=EV_charge(Pmax, eusable, e_ini_r, Pbar)
    
    #---------
    # compute the base policy
    ev.base_policies(road, regulation)
    
    # Three rollout-based solutions (RS)
    # using timid base policy
    #start_t1=time.perf_counter() # set a clock
    #cost1, b_charge1, t_charge1, b_violate1=ev.rollout(ev.timid_charging, ev.timid_overdue, road, regulation) 
    #end_t1=time.perf_counter()
    #interval_t1= round((end_t1-start_t1)/4,4) # computation time
    
    # using greedy base policy
    #start_t2=time.perf_counter() # set a clock
    #cost2, b_charge2, t_charge2, b_violate2=ev.rollout(ev.greedy_charging, ev.greedy_overdue, road, regulation) 
    #end_t2=time.perf_counter()
    #interval_t2= round((end_t2-start_t2)/4,4) # computation time
    
    # using relaxed base policy
    #start_t3=time.perf_counter() 
    #cost3, b_charge3, t_charge3, b_violate3=ev.rollout(ev.relaxed_charging, ev.relaxed_overdue, road, regulation) #
    #end_t3=time.perf_counter()
    #interval_t3= round((end_t3-start_t3)/4,4) # computation time

    #% The linearization solution (LS)
    start_t4=time.perf_counter()
    cost4, b_charge4, t_charge4, b_violate4=ev.best_linearization(road, regulation)
    end_t4=time.perf_counter()
    interval_t4= round((end_t4-start_t4)/4,4) 
    
    #S_v[v]['s1']=[cost1,b_charge1,t_charge1,b_violate1,interval_t1] # timid base policy
    #S_v[v]['s2']=[cost2,b_charge2,t_charge2,b_violate2,interval_t2] # greedy base policy
    #S_v[v]['s3']=[cost3,b_charge3,t_charge3,b_violate3,interval_t3] # relaxed base policy 
    S_v[v][r_index]['s']=[cost4,list(b_charge4),list(t_charge4),b_violate4,interval_t4] # optimal linearization solution
   
    return S_v

        
# Function 5: update the deterministic arrival time of vehicles that are assigned a port with, the remaining battery and waiting budget 
def v_state_update_new(Det_arr_ramp, s_coor, v, t_arr_s, t_charge, t_charge_wait_update, station_v_index, v_tau, v_detour, E_ramp, T_delta):
    
    Pcharging=300/60
    Pbar=110/60
    # update the arrival time
    
    k=station_v_index[s_coor][v] # station index in the route of vehicle v
    if k!=len(v_detour[v]): # i.e., there is still next ramp
        t_wait=t_charge_wait_update[s_coor][v][1] # waiting time due to the queue (in minutes)
        t_dep=(parse(t_arr_s)+timedelta(seconds=(t_charge+t_wait)*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] # deterministic departure time from the station
        
        # compute and update the arrival time at the next ramp
        t_arr_next=(parse(t_dep)+timedelta(seconds=(v_detour[v][k-1]+v_tau[v][k])*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
        Det_arr_ramp[v][k+1]=t_arr_next
        
        # update the remaining battery and waiting budget
        e_s=E_ramp[v][k] # the remaining battery at the k-th ramp
        E_ramp[v][k+1]=round(e_s+Pcharging*t_charge-2*Pbar*v_detour[v][k-1]-Pbar*v_tau[v][k],4)
        
        # update the remaining waiting budget
        wait_r=T_delta[v][k]
        T_delta[v][k+1]=round((wait_r-(2*v_detour[v][k-1]+t_charge+t_wait)),4)
                
    return Det_arr_ramp, E_ramp, T_delta
                

#%%    

from tqdm import tqdm # used to show the progress bar

# The main loop
delta_t=1 #min
Pbar=110/60
for t_sys in tqdm(range(0,800,delta_t)): #required: 10h, 600min
    
    # 1. determine vehicles that arrived at a ramp and need to compute the charging strategy 
    v_arrived_ramps=v_ramp_arrival(Det_arr_ramp, t_sys)
   
    
    # 2. For each vehicle in v_arrived_ramps, compute its rollout-based charging strategy
    if v_arrived_ramps!={}:
        
        for v in v_arrived_ramps.keys():
            #S_online[v]['s']
            # 2.1 determine the list of tau and detour
            r_index=list(v_arrived_ramps[v].keys())[0]
            r_detour=v_detour[v][(r_index-1):]
            r_tau=[0]
            for i in v_tau[v][r_index:]:
                r_tau.append(i)
            
            # 2.2 determine the remainig battery at the ramp, i.e., e_ini_r
            #e_ini_r=remain_battery_ramp(v,r_index,E_ramp_0,S_online)
            e_ini_r=E_ramp[v][r_index]
    
            # 2.3 determine the DeltaT (the remaining extra waiting budget, including charging, detour and waiting)
            DeltaT_r=T_delta[v][r_index]
            
            # 2.4 communication with the connected charging station: get "tp" for the current charging station
            # get the coordinate of the current station
            for s in station_v_index.keys():
                for t in station_v_index[s].keys():
                    if t==v and station_v_index[s][v]==r_index:
                        s_coor=s
            
            # the arrival time at the station
            t_detour=r_detour[0]*60 # change the detour time (minutes) into seconds
            t_arr_r=v_arrived_ramps[v][r_index] # arrival time at the ramp
            t_arr_s=(parse(t_arr_r)+timedelta(seconds=t_detour)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] # arrival time at the charging station
            
            # the feedback minimum waiting time from the closest station
            t_min_wait=Feedback_from_station(p_occupy, s_coor, t_arr_s)
            
        
            # 2.5 compute the online solution at the ramp r_index
            S_v_ramp=charging_solution_at_ramp(v,r_index,r_detour,r_tau,e_ini_r,DeltaT_r,t_min_wait) # solution at a ramp: cost, b_charge, t_charge, b_violate, computation time
        
            # 2.6 update the solution of vehicle v in S_online
            S_online[v]['s'][r_index]=S_v_ramp[v][r_index]['s']
    
            
            # If the vehicle decides to charge at the connected station
            # 2.7 update the deterministic arrival time of vehicle v at the charging station corresponding to the current ramp r_index
            
            if S_v_ramp[v][r_index]['s'][1][0]==1: # i.e., the vehicle will visit the charging approaching station 
                
                t_charge=S_online[v]['s'][r_index][2][0]# charging time [minutes]
            
                # add the arrival time of the vehicle to the potential queue  
                station_queue[s_coor][v]=[t_arr_s,t_charge] # t_arr_s is the arrival time of vehicle v at the station s_coor
                
                # assign the port to the vehicle
                p_occupy_update,t_charge_wait_update=Assign_port_online_new(s_coor, v, t_arr_s, t_charge, p_occupy, t_charge_wait)
                
                # update the deterministic arrival time of the vehicle at next ramp, the remaining energy and its waiting budget (once the port is assigned, the arrival time at next ramp is determined)
                Det_arr_ramp, E_ramp, T_delta=v_state_update_new(Det_arr_ramp, s_coor, v, t_arr_s, t_charge, t_charge_wait_update, station_v_index, v_tau, v_detour, E_ramp, T_delta)
                
            # If the vehicle decides not to charge at the connected station
            else:
                if r_index!=len(v_detour[v]): # i.e., there is other ramps
                    # update the deterministic arrival time of vehicle v at the next ramp
                    t_dep=v_arrived_ramps[v][r_index]
                    t_arr_next=(parse(t_dep)+timedelta(seconds=(v_tau[v][r_index])*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    Det_arr_ramp[v][r_index+1]=t_arr_next
                    
                    # update the remaining battery of vehicle at the next ramp
                    E_ramp[v][r_index+1]=round(E_ramp[v][r_index]-Pbar*v_tau[v][r_index],4)
                    
                    # update the remaining waiting budget of vehicle at the next ramp
                    T_delta[v][r_index+1]=T_delta[v][r_index]
                    
                    
# compute the waiitng time
wait_t={}
wait_t_sum={}
for v in range(N):
    wait_t[v]=[]
    wait_t_sum[v]={}
    
for s in t_charge_wait_update.keys():
    if t_charge_wait_update[s]!={}:
        for v in t_charge_wait_update[s].keys():
            wait_t[v].append(t_charge_wait_update[s][v][1])
            
for v in wait_t.keys():
    wait_t_sum[v]=round(sum(wait_t[v]),3)
    
wait_v_0=[]
wait_v={}
for v in wait_t_sum.keys():
    if wait_t_sum[v]==0:
        wait_v_0.append(v)
    else:
        wait_v[v]=wait_t_sum[v]
        
print(len(wait_v))

print(sum(wait_v.values())/60)

    
# Det_arr_ramp: {vehicle:{s_index: t_arr_s}}
f=open('Dynamics_online_150trucks','w') # the dynamics of 150 trucks, online
f.write(str(Det_arr_ramp))
f.close()


f=open('Solution_online_150trucks','w') # solution (i.e., charging and waiting time) of 150 trucks, online
f.write(str(t_charge_wait_update))
f.close()
        

f=open('Waiting_time_online_150trucks','w') # waiting time of 150 trucks, online
f.write(str(wait_v))
f.close()
        
                
f=open('Arrival_time_online_150trucks','w') # arrival and charging time of each vehicle at a station
f.write(str(station_queue))
f.close()
        

f=open('P_occupy_online_150trucks','w') # Occupancy of ports of 150 trucks, online
f.write(str(p_occupy_update))
f.close()
        
                
f=open('Remain_battery_online_150trucks','w') # Remaining battery of 150 trucks upon arriving at every ramp, online
f.write(str(E_ramp))
f.close()
                
f=open('Remain_waiting_budget_online_150trucks','w') # Remaining waiting budget of 150 trucks upon arriving at every ramp, online
f.write(str(T_delta))
f.close()
                
                
                
            
            
                
                        
                        
                    
            
            
        
        
        
        
        
        


