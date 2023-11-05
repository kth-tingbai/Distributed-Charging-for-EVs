# -*- coding: utf-8 -*-
"""
Created on Sun Nov 5 20:51:05 2023

Data handling: compute the bar length of the Gantt Chart to show the charging time scheduling of trucks at each port at each station.

"""
#f=open('Stations_map_trucks_150','r')
#a=f.read()
#station_v_index=eval(a) # the marix showing the truck index and the corresponding station index in the route of the truck
#f.close() 

#f=open('Dynamics_offline_150','r') # dynamics, offline
#a=f.read()
##D_off=eval(a) 
#f.close()

#f=open('Solution_offline_150','r')  # solution, offline
#a=f.read()
#S_off=eval(a)
#f.close()

#f=open('Waiting_time_offline_150','r') # waiting time, offline
#a=f.read()
#w_t_off=eval(a)
#f.close()

#f=open('Dynamics_online_150','r') # dynamics, online
#a=f.read()
#D_on=eval(a)
#f.close()

f=open('Solution_online_150trucks','r') # solution, online
a=f.read()
S_on=eval(a)
f.close()

#f=open('Waiting_time_online_150','r') # waiting time, online
#a=f.read()
#w_t_on=eval(a)
#f.close()

f=open('Arrival_time_online_150trucks','r')
a=f.read()
station_queue=eval(a)
f.close()

f=open('P_occupy_online_150trucks','r')
a=f.read()
p_occupy=eval(a)
f.close()

#----------------------------------------
from dateutil.parser import parse
from datetime import timedelta

# 1. Map coordinates to stations
S_name={}
for i in range(len(p_occupy.keys())):
    S_name[i+1]=list(p_occupy.keys())[i]
    
    
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
        
# 3. For each port
# 3.1 Compute the earliest arrival time
Port_t_start={}
for s in S_ports.keys():
    Port_t_start[s]={}
    for p in S_ports[s].keys():
        if S_ports[s][p]!={}:
            t=[]
            for v in S_ports[s][p].keys():
                t.append(S_ports[s][p][v][0])
            t_start=min(t)
            Port_t_start[s][p]=t_start
        else:
            Port_t_start[s][p]={}
            
Port_t_start_new={}
remove='2023-07-01'
for s in Port_t_start.keys():
    Port_t_start_new[s]={}
    for p in Port_t_start[s].keys():
        if Port_t_start[s][p]!={}:
            t_new=Port_t_start[s][p].replace(remove,'').strip()
            Port_t_start_new[s][p]=t_new
        else:
            Port_t_start_new[s][p]={}


# Get the list
end_t='20:00:00.0000'
start_times_charging=[]
for s in Port_t_start_new.keys():
    for p in Port_t_start_new[s].keys():
        if Port_t_start_new[s][p]!={}:
            start_times_charging.append(Port_t_start_new[s][p])
        else:
            start_times_charging.append(end_t) # will be used 

