# -*- coding: utf-8 -*-
"""
Created on Mon Oct  9 13:09:22 2023

Functions used to evaluate the dynamics and real waiting time of each vehicle


@author: tingbai
"""

import numpy as np
from dateutil.parser import parse
from datetime import timedelta
import copy

# 3.3.3 define a function to assign the port to individual trucks
# at each time, determine the vehicles that need to assign a port
def v_assign(Dynamics_v_0, t_sys):
    t_start='2023-07-01 08:00:00'
    v_to_assign={}
    for s in Dynamics_v_0.keys():
        v_to_assign[s]={}
        for v in Dynamics_v_0[s].keys():
            if list(Dynamics_v_0[s][v].keys())[0]=='d':
                t_arr=Dynamics_v_0[s][v]['d'][1]
                t_diff=np.array([(parse(t_arr)-parse(t_start)).total_seconds()-t_sys*60])
                t_diff_norm=np.linalg.norm(t_diff, ord=None)
                if (t_diff_norm<30):
                    v_to_assign[s][v]=Dynamics_v_0[s][v]['d']
    v_to_assign_final=copy.deepcopy(v_to_assign)
    for s in v_to_assign.keys():
        if v_to_assign[s]=={}:
            del v_to_assign_final[s]
            
    return v_to_assign_final
      

def Assign_port(p_occupy, v_ass):
    # given the current system time, and the occupancy of the ports
    # return the waiting time, port assignment, and the updated occupancy of the ports
    for s in v_ass.keys():
        for v in v_ass[s].keys():
            t_arr=v_ass[s][v][1]
            t_charge=v_ass[s][v][2]
            label=0
            for p in p_occupy[s].keys():
                if p_occupy[s][p]==[]:
                    t_n_available=(parse(t_arr)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    p_occupy[s][p]=t_n_available
                    v_ass[s][v][3]=[0,p]
                    label=1
                    break
            if label==0:
                t_ava=[]
                for p in p_occupy[s].keys():
                    t_ava.append(p_occupy[s][p])
                t_min=min(t_ava)
                if t_min<=t_arr:
                    t_n_available=(parse(t_arr)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    v_ass[s][v][3]=[0,[k for k,v in p_occupy[s].items() if v==t_min][0]]
                    p_occupy[s][[k for k,v in p_occupy[s].items() if v==t_min][0]]=t_n_available
                    label=1
                else:
                    t_n_available=(parse(t_min)+timedelta(seconds=t_charge*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    v_ass[s][v][3]=[round((parse(t_min)-parse(t_arr)).total_seconds()/60,4),[k for k,v in p_occupy[s].items() if v==t_min][0]]
                    p_occupy[s][[k for k,v in p_occupy[s].items() if v==t_min][0]]=t_n_available
                    label=1
    return p_occupy, v_ass


def Dynamics_Solution_update(v_ass_wait, Dynamics_v_0, S_vehicles_0, v_tau, v_detour, station_v_index):
    
    # update the dynamics (Dynamics_v_0) and solutions (S_vehicles_0) of each vehicle based on the assignment results of the vehicles in v_ass
    for s in v_ass_wait.keys():
        #if v_ass_wait[s]!={}:
            for v in v_ass_wait[s].keys():
                Dynamics_v_0[s][v]['ass']=v_ass_wait[s][v] # add the assignment result of the vehicle at the current station 
                del Dynamics_v_0[s][v]['d'] # remove the original one 
                
                # update the waiting time 
                t_wait=v_ass_wait[s][v][3][0]
                k_current=v_ass_wait[s][v][0] # the index of the current station
                S_vehicles_0[v]['t_w'][k_current-1]=t_wait # update the waiting time
                
                # compute the deterministic arrival time of the vehicle at next charging station
                b_charge=S_vehicles_0[v]['b_c']
                s_index_charge=[]
                for c in range(len(b_charge)):
                    if b_charge[c]==1:
                        s_index_charge.append(c+1)
                k_next=0
                for i in range(len(s_index_charge)):
                    if s_index_charge[i]==k_current:
                        if i!=len(s_index_charge)-1:
                            k_next=s_index_charge[i+1] # the index of the next charging station that vehicle v will visit
                
                # if there is another charing station to visit, compute the deterministic arrival time at the charging station k_next
                if k_next!=0:
                    # update the arrival time and charging time at the next charging station
                    t_charge=v_ass_wait[s][v][2]
                    t_dep=(parse(v_ass_wait[s][v][1])+timedelta(seconds=(t_charge+t_wait)*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] # departure time from the current charging station
                    t_arr_next=(parse(t_dep)+timedelta(seconds=(v_detour[v][k_current-1]+v_detour[v][k_next-1]+sum(v_tau[v][k_current:k_next]))*60)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    t_charge_next=S_vehicles_0[v]['t_c'][k_next-1]
                    
                    # obtain the coordinate of the next charging station
                    for t in station_v_index.keys():
                        if v in station_v_index[t].keys():
                            if station_v_index[t][v]==k_next:
                                s_coor=t
                    # update Dynamics_v_0
                    Dynamics_v_0[s_coor][v]={}
                    Dynamics_v_0[s_coor][v]['d']=[k_next, t_arr_next, t_charge_next,0]
                    
    
            
    return Dynamics_v_0, S_vehicles_0