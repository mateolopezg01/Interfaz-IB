from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
import numpy as np
from scipy import signal
import serial
import threading

def initialize_board(placa, puerto_placa):
    params = BrainFlowInputParams()
    params.serial_port = puerto_placa
    if placa == 'CYTON':
        board_id = BoardIds.CYTON_BOARD.value
    else:
        board_id = BoardIds.SYNTHETIC_BOARD.value
    board = BoardShim(board_id, params)
    board.prepare_session()
    return board

def pasa_banda(Fr, Fs=250):
    b, a = signal.iirfilter(2, [(Fr-1), (Fr+1)], btype='band', analog=False, ftype='butter', fs=Fs)
    return b, a

def p_welch(ruta, canal, Fs, start_position=0, end_position=-1):
    lab = open(ruta)
    datos = np.loadtxt(lab, delimiter="\t")
    datos = np.transpose(datos)
    x = datos[canal][start_position:end_position]
    f_welch, S_xx_welch = signal.welch(x, fs=Fs)
    df_welch = f_welch[1] - f_welch[0]
    indices_intervalo = np.where((f_welch >= 8) & (f_welch <= 12))[0]
    S_xx_intervalo = S_xx_welch[indices_intervalo]
    return np.sum(S_xx_intervalo) * df_welch

def estim(board, puerto_arduino, ruta, canal, fs, fr, t_duracion, t_guardado, delay_time, start_position=0, end_position=-1, plot=False):
    puerto_serie = serial.Serial(puerto_arduino, 2000000)
    BoardShim.enable_dev_board_logger()
    data = np.zeros((32, 0)) if board.get_board_id() == BoardIds.SYNTHETIC_BOARD.value else np.zeros((24, 0))
    b, a = pasa_banda(fr, fs)
    y = [0] * 5
    x = [0] * 5
    cruces = []
    error = 0
    for i in range(t_duracion * fs):
        new_data = board.get_board_data()
        data = np.concatenate((data, new_data), axis=1)
        if new_data.shape[1] != 0:
            if new_data.shape[1] != 1:
                error += 1
            D = new_data[canal][-1]
            x.append(D)
            yn = b[0] * x[-1] + b[1] * x[-2] + b[2] * x[-3] + b[3] * x[-4] + b[4] * x[-5] - a[1] * y[-1] - a[2] * y[-2] - a[3] * y[-3] - a[4] * y[-4]
            if yn > 0 and y[-1] < 0:
                cruces.append(len(y) / fs)
                threading.Thread(target=led_toggle_on, args=(puerto_serie, delay_time)).start()
            elif yn < 0 and y[-1] > 0:
                threading.Thread(target=led_toggle_off, args=(puerto_serie, delay_time)).start()
            y.append(yn)
            if not plot:
                x = x[1:]
                y = y[1:]
        if i % int(fs * t_guardado) == 0:
            DataFilter.write_file(data, ruta, 'a')
            data = np.zeros((32, 0)) if board.get_board_id() == BoardIds.SYNTHETIC_BOARD.value else np.zeros((24, 0))
    DataFilter.write_file(data, ruta, 'a')
    board.stop_stream()
    board.release_session()
    palfa = p_welch(ruta, canal, fs, start_position, end_position)
    return palfa

def led_toggle_on(puerto_serie, delay_time):
    threading.Timer(delay_time, lambda: puerto_serie.write('p'.encode())).start()

def led_toggle_off(puerto_serie, delay_time):
    threading.Timer(delay_time, lambda: puerto_serie.write('a'.encode())).start()
