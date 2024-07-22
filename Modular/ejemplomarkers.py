from brainflow.data_filter import DataFilter
import matplotlib.pyplot as plt
import numpy as np
sampling_rate=250
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


def AlphaPowerFromFile(n_channel,access_route='DATA.csv'):
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

print(AlphaPowerFromFile(2))