# 3.2 Compute the charging time of each vehicle at a port, in hours
# determine the lenght of each bar at a port and the color of the bar
Bar_len={}
Col_bar={} # color of the bar
for i in S_ports.keys():
    Bar_len[i]={}
    Col_bar[i]={}
    for p in S_ports[i].keys():
        if S_ports[i][p]!={}:
            Bar_len[i][p]={}
            Col_bar[i][p]={}
            # compute the length of each bar of each vehicle at each port
            t_end=[Port_t_start[i][p]] #'2023-07-01 08:27:05.8600'
            for v in range(len(S_ports[i][p].keys())):
                v_i=list(S_ports[i][p].keys())[v]
                # the first bar at a port
                if v==0:
                    t_a=S_ports[i][p][v_i][0] 
                    l_1=round(S_ports[i][p][v_i][1]/60,4) # charging time in hours
                    Bar_len[i][p][v_i]=[l_1]
                    Col_bar[i][p][v_i]=['g']
                    t_e=(parse(t_a)+timedelta(seconds=l_1*3600)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    t_end.append(t_e)
                    
                # not the first bar at a port
                if v!=0:
                    t_a=S_ports[i][p][v_i][0] # arrival time at the charging station
                    t_w=round(S_ports[i][p][v_i][-1]/60,4) # waiting time in hours
                    t_c=round(S_ports[i][p][v_i][1]/60,4) # charging time in hours
                    
                    
                    if t_w==0: # no red bar
                        t_diff=(parse(t_a)-parse(t_end[-1])).total_seconds() # in seconds
                        if (t_diff>60): # there is white bar
                            l_2=round(t_diff/3600,4) # length of the white bar
                            Bar_len[i][p][v_i]=[l_2, t_c]
                            Col_bar[i][p][v_i]=['w','g']
                            t_e=(parse(t_a)+timedelta(seconds=t_c*3600)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                            t_end.append(t_e)
                    
                    else: 
                        # case1: waiting time is shorter than the previous charging time, i.e., divide the previous charging time into charging and waiting time
                        # there is a red bar, i.e., revise the bar length of the previous vehicle
                        v_i_pre=list(S_ports[i][p].keys())[v-1]
                        bar_pre=Bar_len[i][p][v_i_pre]
                        # update the bar length of the current vehicle
                        Bar_len[i][p][v_i]=[t_c]
                        Col_bar[i][p][v_i]=['g']
                        # update the departure time of the current vehicle 
                        t_e=(parse(t_a)+timedelta(seconds=(t_c+t_w)*3600)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                        t_end.append(t_e)
                        
                        # the length of the red bar
                        if t_w<bar_pre[-1]:
                            
                            # divide the previous green bar into two bars: a green bar and a red bar
                            t_c_pre_new=round(bar_pre[-1]-t_w,4) # the new charing time bar
                            if len(bar_pre)==1: # one green bar
                                Bar_len[i][p][v_i_pre]=[t_c_pre_new, t_w]
                                Col_bar[i][p][v_i_pre]=['g','r']
                            else: # one white bar and one green bar
                                Bar_len[i][p][v_i_pre]=[bar_pre[0], t_c_pre_new, t_w]
                                Col_bar[i][p][v_i_pre]=['w','g','r']
                                
                        else:
                            # Note that: the current code can only handle the case where at most two trucks waiting while one truck is charging. If more complicated cases exist, more codes need to compute the bar lengths and colors.
                            # case2: waiting time is longer than the previous charging time, i.e., the waiting time of current vehicle is overlapping with the waiting time of the previous vehicle
                            # divide the pre-prevariou red bar into a red and a purple bar, and change the previous green bar into a red bar
                            v_i_pre_pre=list(S_ports[i][p].keys())[v-2]
                            bar_pre_pre=Bar_len[i][p][v_i_pre_pre]
                            t_a_pre=S_ports[i][p][v_i_pre][0]
                            # the purple bar
                            l_r=bar_pre_pre[-1] # red bar
                            l_r_new=round((parse(t_a)-parse(t_a_pre)).total_seconds()/3600,4) # new red bar
                            l_p_new=round(l_r-l_r_new,4) # new purple bar
                            
                            if len(bar_pre_pre)==2: # one green bar and one red bar
                                Bar_len[i][p][v_i_pre_pre]=[bar_pre_pre[0], l_r_new, l_p_new] # one green bar, one red bar, one purple
                                Col_bar[i][p][v_i_pre_pre]=['g','r','p']
                            else: # one white bar, one green bar, and one red bar
                                Bar_len[i][p][v_i_pre_pre]=[bar_pre_pre[0:1], l_r_new, l_p_new] # one green bar, one red bar, one purple
                                Col_bar[i][p][v_i_pre_pre]=['w','g','r','p']
                            
                            # change the previous green bar into red bar
                            Col_bar[i][p][v_i_pre]=['r']
                                
                            

# 3.3 Get the list of bar length for each port
L_bar_port={} # bar length
C_bar_port={} # bar color
for i in Port_t_start.keys():
    L_bar_port[i]={}
    C_bar_port[i]={}
    for p in Port_t_start[i].keys():
        if Port_t_start[i][p]!={}:
            L_bar_port[i][p]={}
            C_bar_port[i][p]={}
            L_bar=[]
            C_bar=[]
            for v in Bar_len[i][p].keys():
                L_bar.append(Bar_len[i][p][v])
                C_bar.append(Col_bar[i][p][v])
            L_bar_port[i][p]=L_bar
            C_bar_port[i][p]=C_bar
        else:
            L_bar_port[i][p]=[[0]]
            C_bar_port[i][p]=[['w']]
            
# Combine the bars at each port, and their colors
L_bar_combine={}
C_bar_combine={}
for i in L_bar_port.keys():
    L_bar_combine[i]={}
    C_bar_combine[i]={}
    for p in L_bar_port[i].keys():
        L_bar_combine[i][p]={}
        C_bar_combine[i][p]={}
        bar_list=[]
        col_list=[]
        for v in L_bar_port[i][p]:
            for b in v:
                bar_list.append(b)
        for v in C_bar_port[i][p]:
            for c in v:
                col_list.append(c)
        
        L_bar_combine[i][p]=bar_list
        C_bar_combine[i][p]=col_list
                

# For each bar, expand a white bar at the end
L_bar_all={}
C_bar_all={}
for i in L_bar_combine.keys():
    L_bar_all[i]={}
    C_bar_all[i]={}
    for p in L_bar_combine[i].keys():
        L_bar_all[i][p]=L_bar_combine[i][p]
        C_bar_all[i][p]=C_bar_combine[i][p]
        if L_bar_combine[i][p][0]!=0:
            L_bar_all[i][p].append(1)
            C_bar_all[i][p].append('w')
            

            
# 3.4 Get the final bar list and color list

# red: (1, 0.1, 0, 0.8), green: (0.6, 0.98, 0.6, 1), white: (1, 1, 1, 1), purple: (0.6, 0.2, 1, 0.7)
# pink: (1.000, 0.753, 0.796, 1), palegreen: (0.596, 0.984, 0.596, 1)
C_bar_all_new={}
for i in C_bar_all.keys():
    C_bar_all_new[i]={}
    for p in C_bar_all[i].keys():
        C_bar_all_new[i][p]=[]
        for j in C_bar_all[i][p]:
            if j=='g':
                C_bar_all_new[i][p].append((0.6, 0.98, 0.6, 1))
            if j=='w':
                C_bar_all_new[i][p].append((1, 1, 1, 1))
            if j=='r':
                C_bar_all_new[i][p].append((1, 0.1, 0, 0.8))
            if j=='p':
                C_bar_all_new[i][p].append((0.6, 0.2, 1, 0.7))
                
            
f=open('Length_bar_2023','w') 
f.write(str(L_bar_all))
f.close()

f=open('Color_bar_2023','w') 
f.write(str(C_bar_all_new))
f.close()

f=open('Start_time_2023','w') 
f.write(str(Port_t_start_new))
f.close()
        
