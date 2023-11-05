# -*- coding: utf-8 -*-
"""
Created on Sun Nov  5 12:49:30 2023

Handle the obtained simulation results and prepare data for plotting.

"""

# Compute the total charging time and wating time at each port

f=open('Solution_online_150trucks','r') # solution, online
a=f.read()
S_on=eval(a)
f.close()
    
f=open('Arrival_time_online_150trucks','r')
a=f.read()
station_queue=eval(a)
f.close()

f=open('P_occupy_online_150trucks','r')
a=f.read()
p_occupy=eval(a)
f.close()

f=open('Solution_offline_150trucks','r')  # solution, offline
a=f.read()
S_off=eval(a)
f.close()

f=open('Stations_map_trucks_150','r')
a=f.read()
station_v_index=eval(a) # the marix showing the truck index and the corresponding station index in the route of the truck
f.close() 
        

# Handling the data of the proposed charging strategy
# 1. Map coordinates to stations
S_name={}
for i in range(len(p_occupy.keys())):
    S_name[i+1]=list(p_occupy.keys())[i]
    
f=open('S_index_coordinates','w') # station index and coordinate of 150 trucks
f.write(str(S_name))
f.close()

S_ports={}
for i in range(1,25):
    S_ports[i]={}
    for j in range(3):
        S_ports[i][j]={} # {station: {port: {vehicle: [arrival time, charging time, waiting time]}}}


# 2. Compute the arrival time, charging time, waiting time of each vehicle at a certain port of a charging station
for i in station_queue.keys():
    S_index=[k for k, v in S_name.items() if v==i][0] # Station index 
    # Match vehicles to ports at each charing station
    for v in station_queue[i].keys():
        t_arr=station_queue[i][v][0]
        t_charge=S_on[i][v][0] # in minutes
        t_wait=S_on[i][v][1]
        port=S_on[i][v][-1]
        S_ports[S_index][port][v]=[t_arr,t_charge,t_wait]
        
c_w_ports={}
for i in S_ports.keys():
    c_w_ports[i]={}
    for p in S_ports[i].keys():
        if S_ports[i][p]!={}:
            t_c=[0]
            t_w=[0]
            v_n=[]
            for v in S_ports[i][p].keys():
                t_c.append(S_ports[i][p][v][1])
                t_w.append(S_ports[i][p][v][2])
                if S_ports[i][p][v][2]!=0:
                    v_n.append(v)
            c_w_ports[i][p]=[round(sum(t_c),3),round(sum(t_w),3),v_n]
        else:
            c_w_ports[i][p]=[0,0,[]]
            
c_w_station={}
for i in c_w_ports.keys():
    t_c=[]
    t_w=[]
    n_v=[]
    for p in c_w_ports[i].keys():
        t_c.append(c_w_ports[i][p][0])
        t_w.append(c_w_ports[i][p][1])
        if c_w_ports[i][p][2]!=[]:
            n_v.append(len(c_w_ports[i][p][2]))
    if n_v==[]:
        c_w_station[i]=[round(sum(t_c),3),round(sum(t_w),3),0]
    else:
        c_w_station[i]=[round(sum(t_c),3),round(sum(t_w),3),sum(n_v)] # total charing and waiting time of trucks at each station
    

# save data
f=open('Online_charing_waiting_time_2023','w') 
f.write(str(c_w_station))
f.close()

#------------------------------------------------------
# Handling the data of offline charging strategy 

S_off_150={}# the charging solution of 150 trucks
for i in S_off.keys():
    t_c=S_off[i]['t_c']
    t_w=S_off[i]['t_w']
    if sum(t_c)!=0:
        t_charge=[]
        t_wait=[]
        s_index=[]
        for s in range(len(t_c)):
            if t_c[s]!=0:
                t_charge.append(t_c[s])
                t_wait.append(t_w[s])
                s_index.append(s+1)
        S_off_150[i]=[s_index,t_charge,t_wait]


S_off_v={}
for i in S_off_150.keys():
    if len(S_off_150[i][0])==1:
        S_off_v[i]=[S_off_150[i][0][0],round(S_off_150[i][1][0],4),round(S_off_150[i][2][0],4)]
    if len(S_off_150[i][0])==2:
        S_off_v[i]=S_off_150[i]
        
# change the station index into the coordinate
S_off_v_new={}
for i in S_off_v.keys():
    if type(S_off_v[i][0]) is not list:
        s_index=S_off_v[i][0]
        for k in station_v_index.keys():
            for v in station_v_index[k].keys():
                if v==i:
                    if station_v_index[k][v]==s_index:
                        s_coor=k
        S_off_v_new[i]=[s_coor,S_off_v[i][1],S_off_v[i][2]]
    else:
        s_set=S_off_v[i][0]
        S_off_v_new[i]={}
        for j in range(len(s_set)):
            s_index=s_set[j]
            for k in station_v_index.keys():
                for v in station_v_index[k].keys():
                    if v==i:
                        if station_v_index[k][v]==s_index:
                            s_coor=k
            S_off_v_new[i][s_index]=[s_coor, round(S_off_v[i][1][j],4),round(S_off_v[i][2][j],4)]

# 1. Map coordinates to stations
S_name={}
for i in range(len(p_occupy.keys())):
    S_name[i+1]=list(p_occupy.keys())[i] # the index matches the coordinate


# Key(station coordinate)：{vehicle:[charging time, waiting time],vehicle2:[charging time, waiting time]}
Station_v={}
for i in S_name.values():
    Station_v[i]={}
    
for v in S_off_v_new.keys():
    if type(S_off_v_new[v]) is list:
        hub=S_off_v_new[v][0]
        Station_v[hub][v]=[S_off_v_new[v][1],S_off_v_new[v][2]]
    if type(S_off_v_new[v]) is dict:
        for index in S_off_v_new[v].keys():
            hub=S_off_v_new[v][index][0]
            Station_v[hub][v]=[S_off_v_new[v][index][1],S_off_v_new[v][index][2]]
            
c_w_station_off={}
for s in Station_v.keys():
    s_new=[k for k,v in S_name.items() if s==v][0]
    c_w_station_off[s_new]={}
    if Station_v[s]!={}:
        t_c=[]
        t_w=[]
        n_v=[]
        for v in Station_v[s].keys():
            t_c.append(Station_v[s][v][0])
            t_w.append(Station_v[s][v][1])
            if Station_v[s][v][1]!=0:
                n_v.append(v)
    c_w_station_off[s_new]=[round(sum(t_c),3),round(sum(t_w),3),len(n_v)]

# save data
f=open('Offline_charing_waiting_time_2023','w') 
f.write(str(c_w_station_off))
f.close()