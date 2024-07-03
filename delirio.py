from PyQt6.QtWidgets import  QMessageBox, QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QHBoxLayout, QProgressBar
from PyQt6.QtCore import  Qt, pyqtSignal, pyqtSlot, QSize, QTimer
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
import sys
import numpy as np
from scipy import signal
import pyqtgraph as pg
import time
import sqlite3
import pyaudio
import time
import serial
import threading

class NeurobackApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NeuroBack - Patient Registration")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")

        self.patient_data = []

        self.init_ui()

    def init_ui(self):
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

        # Set size policies for labels
        self.label_title.setSizePolicy(self.get_expanding_size_policy())
        self.label_name.setSizePolicy(self.get_expanding_size_policy())
        self.label_age.setSizePolicy(self.get_expanding_size_policy())
        self.label_treatment.setSizePolicy(self.get_expanding_size_policy())
        self.label_sessions.setSizePolicy(self.get_expanding_size_policy())

    def get_expanding_size_policy(self):
        size_policy = QSizePolicy()
        size_policy.setVerticalPolicy(QSizePolicy.Policy.Expanding)
        return size_policy

    def save_data(self):
        name = self.entry_name.text()
        age = self.entry_age.text()
        treatment = self.entry_treatment.text()
        sessions = self.entry_sessions.text()

        # Save data to database
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id_patient INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                treatment TEXT,
                sessions INTEGER
            )
        """)

        cursor.execute("INSERT INTO patients (name, age, treatment, sessions) VALUES (?, ?, ?, ?)",
            (name, age, treatment, sessions))


        cursor.execute(f"CREATE TABLE IF NOT EXISTS {name}(session_num INTEGER PRIMARY KEY AUTOINCREMENT,PAF FLOAT,cal_route TEXT,ev_route TEXT)")
        # Commit changes
        connection.commit()

        # Close connection
        connection.close()

        # Clear the input fields
        self.entry_name.clear()
        self.entry_age.clear()
        self.entry_treatment.clear()
        self.entry_sessions.clear()

    def show_patient_list(self):
        # Display the list in a new window
        self.patient_list_window = PatientListWindow()
        self.patient_list_window.setWindowTitle("Patient List")
        self.patient_list_window.setGeometry(100, 100, 600, 400)
        self.patient_list_window.setStyleSheet("background-color: #1E3B4D; color: white;")

        # Connect the patient selected signal to open session window
        self.patient_list_window.patientSelected.connect(self.open_session_window)
        # Connect the start session button signal
        self.patient_list_window.startSession.connect(self.open_session_window)
        # Connect the remove patient button signal
        self.patient_list_window.removePatient.connect(self.remove_patient)

        self.patient_list_window.getData.connect(self.get_patient_data)

        self.patient_list_window.show()

    @pyqtSlot(int)
    def open_session_window(self, patient_id):
        # Open a new session window for the selected patient
        self.session_window = SessionWindow(patient_id)
        self.session_window.show()

    @pyqtSlot(int)
    def remove_patient(self, patient_id):
        # Remove the patient from the patient list
        self.delete_patient_data(patient_id)

        # Update the patient list window
        self.patient_list_window.update_patient_list()
    
    @pyqtSlot(int)
    def get_patient_data(self, patient_id):
        self.data_window = PatientDataWindow(patient_id)
        self.data_window.show()

    # New method to delete patient data
    def delete_patient_data(self, patient_id):
        conn = sqlite3.connect('patient_data.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM patients WHERE id_patient=?", (patient_id,))

        conn.commit()
        conn.close()


class PatientListWindow(QWidget):
    patientSelected = pyqtSignal(int)
    startSession = pyqtSignal(int)
    removePatient = pyqtSignal(int)
    getData = pyqtSignal(int)

    def __init__(self):#, patient_data):
        super().__init__()
        
        # Connect to the database
        connection = sqlite3.connect("patient_data.db")

        # Create a cursor
        cursor = connection.cursor()

        # Execute the query `SELECT * FROM patients`
        cursor.execute(f"SELECT * FROM patients")
        # Create a list to store the results
        patient_data = []
        row=[]
        # Iterate over the results of the query and add them to the list
        for row in cursor.fetchall():
            id=row[0]
            name=row[1]
            age=row[2]
            treatment=row[3]
            sessions=row[4]
            patient_data.append({"ID": id,"Name": name, "Age": age, "Treatment": treatment, "Sessions": sessions})
        
        print("La lista de pacientes es:" , patient_data)
        # Close the cursor and the connection to the database
        cursor.close()
        connection.close()

        self.list_widget = QListWidget()

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
            btn_start_session.clicked.connect(lambda _, id=id: self.startSession.emit(id))

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

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
    
    def confirmar(self):
        msg=QMessageBox()
        msg.setWindowTitle("Confirm patient removal")
        msg.setText("Are you sure that you want to remove this patient?")
        msg.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        
        x = msg.exec_()

    def execute_popup_window():
        # Create a new instance of the popup window class
        popup_window = PopupWindow()

        # Start the event loop
        popup_window.app.exec()


    def update_patient_list(self):
        self.list_widget.clear()
        # Connect to the database
        connection = sqlite3.connect("patient_data.db")

        # Create a cursor
        cursor = connection.cursor()

        # Execute the query `SELECT * FROM patients`
        cursor.execute(f"SELECT * FROM patients")
        # Create a list to store the results
        row=[]
        # Iterate over the results of the query and add them to the list
        for row in cursor.fetchall():
            id=row[0]
            name=row[1]
            age=row[2]
            sessions=row[4]
            
            item_text = f"Name: {name}, Age: {age}, Sessions: {sessions}"

            item = QListWidgetItem(item_text)
            item.setSizeHint(QSize(0, 80))

            btn_see_data = QPushButton("See Data")
            btn_see_data.clicked.connect(lambda _, id=id: self.getData.emit(id))

            btn_start_session = QPushButton("Start Session")
            btn_start_session.clicked.connect(lambda _, name=name: self.startSession.emit(name))

            btn_remove_patient = QPushButton("Remove Patient")
            btn_remove_patient.clicked.connect(self.confirmar)
            btn_remove_patient.clicked.connect(lambda _, id=id: self.removePatient.emit(id))

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

        # Close the cursor and the connection to the database
        cursor.close()
        connection.close()

class PopupWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set the window title
        self.setWindowTitle("Popup Window")

        # Create a layout for the window
        layout = QVBoxLayout()

        # Add a label to the layout
        label = QLabel("Confirmation")
        layout.addWidget(label)

        # Add a button to the layout
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        layout.addWidget(button)

        # Set the layout for the window
        self.setLayout(layout)

        # Show the window
        self.show()

class PatientDataWindow(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle(f"NeuroBack - Data Controls for {patient_id}")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")

        self.plot_power = pg.PlotWidget()
        # self.plot_widget.setBackground((18,60,790))

        h_layout = QHBoxLayout()    
        h_layout.addWidget(self.plot_power)


class SessionWindow(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()

        n_session=1
        # Execute the query `SELECT * FROM patients`
        cursor.execute(f"SELECT * FROM patients WHERE id_patient=?", (patient_id,))

        # Create a list to store the results
        row=cursor.fetchone()
        id=row[0]
        name=row[1]
        sessions=row[4]

        self.nombre=name

        cursor.execute(f"SELECT * FROM {name} ORDER BY session_num DESC LIMIT 1")

        registro = cursor.fetchone()
        if registro is not None:

            n_session=registro[0]+1

        connection.commit()
        connection.close()

        self.nombre_CAL=f"CAL-EEG{name}{n_session}.csv"
        self.nombre_EV=f"EV-EEG{name}{n_session}.csv"


        self.value=0
        self.period=1

        self.setWindowTitle(f"NeuroBack - Session Controls for {name}")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")

        plot_duration = 5
        sample_frecuency=250
        self.plot_length=int(plot_duration*sample_frecuency)

        # Create a PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((18,60,790))

        # Create a horizontal layout for the PlotWidget and buttons
        h_layout = QHBoxLayout()    
        h_layout.addWidget(self.plot_widget)

        # Create a vertical layout for the main window
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(20, 20, 20, 20)

        # Add the horizontal layout to the vertical layout
        v_layout.addLayout(h_layout)
        
        # Create a label
        self.period_label = QLabel("Press Start Calibration to begin")

        v_layout.addWidget(self.period_label)


        # Create a progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        # Start the progress bar
        self.progress_bar.setValue(0)

        # Add the progress bar to the main window
        v_layout.addWidget(self.progress_bar)
        # Add the buttons to the vertical layout
        btn_start_recording = QPushButton("Start Calibration", self)
        btn_start_evaluation = QPushButton("Start Evaluation", self)
        btn_stop_session = QPushButton("Stop Session", self)
        btn_calc_PAF= QPushButton("Calculate PAF", self)
        btn_conectar=QPushButton("Connect Cyton", self)

        # Connect buttons to slots
        btn_start_recording.clicked.connect(self.start)
        btn_start_evaluation.clicked.connect(self.evaluation)
        btn_stop_session.clicked.connect(self.stop)
        btn_calc_PAF.clicked.connect(self.calc_PAF)
        btn_conectar.clicked.connect(self.connect_cyton)

        # Create a QLabel to display the PAF value
        self.paf_label = QLabel("PAF: ", self)

        # Add the PAF label to the vertical layout
        v_layout.addWidget(self.paf_label)

        v_layout.addWidget(btn_conectar)
        v_layout.addWidget(btn_start_recording)
        v_layout.addWidget(btn_start_evaluation)
        #layout.addWidget(btn_start_session)
        v_layout.addWidget(btn_stop_session)
        v_layout.addWidget(btn_calc_PAF)
        

        # Open the WAV file
        wav_file = open('beep.wav', 'rb')
        self.wav_data = wav_file.read()

        # self.setLayout(v_layout)
    def reset_progress_bar(self):
        self.value=0
        self.progress_bar.reset()
        
        # Create a Stream object
        stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)

        # Play the WAV file
        stream.write(self.wav_data)

        # Close the Stream object
        stream.stop_stream()
        stream.close()

    def update_progress(self):
        # Set the progress bar value
        self.value+=1
        self.progress_bar.setValue(self.value)

        # Update the progress bar
        self.progress_bar.update()

    def evaluation(self):
        PuertoArduino='/dev/cu.usbmodem101'
        PuertoPlaca='/dev/cu.usbserial-DM03H6KD'
        Placa='Sintetica'
        ruta=self.nombre_EV
        canal=7
        fs = 250
        if self.PAF is not None:
            fr=self.PAF
        else:
            fr=10
        tGuardado=10
        tDuracion=20
        POTENCIAS=[]
        dt=12.5/1000
        self.period=10
        for i in range(11):
            delay_time=i*dt
            start=i*int(tDuracion*fs)
            end=(i+1)*int(tDuracion*fs)-1
            Pi=Estim(PuertoArduino,Placa,PuertoPlaca,ruta,canal,fs,fr,tDuracion,tGuardado,dt,startPosition=start,endPosition=end,PLOT=False)
            POTENCIAS.append(Pi)
        self.period_label.setText("Evaluation: ER-NF")
        self.start_part1(210*1000)

    def PasaBanda(Fr,Fs=250,plotear=False):
        b, a = signal.iirfilter(2, [(Fr-1),(Fr+1)], btype='band', analog=False, ftype='butter',fs=Fs)
        return b, a


    def led_toggle_ON(puerto_serie,delay_time):
        # Adjust the delay time as needed (in seconds)
        time.sleep(delay_time)
        puerto_serie.write('p'.encode())

    def led_toggle_OFF(puerto_serie,delay_time):
        time.sleep(delay_time)
        puerto_serie.write('a'.encode())


    def P_Welch(ruta,canal,Fs,startPosition=0,endPosition=-1):
        lab= open(ruta)
        datos = np.loadtxt(lab, delimiter="\t")
        datos=np.transpose(datos)
        x=datos[canal][startPosition:endPosition]
        # Estimate PSD `S_xx_welch` at discrete frequencies `f_welch`
        f_welch, S_xx_welch = signal.welch(x, fs=Fs)
        # Integrate PSD over spectral bandwidth
        df_welch = f_welch[1] - f_welch[0]

        indices_intervalo = np.where((f_welch >= 8) & (f_welch <= 12))[0]
        # Seleccionar las frecuencias y la PSD dentro del intervalo deseado
        S_xx_intervalo = S_xx_welch[indices_intervalo]
        return  np.sum(S_xx_intervalo) * df_welch #AlfaPower
        
    def Estim(PuertoArduino,Placa,PuertoPlaca,ruta,canal,fs,fr,tDuracion,tGuardado,delay_time,PLOT=False,startPosition=0,endPosition=-1):
        puerto_serie = serial.Serial(PuertoArduino, 2000000)
        BoardShim.enable_dev_board_logger()
        params = BrainFlowInputParams()
        if Placa == 'CYTON':
            board_id = BoardIds.CYTON_BOARD.value ; DATA=np.zeros((24,0))
        else:
            board_id = BoardIds.SYNTHETIC_BOARD.value ; DATA=np.zeros((32,0))
        params.serial_port = PuertoPlaca
        board = BoardShim(board_id, params)
        board.prepare_session()
        board.start_stream ()
        y=[0,0,0,0,0]
        x=[0,0,0,0,0]
        b,a=PasaBanda(fr,fs)
        cruces=[]
        error=0
        i=0
        time.sleep(0.5)
        while i< tDuracion*fs:
            #data= board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
            data = board.get_board_data()  # get all data and remove it from internal buffer
            DATA = np.concatenate((DATA, data), axis=1)
            if data.shape[1] != 0:
                i+=1
                if data.shape[1] != 1:
                    error+=1
                    print('error')
                D=data[canal][-1]
                x.append(D)
                yn=b[0]*x[-1]+b[1]*x[-2]+b[2]*x[-3]+b[3]*x[-4]+b[4]*x[-5]-a[1]*y[-1]-a[2]*y[-2]-a[3]*y[-3]-a[4]*y[-4]
                if yn>0 and y[-1]<0: # revisar esta condicion
                    cruces.append(len(y)/fs)
                    threading.Thread(target=led_toggle_ON, args=(puerto_serie, delay_time)).start()
                elif yn<0 and y[-1]>0: # revisar esta condicion
                    threading.Thread(target=led_toggle_OFF, args=(puerto_serie, delay_time)).start()
                y.append(yn)
                if not PLOT:
                    x=x[1:]
                    y=y[1:]
            if i%int(fs*tGuardado)==0:
                DataFilter.write_file(DATA, ruta, 'a')
                np.delete(DATA, np.s_[:], axis=1)

        DataFilter.write_file(DATA, 'ruta', 'a')
        np.delete(DATA, np.s_[:], axis=1)
        board.stop_stream()
        board.release_session()
        Palfa=P_Welch(ruta,canal,fs,startPosition,endPosition)
        return Palfa
    def start_part1(self,largo):
        self.T1 =QTimer()
        self.T1.setInterval(largo)
        self.T1.start()
        self.T1.timeout.connect(self.end_part1)

    def conectar_protocolo(self):
    
    def end_part1(self):
        self.T1.stop()
        self.end_evaluation(1000)
    
    def end_evaluation(self):
        self.period_label.setText("Evaluation finished")
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()

        cursor.execute(f"INSERT INTO {self.nombre} (PAF, cal_route, ev_route) VALUES (?, ?, ?)",
            (self.PAF, self.nombre_CAL, self.nombre_EV))

        connection.commit()
        connection.close()       



    @pyqtSlot()
    def connect_cyton(self):
        # SE ESTABLECE COMUNICACIÓN CON CYTHON
        # BoardShim.enable_board_logger()
        BoardShim.enable_dev_board_logger()
        params = BrainFlowInputParams()
        params.serial_port = '/dev/ttyUSB0'
        # params.serial_port = 'COM12'
        # params.timeout = 0
        # params.file = ''
        board_id = BoardIds.SYNTHETIC_BOARD.value
        #board_id = BoardIds.CYTON_BOARD.value
        self.board = BoardShim(board_id, params)
        self.board.prepare_session()

        # self.board.config_board('x1060100X')
        # self.board.config_board('x2160100X')
        # self.board.config_board('x3160100X')
        # self.board.config_board('x4160100X')
        # self.board.config_board('x5160100X')
        # self.board.config_board('x6160100X')
        # self.board.config_board('x7160100X')
        # self.board.config_board('x8160100X')


    def start_VEP1(self, largo):
        self.period_label.setText("First period: VEP")
        self.tVEP1 =QTimer()
        self.tVEP1.setInterval(largo)
        self.timer1 = QTimer()
        self.timer1.setInterval(largo//100)
        self.timer1.timeout.connect(self.update_progress)
        self.timer1.start()
        self.tVEP1.start()
        self.tVEP1.timeout.connect(self.end_VEP1)

    def end_VEP1(self):

        self.reset_progress_bar()
        self.timer1.stop()
        self.tVEP1.stop()
        self.start_rest1(1000)

    def start_rest1(self,largo):
        self.period=2
        self.period_label.setText("2nd period: RESTING")
        self.tREST1 =QTimer()
        self.tREST1.setInterval(largo)
        self.timer2 = QTimer()
        self.timer2.setInterval(largo//100)
        self.timer2.timeout.connect(self.update_progress)
        self.timer2.start()
        self.tREST1.start()
        self.tREST1.timeout.connect(self.end_rest1)

    def end_rest1(self):
        self.reset_progress_bar()
        self.timer2.stop()
        self.tREST1.stop()
        self.start_VEP2(1000)

    def start_VEP2(self, largo):
        self.period=3
        self.period_label.setText("3rd period: VEP")
        self.tVEP2 =QTimer()
        self.tVEP2.setInterval(largo)
        self.timer3 = QTimer()
        self.timer3.setInterval(largo//100)
        self.timer3.timeout.connect(self.update_progress)
        self.timer3.start()
        self.tVEP2.start()
        self.tVEP2.timeout.connect(self.end_VEP2)

    def end_VEP2(self):
        self.reset_progress_bar()
        self.timer3.stop()
        self.tVEP2.stop()
        self.start_rest2(1000)

    def start_rest2(self, largo):
        self.period=4
        self.period_label.setText("4th period: RESTING")
        self.tREST2 =QTimer()
        self.tREST2.setInterval(largo)
        self.timer4 = QTimer()
        self.timer4.setInterval(largo//100)
        self.timer4.timeout.connect(self.update_progress)
        self.timer4.start()
        self.tREST2.start()
        self.tREST2.timeout.connect(self.end_rest2)

    def end_rest2(self):
        self.reset_progress_bar()
        self.timer4.stop()
        self.tREST2.stop()
        self.start_VEP3(1000)

    def start_VEP3(self, largo):
        self.period=5
        self.period_label.setText("5th period: VEP")
        self.tVEP3 =QTimer()
        self.tVEP3.setInterval(largo)
        self.timer5 = QTimer()
        self.timer5.setInterval(largo//100)
        self.timer5.start()
        self.tVEP3.start()
        self.timer5.timeout.connect(self.update_progress)
        self.tVEP3.timeout.connect(self.end_VEP3)
    
    def end_VEP3(self):
        self.reset_progress_bar()
        self.timer5.stop()
        self.tVEP3.stop()
        self.start_rest3(1000)
    
    def start_rest3(self, largo):
        self.period=6
        self.period_label.setText("6th period: RESTING")
        self.tREST3 =QTimer()
        self.tREST3.setInterval(largo)
        self.timer6 = QTimer()
        self.timer6.setInterval(largo//100)
        self.timer6.timeout.connect(self.update_progress)
        self.timer6.start()
        self.tREST3.start()
        self.tREST3.timeout.connect(self.end_rest3)    

    def end_rest3(self):
        self.reset_progress_bar()
        self.timer6.stop()
        self.tREST3.stop()
        self.start_VEP4(1000)

    def start_VEP4(self, largo):
        self.period=7
        self.period_label.setText("7th period: VEP")
        self.tVEP4 =QTimer()
        self.tVEP4.setInterval(largo)
        self.timer7 = QTimer()
        self.timer7.setInterval(largo//100)
        self.timer7.timeout.connect(self.update_progress)
        self.timer7.start()
        self.tVEP4.start()
        self.tVEP4.timeout.connect(self.end_VEP4)
    
    def end_VEP4(self):
        self.reset_progress_bar()
        self.timer7.stop()
        self.tVEP4.stop()
        self.start_rest4(1000)
    
    def start_rest4(self, largo):
        self.period=8
        self.period_label.setText("Last period: RESTING")
        self.tREST4 =QTimer()
        self.tREST4.setInterval(largo)
        self.timer8 = QTimer()
        self.timer8.setInterval(largo//100)
        self.timer8.timeout.connect(self.update_progress)
        self.timer8.start()
        self.tREST4.start()
        self.tREST4.timeout.connect(self.end_rest4)    

    def end_rest4(self):
        self.period_label.setText("Calibration finished")
        self.reset_progress_bar()
        self.timer8.stop()
        self.tREST4.stop()
        self.stop()


    def start(self):
        self.board.start_stream(900000)  # arranca la cyton
        print("START")
        time.sleep(2)

        self.x = [0]  
        self.y = [0]  
        self.pen = pg.mkPen(color=(106, 255, 164))
        self.data_line = self.plot_widget.plot(self.x, self.y, pen=self.pen)

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        self.start_VEP1(1000)

    def stop(self):
        self.board.stop_stream()
        data = self.board.get_board_data()
        if self.period<10:
            DataFilter.write_file(data, self.nombre_CAL, 'a')  # use 'a' for append mode
        else:
            DataFilter.write_file(data, self.nombre_EV, 'a')  # use 'a' for append mode
        self.timer.stop()
        self.plot_widget.clear()
        print("STOP")
        match self.period:
            case 1:
                self.timer1.stop()
                self.tVEP1.stop()
            case 2:
                self.timer2.stop()
                self.tREST1.stop()
            case 3:
                self.timer3.stop()
                self.tVEP2.stop()
            case 4:
                self.timer4.stop()
                self.tREST2.stop()
            case 5:
                self.timer5.stop()
                self.tVEP3.stop()
            case 6:
                self.timer6.stop()
                self.tREST3.stop()
            case 7:
                self.timer7.stop()
                self.tVEP4.stop()
            case 8:
                self.timer8.stop()   
                self.tREST4.stop()
            case 10:
                self.T1.stop()
        self.progress_bar.reset() 

    
    def update_plot_data(self):
        newDATA = self.board.get_board_data()
        n = len(newDATA[0])  # Number of new data points
        # Extend 'x' and 'y' with the new data using NumPy
        new_x = np.arange(self.x[-1]+1, self.x[-1]+1 + n)
        new_y = newDATA[1]
        
        self.x = np.append(self.x, new_x)
        self.y = np.append(self.y, new_y)

        if len(self.y)>self.plot_length:
            y_plot=self.y[-self.plot_length:]
            x_plot=self.x[-self.plot_length:]
        else:
            y_plot=self.y
            x_plot=self.x
        self.data_line.setData(x_plot, y_plot)  # Update the data.
        if self.period<10:
            DataFilter.write_file(newDATA,'CAL-EEG.csv', 'a')  # use 'a' for append mode
        else:
            DataFilter.write_file(newDATA,'EV-EEG.csv', 'a')  # use 'a' for append mode      
    def calc_PAF(self):
        # Cargamos los datos de las señales EEG desde un archivo
        lab= open(self.nombre_CAL)
        datos = np.loadtxt(lab, delimiter="\t")
        datos=np.transpose(datos)
        datos=datos[1:] #Eliminamos la primer columna
        muestras=datos.shape[1]
        t = np.linspace(0,muestras/250, muestras)
        i=0
        eeg=np.zeros([3, muestras])
        for c in [5,6,7]:
            eeg[i]=datos[c]
            i+=1
        eog=np.zeros([2, muestras])
        i=0
        for c in [1,2]:
            eog[i]=datos[c]
            i+=1

        fs=250
        rest=eeg[0]
        
        # Filtra la señal en la banda de 8 a 12 Hz
        sos = signal.butter(2**5, [8, 12], 'band', analog=False, fs=250, output='sos')
        s_filt = signal.sosfiltfilt(sos, rest)
        # Calcula la frecuencia pico
        nper = int(fs * 0.75)
        f, DSP=signal.welch(s_filt, fs,  noverlap=nper//2, nperseg=nper)
        self.PAF=f[np.argmax(DSP)]
        self.paf_label.setText(f"PAF: {self.PAF:.2f}")
        # Imprime la frecuencia pico
        print(f"La frecuencia pico es {self.PAF} Hz")  




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeurobackApp()
    window.show()
    sys.exit(app.exec())