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


class Graph:
    def __init__(self, board_shim, stop_flag,n_channel=1):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 2
        self.num_points = self.window_size * self.sampling_rate
        self.stop_flag = stop_flag

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
        if self.stop_flag.is_set():
            self.app.quit()
            return

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

def PasaBanda(Fr=10,Fs=250): #devuelve a y b de 5 coef c/u
    b, a = signal.iirfilter(2, [(Fr-1),(Fr+1)], btype='band', analog=False, ftype='butter',fs=Fs)
    return b, a

def led_toggle_ON(puerto_serie,delay_time):
    # Adjust the delay time as needed (in seconds)
    time.sleep(delay_time)
    puerto_serie.write('p'.encode())

def led_toggle_OFF(puerto_serie,delay_time):
    time.sleep(delay_time) 
    puerto_serie.write('a'.encode())

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
                if data[0][0] != anterior+1 and data[0][0]!=0:#REVISAR el caso de ==0 si el anterior el 250
                    print('OJO, salteó muestras')
                    print(anterior,data[0][0])
                anterior=data[0][0]
                x.append(data[n_channel][-1])
                x=x[1:]
                yn=b[0]*x[-1]+b[1]*x[-2]+b[2]*x[-3]+b[3]*x[-4]+b[4]*x[-5]-a[1]*y[-1]-a[2]*y[-2]-a[3]*y[-3]-a[4]*y[-4]
                y.append(yn)
                y=y[1:]
                if y[-1]*y[-2]<0:
                    print('Zero crossing detected')
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





def main():
    Board = 'SYNTH'
    PuertoArduino = '/dev/cu.usbmodem1101'
    n_channel = 1
    total_duration = 30  # duration in seconds
    number_of_intervals = 6
    delay_list = np.linspace(0, 200, num=number_of_intervals, endpoint=False).tolist()
    interval_duration = total_duration / number_of_intervals

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
    b, a = PasaBanda()

    try:
        board_shim = BoardShim(board_id, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000, streamer_params)
        # Initialize your serial port object here
        serial_port = serial.Serial(PuertoArduino, 2000000)

        # Start the for loop and delay threads in the main thread
        for index, delay in enumerate(delay_list):
            print('index', index,'delay',delay)
            delay=delay/1000
            stop_flag.clear()

            # Ensure the marker value is not zero
            marker_value = index + 1

            phase_thread = threading.Thread(target=phase_detection,
                                            args=(board_shim, stop_flag, b, a, serial_port, n_channel, delay, marker_value))
            phase_thread.start()

            timer_thread = threading.Thread(target=stop_program_after_interval, args=(interval_duration, stop_flag))
            timer_thread.start()

            # Wait for the timer thread to finish before starting the next interval
            timer_thread.join()
            save(board_shim)

        # Start the Graph in the main thread after the loop
        Graph(board_shim, stop_flag, n_channel)

    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()

if __name__ == '__main__':
    main()
