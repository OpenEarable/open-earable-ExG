import matplotlib.pyplot as plt
import pandas as pd

def plot_recorded_data(filename, sampling_rate, drop_start_seconds=0, drop_end_seconds=0, y_min_uV=-100, y_max_uV=100, inamp_gain=50, draw='filtered'):
    data = pd.read_csv(filename)

    drop_start_samples = int(drop_start_seconds * sampling_rate)
    drop_end_samples = int(drop_end_seconds * sampling_rate)

    if drop_end_samples == 0:
        data = data.iloc[drop_start_samples:]
    else:
        data = data.iloc[drop_start_samples:-drop_end_samples]

    # elapsed time in seconds for each data point
    total_samples = len(data)
    time = [i / sampling_rate for i in range(total_samples)]
    time = [i + drop_start_seconds for i in time]

    values = []
    if draw == 'filtered':
        values = data['filtered_data']
    elif draw == 'raw':
        values = data['raw_data']

    #values = [(v / inamp_gain) * 1e6 for v in values]

    fig, ax = plt.subplots()
    ax.plot(time, values)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Voltage (µV)')
    ax.set_title('Biopontential Data from OpenEarable EEG')
    ax.set_ylim(y_min_uV, y_max_uV)
    ax.legend()

    # Determine x-axis tick positions
    max_time = int(time[-1])
    step = max_time // 4
    x_ticks = list(range(drop_start_seconds, max_time + drop_start_seconds, step))

    # Update the x-axis ticks and labels
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f"{t:.0f}" for t in x_ticks], ha='right')

    plt.tight_layout()
    plt.show()

folder = 'path/to/folder'
filename = 'filename.csv'
plot_recorded_data(folder + filename, sampling_rate=256, drop_start_seconds=2, drop_end_seconds=10, y_min_uV=-100, y_max_uV=100, draw='filtered')
