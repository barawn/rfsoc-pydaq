import matplotlib.pyplot as plt
import csv
import numpy as np

data = []

#with open('/home/xilinx/rfsoc-pydaq-copy/data/scale_change.csv', mode='r') as file:
#	csv_reader = csv.reader(file)
#	print("something for the love of God")
#	for row in csv_reader:
#		print(i)
#		data.append(float(row[0]))

dataa = np.loadtxt('/home/xilinx/data/pid_loop_scale1.csv', delimiter=',')
datab =  np.loadtxt('/home/xilinx/data/pid_loop_scale.csv', delimiter=',')
data1 = dataa[:,0]
data2 = dataa[:,1]
data3 = datab[:,0]
data4 = datab[:,1]

fig, axs = plt.subplots(2,2)
axs[0,0].plot(data1,label="Error")
axs[0,1].plot(data2, label = "Control Value" )

axs[1,0].plot(data3,label="Error")
axs[1,1].plot(data4,label="Control Value")

for ax in axs.flat:
    ax.set(xlabel = "Value", ylabel = 'Value') 
plt.legend()
plt.show()
