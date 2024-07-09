import asyncio
from bleak import BleakClient
import struct
from datetime import datetime, timedelta
import threading
import digitalfilter
import sys
import signal

import matplotlib.pyplot as plt
import matplotlib.animation as animation

BLE_ADDRESS = "F83153A9-8994-8BC6-CAD9-8C2365BAA7C9"
CHARACTERISTIC_UUID = "20a4a273-c214-4c18-b433-329f30ef7275"

# Plotting configuration
dataList = []
max_datapoints_to_display = 700
min_buffer_uV = 150
inamp_gain = 50
sample_rate = 256
filters = digitalfilter.get_Biopotential_filter(order=4, cutoff=[1, 30], btype="bandpass", fs=256, output="sos")
enable_filters = True
write_to_file = False
autoscale = False

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"OpenEarableEEG_BLE_{current_time}.csv"

if write_to_file:
    recording_file = open("./recordings/" + filename, 'w')
    recording_file.write("time,raw_data,filtered_data\n")

fig, ax = plt.subplots()
line, = ax.plot([], [])

exit_event = threading.Event()

last_valid_timestamp = None

def init():
    line.set_data([], [])
    ax.set_xlim(0, max_datapoints_to_display)
    ax.set_title("Biopontential Data from OpenEarable EEG")
    ax.set_ylabel("Voltage (µV)")
    ax.set_xlabel("Samples")
    return line,

def animate(frame):
    global dataList

    # DataList is updated in the notification handler
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

def notification_handler(sender, data):
    global dataList
    global enable_filters
    global sample_rate
    global last_valid_timestamp

    readings = struct.unpack('<5f', data)
    timestamp = datetime.now()

    if last_valid_timestamp is None:
        last_valid_timestamp = timestamp - timedelta(seconds=5 * 1/sample_rate)

    for i, float_value in enumerate(readings):
        # Calculate the correct timestamp for each reading
        if i == 4:
            timestamp_for_float_value = timestamp
        else:
            time_diff = (timestamp - last_valid_timestamp) / 5
            timestamp_for_float_value = last_valid_timestamp + (i + 1) * time_diff
        
        filtered_data = filters(float_value)

        # Convert to µV
        filtered_data = (filtered_data / inamp_gain) * 1e6  
        raw_data = (float_value / inamp_gain) * 1e6
        
        if enable_filters:
            dataList.append(filtered_data)
        else:
            dataList.append(raw_data)

        if write_to_file:
            recording_file.write(f"{timestamp_for_float_value.strftime('%H:%M:%S.%f')},{raw_data},{filtered_data}\n")

    # Update last_valid_timestamp to be the timestamp for the 5th float
    last_valid_timestamp = timestamp

def insert_datapoint():
    global dataList
    global enable_filters
    global sample_rate

    timestamp = datetime.now()
    timestamp_for_float_value = timestamp.strftime("%H:%M:%S.%f")

    filtered_data = 1000000
    raw_data = 1000000

    if enable_filters:
        dataList.append(filtered_data)
    else:
        dataList.append(raw_data)

    if write_to_file:
        recording_file.write(f"{timestamp_for_float_value},{raw_data},{filtered_data}\n")

async def run_ble_client():
    async with BleakClient(BLE_ADDRESS) as client:
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        print("Connected and receiving data...")

        while not exit_event.is_set():
            await asyncio.sleep(1)

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ble_client())

def cleanup(*args):
    exit_event.set()
    if write_to_file:
        recording_file.close()
    plt.close(fig)

def handle_close(evt):
    cleanup()
    sys.exit(0)

def handle_key_press(event):
    global cmd_pressed
    if event.key == 'g':
        insert_datapoint()

def handle_key_release(event):
    global cmd_pressed
    if event.key == 'cmd' or event.key == 'control':
        insert_datapoint()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    fig.canvas.mpl_connect('close_event', handle_close)
    fig.canvas.mpl_connect('key_press_event', handle_key_press)
    fig.canvas.mpl_connect('key_release_event', handle_key_release)
    
    threading.Thread(target=start_async_loop, daemon=True).start()

    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=5, save_count=max_datapoints_to_display)
    plt.show()
