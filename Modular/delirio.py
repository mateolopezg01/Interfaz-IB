from PyQt6.QtWidgets import  QComboBox, QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QHBoxLayout, QProgressBar
from PyQt6.QtCore import  Qt, pyqtSignal, pyqtSlot, QSize, QTimer
from PyQt6.QtGui import QFont 
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
import sys
import numpy as np
from scipy import signal
import pyqtgraph as pg
import time
import sqlite3
# import pyaudio
import random
import time
import serial
import threading
import database as db
from serial.tools import list_ports

from PyQt6.QtWidgets import  QComboBox, QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QHBoxLayout, QProgressBar
from PyQt6.QtCore import  Qt, pyqtSignal, pyqtSlot, QSize, QTimer
from PyQt6.QtGui import QFont 
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
import sys
import numpy as np
from scipy import signal
import pyqtgraph as pg
import time
import sqlite3
import time
import serial
import threading
import random
import database as db
from serial.tools import list_ports
from signal_processing import Stimulation_Sequence, REST
from PyQt6 import QtWidgets, QtCore
import sys
import sqlite3
import logging
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QMessageBox, QScrollArea
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages
from database import get_sessions_by_patient_id



class NeurobackApp(QWidget):
    def __init__(self): 
        super().__init__()
        self.init_ui()

    def init_ui(self): #como se ve la ventana inicial + botones
        self.setWindowTitle("NeuroBack - Patient Registration")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")

        # Title label for NeuroBack
        self.label_title = QLabel("NeuroBack", self)
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.label_title.font()
        title_font.setPointSize(36)
        self.label_title.setFont(title_font)

        # Labels and input fields
        self.label_name = QLabel("Name:")
        self.entry_name = QLineEdit(self)

        self.label_age = QLabel("Age:")
        self.entry_age = QLineEdit(self)

        self.label_treatment = QLabel("Treatment Type:")
        self.entry_treatment = QLineEdit(self)

        self.label_sessions = QLabel("Number of Sessions:")
        self.entry_sessions = QLineEdit(self)

        # Button to save information
        self.btn_save = QPushButton("Save", self)
        self.btn_save.clicked.connect(self.save_data)

        # Button to view patient list
        self.btn_view_list = QPushButton("View Patient List", self)
        self.btn_view_list.clicked.connect(self.show_patient_list)

        # Layout of the main interface
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        # Center the title
        layout.addWidget(self.label_title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.label_name)
        layout.addWidget(self.entry_name)
        layout.addWidget(self.label_age)
        layout.addWidget(self.entry_age)
        layout.addWidget(self.label_treatment)
        layout.addWidget(self.entry_treatment)
        layout.addWidget(self.label_sessions)
        layout.addWidget(self.entry_sessions)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_view_list)

    def save_data(self):
        name = self.entry_name.text()
        age = self.entry_age.text()
        treatment = self.entry_treatment.text()
        sessions = self.entry_sessions.text()

        db.save_patient_data(name,age,treatment,sessions)

        # Clear the input fields
        self.entry_name.clear()
        self.entry_age.clear()
        self.entry_treatment.clear()
        self.entry_sessions.clear()

    def show_patient_list(self): #crear una ventana lista pacientes y definir las conexiones
        # Display the list in a new window
        self.patient_list_window = PatientListWindow()
        # Connect the patient selected signal to open session window
        self.patient_list_window.patientSelected.connect(self.open_session_window)
        # Connect the start session button signal
        self.patient_list_window.startSession.connect(self.open_session_window)
        # Connect the remove patient button signal
        self.patient_list_window.removePatient.connect(self.remove_patient)

        self.patient_list_window.getData.connect(self.get_patient_data)

        self.patient_list_window.show()

    @pyqtSlot(int)
    def open_session_window(self, patient_id): #definimos la función para crear la conexión entre la ventana sesión y la ventana lista pacientes
        # Open a new session window for the selected patient
        self.session_window = SessionWindow(patient_id)
        self.session_window.show()
        

    @pyqtSlot(int)
    def remove_patient(self, patient_id): #definimos la función para remover pacientes
        # Remove the patient from the patient list
        db.delete_patient_data(patient_id)

        # Update the patient list window
        self.patient_list_window.update_patient_list()
    
    @pyqtSlot(int)
    def get_patient_data(self, patient_id):
        self.data_window = PatientDataWindow(patient_id)
        self.data_window.show()

