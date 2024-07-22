import threading
import time
from brainflow.data_filter import DataFilter
from scipy import signal
import numpy as np

def PasaBanda(Fr=10,Fs=250): #devuelve a y b de 5 coef c/u
    b, a = signal.iirfilter(2, [(Fr-1),(Fr+1)], btype='band', analog=False, ftype='butter',fs=Fs)
    return b, a

def led_toggle_ON(puerto_serie,delay_time):
    # Adjust the delay time as needed (in seconds)
    time.sleep(delay_time)
    puerto_serie.write(b'1')

def led_toggle_OFF(puerto_serie,delay_time):
    time.sleep(delay_time) 
    puerto_serie.write(b'0')

def toggle_led(serial_port, led_state, delay):
    if led_state[0]:
        led_toggle_OFF(serial_port, delay)
        led_state[0] = False
    else:
        led_toggle_ON(serial_port, delay)
        led_state[0] = True




def phase_detection(board_shim, stop_flag, b, a, serial_port, n_channel=0, delay=0,marker=0):
    anterior=-1
    y=[0,0,0,0,0]
    x=[0,0,0,0,0]
    led_state = [False]  # Use a list to make it mutable within the nested function
    data=board_shim.get_board_data()
    board_shim.insert_marker(marker)
    while not stop_flag.is_set():
        data = board_shim.get_current_board_data(1) # cant de canales x cant de muestras ej: data.shape=(32,1) al hacer get_current_board(data)(5) con placa Synth
        if data.size > 0:
            if data[0][0] != anterior and len(data[0])!=0:
                if data[0][0] != anterior+1 and data[0][0]!=0:
                    # print('OJO, salteó muestras')
                    # print(anterior,data[0][0])
                anterior=data[0][0]
                x.append(data[n_channel][-1])
                x=x[1:]
                yn=b[0]*x[-1]+b[1]*x[-2]+b[2]*x[-3]+b[3]*x[-4]+b[4]*x[-5]-a[1]*y[-1]-a[2]*y[-2]-a[3]*y[-3]-a[4]*y[-4]
                y.append(yn)
                y=y[1:]
                if y[-1]*y[-2]<0:
                    #print('Zero crossing detected')
                    threading.Thread(target=toggle_led, args=(serial_port, led_state, delay)).start()

                


def save(board_shim,access_route='DATA.csv',mode='a'):
    data = board_shim.get_board_data()
    DataFilter.write_file(data, access_route, mode)  # use 'a' for append mode, or w
    print("Data saved")



def get_data_from_file(access_route='DATA.csv', channel_list=None, n_start=0, n_end=None):  
    """
    Reads data from a file and returns the selected portion.

    Parameters:
    access_route (str): Path to the data file.
    channel_list (list): List of channel indices to select.
    n_start (int): Starting index for data slicing.
    n_end (int or None): Ending index for data slicing. If None, selects till the end.

    Returns:
    numpy.ndarray: Selected data.
    """
    try:
        # Read the data file
        data = DataFilter.read_file(access_route)
        
        # Handle slicing with n_end=None correctly
        data_slice = data[:, n_start:n_end] if n_end is not None else data[:, n_start:]
        
        # If channel_list is provided, select specified channels
        if channel_list is not None:
            data_slice = data_slice[channel_list]
            
        return data_slice
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None




def stop_program_after_interval(interval, stop_flag):
    time.sleep(interval)
    stop_flag.set()


def Stimulation_Sequence(board_shim,serial_port, n_channel,delay_list,interval_duration,stop_flag,access_route='DATA_estim.csv',PAF=10):
    PAF=10
    sampling_rate=250
    b, a = PasaBanda(PAF,sampling_rate)
    # Start the for loop and delay threads in the main thread
    for index, delay in enumerate(delay_list):
        print('index', index,'delay',delay)
        delay=delay/1000
        stop_flag.clear()

        # Ensure the marker value is not zero
        marker_value = index + 1

        phase_thread = threading.Thread(target=phase_detection, args=(board_shim, stop_flag, b, a, serial_port, n_channel, delay, marker_value))
        phase_thread.start()

        timer_thread = threading.Thread(target=stop_program_after_interval, args=(interval_duration, stop_flag))
        timer_thread.start()
        # Start the Graph in the main thread after the loop
        
        # Wait for the timer thread to finish before starting the next interval
        timer_thread.join()
        
        save(board_shim,access_route,'a')


