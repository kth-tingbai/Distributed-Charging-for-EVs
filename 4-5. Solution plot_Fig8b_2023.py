# -*- coding: utf-8 -*-
"""
Created on Sun Nov  5 13:13:38 2023

Fig 8b: Show charing time scheduling at Station 22 

"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

f=open('Length_bar_22','r')
a=f.read()
L_bar_12=eval(a)
f.close()

f=open('Color_bar_22','r')
a=f.read()
C_bar_12=eval(a)
f.close()

f=open('Start_time_22','r')
a=f.read()
Port_t_start_12=eval(a)
f.close()


segment_lengths_hours=[]
segment_colors=[]
start_times=[]
for p in L_bar_12.keys():
    segment_lengths_hours.append(L_bar_12[p])
    segment_colors.append(C_bar_12[p])
    start_times.append(Port_t_start_12[p])
    
# Sample data for tasks and their start times (in HH:MM format)
tasks = ['Port 1', 'Port 2', 'Port 3']

# Create a taller figure
fig, ax = plt.subplots(figsize=(13, 6.7))

# Plot tasks using bars with different lengths and transparent colors for different segments
for i, (task, lengths, colors) in enumerate(zip(tasks, segment_lengths_hours, segment_colors), start=1):
    # Calculate y-position for bars within the same task, increasing the distance between tasks
    y_position = i * 1.5
    
    # Set initial start time for the task
    start_time = datetime.strptime(start_times[i-1], '%H:%M:%S.%f')
    
    # Plot bars with different colors for different segments
    for length, color in zip(lengths, colors):
        # Convert segment length from hours to seconds
        length_seconds = int(length * 3600)
        ax.barh(y_position, length_seconds, left=start_time, height=1, color=color)
        
        # Update start time for the next segment within the same task
        start_time += timedelta(seconds=length_seconds)


# Add gray grid lines at hourly intervals
for i in range(8, 17):  # Hours from 08:00 to 16:00
    grid_time = datetime.strptime(f'{i:02}:00', '%H:%M')
    #grid_time = datetime.strptime(f'{i:02}:00:00', '%H:%M:%S')
    ax.axvline(grid_time, color='gray', linestyle='--', linewidth=0.5)

# Set x-axis limits between 08:00:00 and 17:00:00
#start_time = datetime.strptime('08:00:00', '%H:%M:%S')
start_time = datetime.strptime('08:00', '%H:%M')
end_time = datetime.strptime('17:00', '%H:%M')
ax.set_xlim(start_time, end_time)


# Set the x-axis tick positions at one-hour intervals
tick_positions = [start_time + timedelta(hours=i) for i in range(13)]

# Format the x-axis tick labels as HH:MM:SS
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Set the major ticks and labels on the x-axis
tick_positions = [start_time + timedelta(hours=i) for i in range(int((end_time - start_time).seconds / 3600) + 1)]
ax.set_xticks(tick_positions)
ax.set_xticklabels([time.strftime('%H:%M') for time in tick_positions], rotation=0, fontsize=19)


# Set y-axis labels with task names
ax.set_yticks([i * 1.5 for i in range(1, len(tasks) + 1)])
ax.set_yticklabels(tasks)
ax.set_yticklabels([f'Port {i}' for i in range(1, len(tasks) + 1)], fontsize=19) 
ax.set_ylim(0.55, 6.2)



# Add horizontal grid lines for each port
ax.yaxis.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.7)


# Set x-axis label
ax.set_xlabel('Timeline', fontsize=20)

# Set y-axis label
#ax.set_ylabel('Charging station 11', fontsize=19)


#%%# Create a dictionary to store unique colors and their corresponding labels
# Create a dictionary to store unique colors and their corresponding captions

# red: (1, 0.1, 0, 0.8), green: (0.6, 0.98, 0.6, 1), white: (1, 1, 1, 1), purple: (0.6, 0.2, 1, 0.7)
color_captions = {
    (0.6, 0.98, 0.6, 1): 'One trcuk charging',
    (1, 0.1, 0, 0.8): 'One truck charging while one truck waiting',
    # Add more color captions as needed
}

# Plot tasks using bars with different lengths and transparent colors for different segments
for i, (task, lengths, colors) in enumerate(zip(tasks, segment_lengths_hours, segment_colors), start=1):
    # ... (your existing code for plotting bars)
    
    # Keep track of unique colors for the legend
    for length, color in zip(lengths, colors):
        # ... (your existing code for plotting bars)
        pass

# Create legend handles and modified labels based on the color_captions dictionary
legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in color_captions.keys()]
legend_labels = [color_captions[color] for color in color_captions.keys()]


# Add legend to the plot with modified labels
ax.legend(legend_handles, legend_labels, loc='upper right',fontsize=17)

plt.savefig('Fig8b.pdf', bbox_inches='tight') 
#plt.savefig('Fig8b.png', format="PNG", dpi=1000) 

# Show the Gantt chart
plt.show()
