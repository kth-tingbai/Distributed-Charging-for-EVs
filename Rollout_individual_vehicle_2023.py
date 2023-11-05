# -*- coding: utf-8 -*-
"""
Created on Sun Nov 5 2023

Functions used to compute the optimal or rollout-based charging strategy

"""

import numpy as np
import cvxpy as cp


# Parameters related to the road model
class road_charge:
    def __init__(self, tau, detour, Pcharging):
        self.tau = tau              
        self.detour = detour        
        self.Pcharging = Pcharging  

        
# Parameters related to the regulations and market
class regulation_market:
    def __init__(self, Tbard, DeltaT, price, overdue):
        self.Tbard = Tbard    # Maximum total travel time per day, $\bar{T}_d$
        self.DeltaT = DeltaT  # Maximum deviation time related to the deadline, $\Delta_T$
        self.price = price    # Electricity price, $\xi_k$ constant for all $k$
        self.overdue = overdue# Overdue cost
     
# 3. EV_charging

# Comment: 'self' in '__init__()' and other functions defined in a class refer to the same instance of the class
class EV_charge:
    
    def __init__(self, Pmax, eusable, eini, Pbar, tp):
        self.Pmax = Pmax      # Maximum charging power of the truck, $P_{\max}$
        self.eusable = eusable# Usable energy of the truck with fully charged battery, $e_f-e_s$
        self.e0 = eini        # Initial energy of the truck, $e_{ini}$
        self.Pbar = Pbar      # Energy consumption per unit time, $\bar{P}$
        self.tp = tp          # Charging preparation time, $p_k$ constant for all $k$
        
    #-----------------------------------------------------------------------------
    # Specify the charging problem given the parameters of the truck, road, and related reguations
    def charge_problem(self,road_charge):
        self.N = road_charge.detour.size
        self.b_charging = np.zeros(self.N)                   
        self.b_resting = np.zeros(self.N)           
        
        self.b_overdue = 0
        # The last element is one since the destination has reached.
        self.esafe = np.append(self.Pbar*road_charge.detour.copy(),[0.]) #e_s
        # Vector, elements are $\min{P_k,P_{\max}}$
        self.Pactual = np.minimum(road_charge.Pcharging, self.Pmax)  
    #------------------------------------------------------------------------------
    # Timid base policy, setting $b_k=\tilde{b}_k=1$ for all stations
    def timid_policy(self):
        self.timid_charging = np.ones(self.N)
        self.timid_overdue = 1

    #------------------------------------------------------------------------------
    # Greedy base policy, setting $b_k=\tilde{b}_k=1$ if the truck cannot reach station $k+1$
    def greedy_policy(self,road_charge):
        b = np.zeros(self.N)
        e_current = self.e0
        tau = road_charge.tau
        detour = road_charge.detour

        for i in range(self.N):
            if (e_current-self.Pbar*(tau[i]+tau[i+1]))<self.esafe[i+1]:
                b[i]=1
                e_current = self.eusable-detour[i]*self.Pbar
            else:
                e_current -=self.Pbar*tau[i]
  
        self.greedy_charging = b.copy()
        self.greedy_overdue = 1
        
    #------------------------------------------------------------------------------
    # Computing lower bound
    def lower_bound(self, road_charge, regulation_market):
        N = self.N
        tau = road_charge.tau.copy()
        detour = road_charge.detour.copy()

        Pactual = self.Pactual
        efull = self.eusable
        esafe = self.esafe.copy()
        e0 = self.e0
        Pbar = self.Pbar
        tp = self.tp
        #Tr = regulation_market.Tr
        #Td = regulation_market.Td
        Tbard = regulation_market.Tbard
        DeltaT = regulation_market.DeltaT
        Tbound = 1000000
        price = regulation_market.price
        overdue = regulation_market.overdue
        

        
        # This is the case where the total travel time constraint is fulfilled
        t_charging = cp.Variable((N))                 
        e_battery = cp.Variable((N+1))                
        delta_T = cp.Variable((N+1))

        b_charging = cp.Variable((N))
        Delta_ehat = cp.Variable((N))
        
        b_overdue = cp.Variable()
        t_overdue = cp.Variable()

        cost = 0
        constr = []
        constr += [e_battery[0] == e0-Pbar*tau[0]]
        constr += [delta_T[0] == 0]
        for i in range(N):
            constr += [b_charging[i]<=1,b_charging[i]>=0]
            constr += [Delta_ehat[i]<=b_charging[i]*Tbound,Delta_ehat[i]>=0]
            constr += [t_charging[i]*Pactual[i]-Delta_ehat[i]<=(1-b_charging[i])*Tbound]
            constr += [t_charging[i]*Pactual[i]-Delta_ehat[i]>=0]
            constr += [e_battery[i] >= esafe[i]]
            constr += [t_charging[i] <= (efull-(e_battery[i]-Pbar*tau[i]))/Pactual[i]]
          
            
            constr += [e_battery[i+1] == e_battery[i]+Delta_ehat[i]-2*b_charging[i]*Pbar*detour[i]-Pbar*tau[i+1]]
            
            constr += [t_charging[i] >= 0]
            constr += [t_charging[i] <= b_charging[i]*Tbound]
            constr += [delta_T[i+1]==delta_T[i]+Delta_ehat[i]/Pactual[i]+b_charging[i]*tp]
            cost += Delta_ehat[i]/Pactual[i]+b_charging[i]*tp+b_charging[i]*2*detour[i]+Delta_ehat[i]/Pactual[i]*price
            
        constr += [e_battery[N] >= esafe[N]]
        constr += [detour.T@b_charging <= (Tbard-tau.sum())/2]
        constr += [b_overdue >= 0, b_overdue <= 1]
        constr += [delta_T[N] >= DeltaT*b_overdue, delta_T[N] <= DeltaT*(1-b_overdue)+Tbound*b_overdue]
        constr += [t_overdue >= 0, t_overdue >= delta_T[N]-DeltaT]
        cost += t_overdue * overdue
        
        problem = cp.Problem(cp.Minimize(cost), constr)
        lower_bd = problem.solve(solver='GUROBI', reoptimize=True)
        lower_bd_t_charge = np.array(t_charging.value)
        lower_bd_b_charging = np.array(b_charging.value)
        lower_bd_b_overdue = np.array(b_overdue.value)
        return lower_bd, lower_bd_b_charging, lower_bd_t_charge, lower_bd_b_overdue
    
    #------------------------------------------------------------------------------
    def relaxed_policy(self, road_charge, regulation_market):
        self.relaxed_ld, _, charging, overdue = self.lower_bound(road_charge, regulation_market)
        charging_tem = (charging>0)
        self.relaxed_charging=charging_tem.astype(float)
        overdue_tem = (overdue>0)
        self.relaxed_overdue=overdue_tem.astype(float)

    #------------------------------------------------------------------------------
    # Compute timid, greedy, and relaxed base policies
    def base_policies(self,road_charge,regulation_market):
        self.charge_problem(road_charge)
        self.timid_policy()
        self.greedy_policy(road_charge)
        self.relaxed_policy(road_charge, regulation_market)
    
    #------------------------------------------------------------------------------    
    # Given a set of b_charging and b_resting, compute the optimal times stayed at each station
    def time_schedule(self, b_charging, b_overdue, road_charge, regulation_market):
        N = self.N
        tau = road_charge.tau.copy()
        detour = road_charge.detour.copy()

        Pactual = self.Pactual
        eusable = self.eusable
        esafe = self.esafe.copy()
        e0 = self.e0
        Pbar = self.Pbar
        tp = self.tp
        Tbard = regulation_market.Tbard
        DeltaT = regulation_market.DeltaT
        Tbound = 1000
        price = regulation_market.price
        overdue = regulation_market.overdue
        epsilon = 0.001

        if detour.dot(b_charging) <= (Tbard-tau.sum())/2:
            
            # This is the case where the total travel time constraint is fulfilled
            t_charging = cp.Variable((N))                 
            delta_e = cp.Variable((N))                    
            e_battery = cp.Variable((N+1))                

            delta_T = cp.Variable((N+1))

            cost = 0
            constr = []
            constr += [e_battery[0] == e0-Pbar*tau[0]]
            constr += [delta_T[0] == 0]
            for i in range(N):
                constr += [e_battery[i] >= esafe[i]]
                constr += [delta_e[i]+e_battery[i] <= eusable+Pbar*tau[i]]
                constr += [delta_e[i] == t_charging[i]*Pactual[i]]
                constr += [e_battery[i+1] == e_battery[i]+b_charging[i]*delta_e[i]-2*b_charging[i]*Pbar*detour[i]-Pbar*tau[i+1]]
                constr += [t_charging[i] >= 0]
                constr += [t_charging[i] <= b_charging[i]*Tbound]
                constr += [delta_T[i+1]==delta_T[i]+b_charging[i]*(t_charging[i]+tp)]
                cost += b_charging[i]*(t_charging[i]+tp+2*detour[i])+b_charging[i]*t_charging[i]*price
                
            constr += [e_battery[N] >= esafe[N]]
            if b_overdue == 0:
                constr += [delta_T[N] <= DeltaT]
            else:
                constr += [delta_T[N] >= DeltaT+epsilon]
                cost += (delta_T[N] - DeltaT)*overdue

            problem = cp.Problem(cp.Minimize(cost), constr)
            op_value = problem.solve(solver='GUROBI', reoptimize=True)
            op_t_charge = np.array(t_charging.value)
        else:
            op_value = np.inf
            op_t_charge = np.nan*np.ones(N)
            
        
        return op_value, op_t_charge 
    
    #------------------------------------------------------------------------------
    # Rollout algorithm for solving the charging problem
    def rollout(self, b_charging_ini, b_overdue_ini, road_charge, regulation_market):
        rollout = np.inf
        temp = np.inf
        b_charging = b_charging_ini.copy()
        b_overdue = b_overdue_ini
        rollout_charging = b_charging.copy()
        
        
        rollout_overdue = b_overdue
        rollout_t_charge = cp.Variable(self.N) 
     
    
        for i in reversed(range(self.N)):
            b_charging = rollout_charging.copy()
            #b_resting = rollout_resting.copy()
            
            for j in range(4):
                if j == 0:
                    b_charging[i] = 0
                    b_overdue = 0
                elif j == 1:
                    b_charging[i] = 0
                    b_overdue = 1
                elif j == 2:
                    b_charging[i] = 1
                    b_overdue = 0
                else:
                    b_charging[i] = 1
                    b_overdue = 1
                temp, op_t_charge = self.time_schedule(b_charging, b_overdue, road_charge, regulation_market)
                if temp is not None:
                    if rollout > temp:
                        rollout_charging = b_charging.copy()
                        rollout_overdue = b_overdue
                        rollout = temp
                        rollout_t_charge = op_t_charge
                        
                
    
        return rollout, rollout_charging, rollout_t_charge, rollout_overdue   # rollout_overdue: whether violate the delivery deadline (1 means violation)

    #------------------------------------------------------------------------------
    # Computing optimal via linearization
    def best_linearization(self, road_charge, regulation_market):
        N = self.N
        tau = road_charge.tau.copy()
        detour = road_charge.detour.copy()

        Pactual = self.Pactual
        efull = self.eusable
        esafe = self.esafe.copy()
        e0 = self.e0
        Pbar = self.Pbar
        tp = self.tp
        Tbard = regulation_market.Tbard
        DeltaT = regulation_market.DeltaT
        Tbound = 1000000
        price = regulation_market.price
        overdue = regulation_market.overdue

        
        # This is the case where the total travel time constraint is fulfilled
        t_charging = cp.Variable((N))                
        e_battery = cp.Variable((N+1))                

        delta_T = cp.Variable((N+1))

        b_charging = cp.Variable(N, boolean=True)
        Delta_ehat = cp.Variable((N))

        
        b_overdue = cp.Variable(N, boolean=True)
        t_overdue = cp.Variable()

        cost = 0
        constr = []
        constr += [e_battery[0] == e0-Pbar*tau[0]]
        constr += [delta_T[0] == 0]
        for i in range(N):
            
            constr += [Delta_ehat[i]<=b_charging[i]*Tbound,Delta_ehat[i]>=0]
            constr += [t_charging[i]*Pactual[i]-Delta_ehat[i]<=(1-b_charging[i])*Tbound]
            constr += [t_charging[i]*Pactual[i]-Delta_ehat[i]>=0]
            constr += [e_battery[i] >= esafe[i]]
            constr += [t_charging[i] <= (efull-(e_battery[i]-Pbar*tau[i]))/Pactual[i]]
            
    
            constr += [e_battery[i+1] == e_battery[i]+Delta_ehat[i]-2*b_charging[i]*Pbar*detour[i]-Pbar*tau[i+1]]
            constr += [t_charging[i] >= 0]
            constr += [t_charging[i] <= b_charging[i]*Tbound]
            constr += [delta_T[i+1]==delta_T[i]+Delta_ehat[i]/Pactual[i]+b_charging[i]*tp]
            cost += Delta_ehat[i]/Pactual[i]+b_charging[i]*tp+b_charging[i]*2*detour[i]+Delta_ehat[i]/Pactual[i]*price
            
        
        constr += [e_battery[N] >= esafe[N]]
        constr += [detour.T@b_charging <= (Tbard-tau.sum())/2]
        constr += [delta_T[N] >= DeltaT*b_overdue, delta_T[N] <= DeltaT*(1-b_overdue)+Tbound*b_overdue]
        constr += [t_overdue >= 0, t_overdue >= delta_T[N]-DeltaT]
        cost += t_overdue * overdue
        
        problem = cp.Problem(cp.Minimize(cost), constr)
        op_value = problem.solve(solver='GUROBI', reoptimize=True)
        op_t_charge = np.array(t_charging.value)
        op_b_charging = np.array(b_charging.value)
        op_b_overdue = np.array(b_overdue.value)
        return op_value, op_b_charging,  op_t_charge, op_b_overdue
        