def save_REST(board_shim,total_duration,access_route='DATA.csv'):
    data=board_shim.get_board_data()
    time.sleep(total_duration)
    save(board_shim,access_route,mode='w')


def REST(board_shim,total_duration=60,n_channel=4,access_route='DATA.csv',sampling_rate=250):
    save_REST(board_shim,total_duration,access_route)
    data=get_data_from_file(access_route, channel_list=[n_channel], n_start=0, n_end=None)
    data=np.transpose(data)
    length=len(data)
    fft_result = np.fft.fft(data,axis=0)
    frequencies = np.fft.fftfreq(length, 1/sampling_rate)
    # # Take the magnitude of the FFT
    magnitude = np.abs(fft_result)
    # # Filter the frequencies to the desired range (8 to 12 Hz)
    filtered_indices = np.where((frequencies >= 8) & (frequencies <= 12))[0]
    # Find the peak frequency within the filtered range
    peak_frequency = frequencies[filtered_indices][np.argmax(magnitude[filtered_indices])]
    return peak_frequency

def get_data_from_file(access_route='DATA.csv', channel_list=None, n_start=0, n_end=None):  
    """
    Reads data from a file and returns the selected portion.

    Parameters:
    access_route (str): Path to the data file.
    channel_list (list): List of channel indices to select.
    n_start (int): Starting index for data slicing.
    n_end (int or None): Ending index for data slicing. If None, selects till the end.

    Returns:
    numpy.ndarray: Selected data.
    """
    try:
        # Read the data file
        data = DataFilter.read_file(access_route)
        
        # Handle slicing with n_end=None correctly
        data_slice = data[:, n_start:n_end] if n_end is not None else data[:, n_start:]
        
        # If channel_list is provided, select specified channels
        if channel_list is not None:
            data_slice = data_slice[channel_list]
            
        return data_slice
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    




def splice_signal(signal_markers):
    """
    Splits the signal into segments based on non-zero markers.
    
    Parameters:
    signal_markers (numpy.ndarray): A 2D numpy array where the first row is the signal
                                    and the second row contains markers.
                                    
    Returns:
    list: A list of numpy arrays, each representing a segment of the signal.
    """
    signal = signal_markers[0]
    markers = signal_markers[1]
    
    # Find indices of non-zero markers
    marker_indices = np.where(markers != 0)[0]
    
    segments = []
    
    # If there are no markers, return the whole signal as a single segment
    if len(marker_indices) == 0:
        return [signal]
    
    # Extract segments based on marker indices
    for i in range(len(marker_indices) - 1):
        start_idx = marker_indices[i]
        end_idx = marker_indices[i + 1]
        segments.append(signal[start_idx:end_idx].reshape(1, -1))
    
    # Add the last segment from the last marker to the end of the signal
    last_start_idx = marker_indices[-1]
    segments.append(signal[last_start_idx:].reshape(1, -1))
    
    return segments


def AlphaPowerFromFile(n_channel,sampling_rate,access_route='DATA.csv'):
    channel_data=(get_data_from_file(access_route, channel_list=[n_channel,-1], n_start=0, n_end=None))
    segments=splice_signal(channel_data)

    POWERS=[]
    for segment in segments:
        segment=np.transpose(segment)
        length=len(segment)
        fft_result = np.fft.fft(segment,axis=0)
        frequencies = np.fft.fftfreq(length, 1/sampling_rate)
        # # Take the magnitude of the FFT
        power_spectrum = np.abs(fft_result) ** 2
        
        # Filter the frequencies to the desired range
        filtered_indices = np.where((frequencies >= 8) & (frequencies <= 12))[0]
        # Calculate the power in the specified frequency band
        power_in_band = np.sum(power_spectrum[filtered_indices])
        POWERS.append(power_in_band)
        POWERS_np=np.array(POWERS)
    return (POWERS_np/np.max(POWERS_np))
