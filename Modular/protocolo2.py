#SESION DE REST.
import logging
import threading
import time

import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
from PyQt6 import QtWidgets, QtCore
from scipy import signal
import serial
import numpy as np



                


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


def REST(board_shim,duration,access_route='DATA.csv'):
    board_shim.insert_marker(1)
    time.sleep(duration)
    board_shim.insert_marker(1)
    save(board_shim,access_route,'a')

class Graph:
    def __init__(self, board_shim,n_channel=1):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 2
        self.num_points = self.window_size * self.sampling_rate

        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(show=True, title='BrainFlow Plot')
        self.win.resize(800, 600)
        self.win.setWindowTitle('BrainFlow Plot')
        self.plotlist = [n_channel]
        #self.plotlist = self.exg_channels
        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtWidgets.QApplication.instance().exec()

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.plotlist)):  # self.plotlist replaces self.exg_channels to plot only selected channels
            p = self.win.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        for count, channel in enumerate(self.plotlist):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            self.curves[count].setData(data[channel].tolist())

        self.app.processEvents()

def main():
    Board = 'SYNTH'
    PuertoArduino = '/dev/cu.usbmodem1101'
    n_channel = 1
    total_duration = 30  # duration in seconds
    number_of_intervals = 6

    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    params = BrainFlowInputParams()
    params.ip_port = 0
    params.serial_port = ''
    params.mac_address = ''
    params.other_info = ''
    params.serial_number = ''
    params.ip_address = ''
    params.ip_protocol = 0
    params.timeout = 0
    params.file = ''
    if Board == 'CYTON':
        board_id = BoardIds.CYTON_BOARD
    else:
        board_id = BoardIds.SYNTHETIC_BOARD

    streamer_params = ''
    stop_flag = threading.Event()
    try:
        board_shim = BoardShim(board_id, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000, streamer_params)
        # Initialize your serial port object here
        serial_port = serial.Serial(PuertoArduino, 2000000)
        # Start the Stimulation_Sequence in a separate thread
        resting_thread = threading.Thread(target=REST, args=(board_shim,duration,access_route='DATA.csv'))
        resting_thread.start()

        # Start the Graph in the main thread
        Graph(board_shim, n_channel)

        
    #Graph(board_shim, stop_flag, n_channel)
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()

if __name__ == '__main__':
    main()