class PatientListWindow(QWidget):
    patientSelected = pyqtSignal(int)
    startSession = pyqtSignal(int)
    removePatient = pyqtSignal(int)
    getData = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self): #como se ve la ventana inicial
        self.setWindowTitle("Patient List")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")
        self.list_widget = QListWidget()
        self.add_list_buttons()
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
    
    def add_list_buttons(self):#añadir botones
        patient_data=db.get_patient_data()

        for patient in patient_data:
            id= patient["ID"]
            name = patient["Name"]
            age = patient["Age"]
            sessions = patient["Sessions"]

            item_text = f"Name: {name}, Age: {age}, Sessions: {sessions}"

            item = QListWidgetItem(item_text)
            item.setSizeHint(QSize(0, 80))
            
            btn_see_data = QPushButton("See Data")
            btn_see_data.clicked.connect(lambda _, id=id: self.getData.emit(id))

            btn_start_session = QPushButton("Start Session")
            # btn_start_session.clicked.connect(lambda _, id=id: self.startSession.emit(id))
            btn_start_session.clicked.connect(self.seleccionarparametros)

            btn_remove_patient = QPushButton("Remove Patient")
            btn_remove_patient.clicked.connect(lambda _, id=id : self.removePatient.emit(id))

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(QLabel(item_text))  # Display the name
            layout.addWidget(btn_see_data)
            layout.addWidget(btn_start_session)
            layout.addWidget(btn_remove_patient)

            container_item = QListWidgetItem()
            container_item.setSizeHint(QSize(0, 80))
            self.list_widget.addItem(container_item)
            self.list_widget.setItemWidget(container_item, widget)

    def update_patient_list(self):
        self.list_widget.clear()
        self.add_list_buttons()
    def seleccionarparametros(self):
        self.Vparametros=VentanaParametros()
        self.Vparametros.show()

class PatientDataWindow(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.patient_id = patient_id
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f"Patient {self.patient_id} Sessions Viewer")
        
        layout = QVBoxLayout()
        
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        
        self.load_sessions()
    
    def load_sessions(self):
        sessions = get_sessions_by_patient_id(self.patient_id)
        if not sessions:
            QMessageBox.warning(self, "No Sessions", "No sessions found for the given patient ID.")
            return
        
        for session in sessions:
            session_layout = QHBoxLayout()
            
            session_info = (
                f"Session {session['session_num']}:\n"
                f"  Duration: {session['duration']}\n"
                f"  Phases Applied: {session['phases_applied']}\n"
                f"  Record Channel: {session['record_channel']}\n"
                f"  PAF: {session['paf']}\n"
                f"  Powers: {session['powers']}\n"
            )
            
            info_label = QLabel(session_info)
            info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            button_layout = QVBoxLayout()
            plot_button = QPushButton("Plot")
            plot_button.clicked.connect(lambda _, s=session: self.plot_session(s))
            export_button = QPushButton("Export PDF")
            export_button.clicked.connect(lambda _, s=session: self.export_pdf(s))
            
            button_layout.addWidget(plot_button)
            button_layout.addWidget(export_button)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            session_layout.addWidget(info_label)
            session_layout.addLayout(button_layout)
            session_layout.setAlignment(button_layout, Qt.AlignmentFlag.AlignTop)
            
            self.scroll_layout.addLayout(session_layout)
    
    def plot_session(self, session):
        try:
            phases = list(map(float, session['phases_applied'].split(',')))
            powers = list(map(float, session['powers'].split(',')))
            if len(phases) != len(powers):
                QMessageBox.warning(self, "Data Error", "Phases and Powers length mismatch.")
                return
            # Sort the phases and powers together based on phases
            sorted_data = sorted(zip(phases, powers))
            phases, powers = zip(*sorted_data)
        except ValueError:
            QMessageBox.warning(self, "Data Error", "Invalid data format.")
            return
        
        fig, ax = plt.subplots()
        ax.plot(phases, powers, 'o-')
        ax.set_title(f"Session {session['session_num']}: Powers vs Phases Applied")
        ax.set_xlabel("Phases Applied")
        ax.set_ylabel("Powers")
        
        fig.show()
    
    def export_pdf(self, session):
        try:
            phases = list(map(float, session['phases_applied'].split(',')))
            powers = list(map(lambda x: f"{float(x):.2f}", session['powers'].split(',')))
            if len(phases) != len(powers):
                QMessageBox.warning(self, "Data Error", "Phases and Powers length mismatch.")
                return
            # Sort the phases and powers together based on phases
            sorted_data = sorted(zip(phases, powers))
            phases, powers = zip(*sorted_data)
        except ValueError:
            QMessageBox.warning(self, "Data Error", "Invalid data format.")
            return
        
        formatted_powers = ", ".join(powers)
        with PdfPages(f'session_{session["session_num"]}.pdf') as pdf:
            fig, ax = plt.subplots()
            ax.plot(phases, list(map(float, powers)), 'o-')
            ax.set_title(f"Session {session['session_num']}:\n"
                         f"Duration: {session['duration']}\n"
                         f"Phases Applied: {session['phases_applied']}\n"
                         f"Record Channel: {session['record_channel']}\n"
                         f"PAF: {session['paf']}\n"
                         f"Powers: {formatted_powers}")
            ax.set_xlabel("Phases Applied")
            ax.set_ylabel("Powers")
            pdf.savefig(fig)
            plt.close(fig)
        
        QMessageBox.information(self, "Export PDF", f"Session {session['session_num']} data and plot saved as PDF.")

