from brainflow.data_filter import DataFilter


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

data= get_data_from_file(access_route='/Users/juanblasperedocamio/Documents/TPIB2FINAL/DATA.csv',channel_list=[0],n_start=0,n_end=100)
print(data)


