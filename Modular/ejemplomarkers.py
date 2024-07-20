
import time
import logging
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
import matplotlib.pyplot as plt

def main():
    BoardShim.enable_dev_board_logger()

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
    try:
        board_shim = BoardShim(board_id, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000, streamer_params)
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()

    board_shim.prepare_session()

    board_shim.start_stream()
    for i in range(10):
        time.sleep(1)
        board_shim.insert_marker(i + 1)
    data = board_shim.get_board_data()
    board_shim.stop_stream()
    board_shim.release_session()

    print(data[-1])
    plt.plot(data[-1])
    plt.show()

if __name__ == "__main__":
    main()