import threading
import time
from brainflow.data_filter import DataFilter
from scipy import signal
import numpy as np


from signal_processing import save, get_data_from_file

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import matplotlib.pyplot as plt

def save_REST(board_shim,total_duration,access_route='DATA.csv'):
    data=board_shim.get_board_data()
    time.sleep(total_duration)
    save(board_shim,access_route,mode='w')


def REST(board_shim,total_duration,n_channel,access_route='DATA.csv',sampling_rate=250):
    #save_REST(board_shim,total_duration,access_route)
    data=get_data_from_file(access_route, channel_list=[n_channel], n_start=0, n_end=None)
    print(data.shape)
    # plt.plot(np.transpose(data))
    # plt.show()
    data=np.transpose(data)
    length=len(data)
    print(length)
    fft_result = np.fft.fft(data,axis=0)
    frequencies = np.fft.fftfreq(length, 1/sampling_rate)
    # # Take the magnitude of the FFT
    magnitude = np.abs(fft_result)
    # # Filter the frequencies to the desired range (8 to 12 Hz)
    filtered_indices = np.where((frequencies >= 8) & (frequencies <= 12))[0]
    # Find the peak frequency within the filtered range
    peak_frequency = frequencies[filtered_indices][np.argmax(magnitude[filtered_indices])]
    # # Print the peak frequency
    #print(f"The peak frequency is: {peak_frequency} Hz")
    # plt.plot(frequencies,magnitude)
    # plt.xlim((0,50))
    # plt.show()
    return peak_frequency



Board = 'SYNTH'
PuertoArduino = '/dev/cu.usbmodem1101'
n_channel = 1
total_duration = 60  # duration in seconds


params = BrainFlowInputParams()
params.ip_port = 0
params.serial_port = ''
params.mac_address = ''
params.other_info = ''
params.ip_address = ''
params.ip_protocol = 0
params.timeout = 0
params.file = ''
if Board == 'CYTON':
    board_id = BoardIds.CYTON_BOARD
    params.serial_port = '/dev/cu.usbserial-DM03H6KD'
else:
    board_id = BoardIds.SYNTHETIC_BOARD
    params.serial_port = ''

streamer_params = ''
stop_flag = threading.Event()
sampling_rate=BoardShim.get_sampling_rate(board_id)

board_shim = BoardShim(board_id, params)
board_shim.prepare_session()
board_shim.start_stream(450000, streamer_params)

BoardShim.get_sampling_rate(board_id)  # Sampling rate in Hz
print('fs:',sampling_rate)
PAF=REST(board_shim,total_duration,n_channel,sampling_rate=sampling_rate)


