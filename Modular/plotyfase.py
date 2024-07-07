import logging
import threading
import time

import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
from PyQt6 import QtWidgets, QtCore

from scipy import signal


class Graph:
    def __init__(self, board_shim, stop_flag):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate
        self.stop_flag = stop_flag

        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(show=True, title='BrainFlow Plot')
        self.win.resize(800, 600)
        self.win.setWindowTitle('BrainFlow Plot')
        self.plotlist = [-1, 5, 2]
        self.plotlist = self.exg_channels
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

def phase_detection(board_shim, stop_flag,b,a,n_channel=0):
    anterior=-1
    y=[0,0,0,0,0]
    while not stop_flag.is_set():
        data = board_shim.get_current_board_data(5) # cant de canales x cant de muestras ej: data.shape=(32,5) al hacer get_current_board(data)(5) con placa Synth 
        #print(data[0][0]) #al hacer esto por muestra se imprimen un monton de veces las mismas o sea que esto se revisa muchas mas veces de las que entran muestras (OK)
        if data[0][0] != anterior and len(data[0])==5:
            anterior=data[0][0]
            x=data[n_channel]
            yn=b[0]*x[-1]+b[1]*x[-2]+b[2]*x[-3]+b[3]*x[-4]+b[4]*x[-5]-a[1]*y[-1]-a[2]*y[-2]-a[3]*y[-3]-a[4]*y[-4]
            y.append(yn)
            y=y[1:]
            if y[-1]*y[-2]<0:
                print('LED')
            





def stop_program_after_interval(interval, stop_flag):
    time.sleep(interval)
    stop_flag.set()


def main():
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
    board_id = BoardIds.SYNTHETIC_BOARD
    streamer_params = ''
    stop_flag = threading.Event()
    duration = 10  # Set the duration in seconds after which the program should stop
    b,a= PasaBanda()

    try:
        board_shim = BoardShim(board_id, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000, streamer_params)
        
        phase_thread = threading.Thread(target=phase_detection, args=(board_shim, stop_flag,b,a,1))
        phase_thread.start()
        
        timer_thread = threading.Thread(target=stop_program_after_interval, args=(duration, stop_flag))
        timer_thread.start()
        
        Graph(board_shim, stop_flag)
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()
