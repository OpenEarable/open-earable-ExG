import serial
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import digitalfilter
from datetime import datetime
from struct import unpack
import sys

#ser = serial.Serial("/dev/cu.usbmodem2101", 115200)
ser = serial.Serial("/dev/cu.usbserial-020766C8", 115200)
ser.timeout = 0  # non-blocking read

# Configure parameters for plotting
dataList = []
newDataBuffer = []
max_datapoints_to_display = 1500
#max_datapoints_to_display = 100
#min_buffer_uV = 150
min_buffer_uV = 10500
inamp_gain = 50
#filters = digitalfilter.get_Biopotential_filter(order=4, cutoff=[1, 30], btype="bandpass", fs=320, output = "sos")
filters = digitalfilter.get_Biopotential_filter(order=4, cutoff=[1, 30], btype="bandpass", fs=256, output = "sos", notch=True)
#filters = digitalfilter.get_Highpass_filter(order=4, cutoff=0.5, fs=256, output="sos")
enable_filters = True
write_to_file = False
autoscale = False

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"OpenEarableEEG_Serial_{current_time}.csv"

if write_to_file:
    recording_file = open("./recordings/" + filename, 'w')
    recording_file.write("time,raw_data,filtered_data\n")

fig, ax = plt.subplots()
line, = ax.plot([], [])

running = True

def read_from_serial():
    global newDataBuffer
    buffer = bytearray()

    while running:
        byte = ser.read(1)
        if byte:
            if byte == b'\n':
                if len(buffer) == 4:
                    value = unpack('<f', buffer)
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")
                    float_value = value[0]
                    #print(float_value)

                    filtered_data = filters(float_value)

                    # Convert to µV
                    filtered_data = (filtered_data / inamp_gain) * 1e6  
                    raw_data = (float_value / inamp_gain) * 1e6

                    if enable_filters:
                        newDataBuffer.append(filtered_data)
                    else:
                        newDataBuffer.append(raw_data)

                    if write_to_file:
                        recording_file.write(f"{timestamp},{raw_data},{filtered_data}\n")

                buffer.clear()
            else:
                buffer.append(byte[0])

threading.Thread(target=read_from_serial, daemon=True).start()


def init():
    line.set_data([], [])
    ax.set_xlim(0, max_datapoints_to_display)
    ax.set_title("Biopontential Data from OpenEarable EEG")
    ax.set_ylabel("Voltage (µV)")
    ax.set_xlabel("Samples")
    return line,

def animate(frame):
    global dataList, newDataBuffer

    dataList.extend(newDataBuffer)
    newDataBuffer = []

    dataList = dataList[-max_datapoints_to_display:]  # Keep only the latest data points
    line.set_data(range(1, len(dataList) + 1), dataList)

    if dataList:
        min_val = min(dataList)
        max_val = max(dataList)
        buffer = 0.1 * (max_val - min_val) if max_val - min_val > min_buffer_uV else min_buffer_uV
        if autoscale:
            ax.set_ylim(min_val - buffer, max_val + buffer)
        else:
            ax.set_ylim(-min_buffer_uV, min_buffer_uV)

    return line,

def close_event(event):
    global running
    running = False
    ser.close()
    if write_to_file:
        recording_file.close()
    plt.close('all')
    sys.exit(0)

fig.canvas.mpl_connect('close_event', close_event)

ani = animation.FuncAnimation(fig, animate, init_func=init, interval=5, save_count=max_datapoints_to_display)
plt.show()