class VentanaParametros(QWidget): 
    def __init__(self):
        super().__init__()
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Session parameters configuration")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")
        self.list_widget = QListWidget()

        self.insertar_filas_parametros()
        # Button to save information
        self.btn_save = QPushButton("Save", self)
        self.btn_save.clicked.connect(self.save_data)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.btn_save)

    def fila_parametro(self, parametro, nombre_parametro, items):
        item_text=nombre_parametro
        item = QListWidgetItem(item_text)
        item.setSizeHint(QSize(0, 80))

        parametro.addItems(items)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel(item_text))
        layout.addWidget(parametro)

        container_item = QListWidgetItem()
        container_item.setSizeHint(QSize(0, 80))
        self.list_widget.addItem(container_item)
        self.list_widget.setItemWidget(container_item, widget)

    def insertar_filas_parametros(self):
        self.numfases=QComboBox()
        self.fila_parametro(self.numfases,"Number of phases:",[str(i) for i in range(2,21)])
        self.duration=QComboBox()
        self.fila_parametro(self.duration,"Duration (minutes):",[str(i) for i in range(1,31)])
        lista_puertos=list_ports.comports()
        self.puerto=QComboBox()
        self.fila_parametro(self.puerto,"Serial port:",[str(port)for port in lista_puertos])
        lista_puertos.append("Synthetic")
        self.placa=QComboBox()
        self.fila_parametro(self.placa,"Board:",[str(port)for port in lista_puertos])
    
    def save_data(self):
        nphases = self.numfases.currentText()
        duration = self.duration.currentText()
        puerto = self.puerto.currentText()
        placa = self.placa.currentText()

        self.session_window = SessionWindow(nphases, duration, puerto, placa)
        self.session_window.show()
        self.close()


class SessionWindow(QWidget):
    def __init__(self, nphases, duration, puerto, placa):
        super().__init__()
        self.init_ui(nphases, duration, puerto, placa)

    def init_ui(self, nphases, duration, puerto, placa):
        self.setWindowTitle("Session Window")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")

        # Update to reflect passed parameters
        nfases= int(nphases)
        duracion = int(duration) * 60  # Convert minutes to seconds
        port= str(puerto.split(' ',1)[0])
        board= str(placa.split(' ',1)[0])
        self.board=board
        self.n_channel=4

        # Layout for the session window
        layout = QVBoxLayout(self)
        self.board_shim=self.parametros_brainflow(self.board)
        # self.btn_calibracion=QPushButton("Start Rest",self)
        # self.btn_calibracion.clicked.connect(self.init_brainflow_rest)
        # layout.addWidget(self.btn_calibracion)

        # Initialize BrainFlow and plotting      
        self.init_brainflow(nfases, duracion,port,self.board)

        # Add plot widget to layout
        self.plot_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.plot_widget)
        self._init_timeseries()

        # Start the timer for updating the plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # update every 50 ms
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.close)
        self.timer2.start(120000)


    def init_brainflow(self,number_of_intervals,total_duration,PuertoArduino = '/dev/cu.usbmodem1101',Board = 'Synthetic',n_channel=4):
        BoardShim.enable_dev_board_logger()
        self.board_shim,streamer_params=self.parametros_brainflow(Board)
        self.stop_flag = threading.Event()
        self.board_shim.prepare_session()
        self.board_shim.start_stream(450000, streamer_params)
        # Initialize your serial port object here
        self.serial_port = serial.Serial(PuertoArduino, 2000000)
        delay_list = np.linspace(0, 200, num=number_of_intervals, endpoint=False).tolist()
        random.shuffle(delay_list)
        interval_duration = total_duration / number_of_intervals
        # Start the Stimulation_Sequence in a separate thread
        stimulation_thread = threading.Thread(target=Stimulation_Sequence, args=(self.board_shim, self.serial_port, n_channel, delay_list,interval_duration, self.stop_flag))
        stimulation_thread.start()

        # Board info
        self.board_id = self.board_shim.get_board_id()
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.window_size = 2
        self.num_points = self.window_size * self.sampling_rate

    def parametros_brainflow(self,Board):
        params = BrainFlowInputParams()
        params.ip_port = 0
        params.serial_port = ''
        params.mac_address = ''
        params.other_info = ''
        params.ip_address = ''
        params.ip_protocol = 0
        params.timeout = 0
        params.file = ''
        board_id,params.serialport=self.obtener_id_placa(Board)
        streamer_params = ''
        board_shim = BoardShim(board_id, params)
        return board_shim, streamer_params

    def _init_timeseries(self):
        self.plots = []
        self.curves = []
        for i in range(1):  # Only one channel as per the original requirement
            p = self.plot_widget.addPlot(row=i, col=0)
            p.showAxis('left', True)
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
        self.curves[0].setData(data[self.n_channel].tolist())
    def comenzar_rest(self):
        self.falfapico=REST(self.board_shim)

    def obtener_id_placa(self,Board):
        if Board == 'Synthetic':
            board_id = BoardIds.SYNTHETIC_BOARD
            serial_port = ''
        else:
            board_id = BoardIds.CYTON_BOARD
            serial_port = Board
        return board_id , serial_port


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeurobackApp()
    window.show()
    sys.exit(app.exec())
