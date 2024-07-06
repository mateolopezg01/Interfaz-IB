from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QHBoxLayout, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
import pyqtgraph as pg
from database import save_patient_data, delete_patient_data, get_patient_data, get_patient_session
from signal_processing import initialize_board, estim

class NeurobackApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroBack - Patient Registration")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")
        self.patient_data = []
        self.init_ui()

    def init_ui(self):
        self.label_title = QLabel("NeuroBack", self)
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self.label_title.font()
        title_font.setPointSize(36)
        self.label_title.setFont(title_font)

        self.label_name = QLabel("Name:")
        self.entry_name = QLineEdit(self)
        self.label_age = QLabel("Age:")
        self.entry_age = QLineEdit(self)
        self.label_treatment = QLabel("Treatment Type:")
        self.entry_treatment = QLineEdit(self)
        self.label_sessions = QLabel("Number of Sessions:")
        self.entry_sessions = QLineEdit(self)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.clicked.connect(self.save_data)

        self.btn_view_list = QPushButton("View Patient List", self)
        self.btn_view_list.clicked.connect(self.show_patient_list)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.addWidget(self.label_title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.label_name)
        layout.addWidget(self.entry_name)
        layout.addWidget(self.label_age)
        layout.addWidget(self.entry_age)
        layout.addWidget(self.label_treatment)
        layout.addWidget(self.entry_treatment)
        layout.addWidget(self.label_sessions)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_view_list)

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
        save_patient_data(name, age, treatment, sessions)
        self.entry_name.clear()
        self.entry_age.clear()
        self.entry_treatment.clear()
        self.entry_sessions.clear()

    def show_patient_list(self):
        self.patient_list_window = PatientListWindow()
        self.patient_list_window.setWindowTitle("Patient List")
        self.patient_list_window.setGeometry(100, 100, 600, 400)
        self.patient_list_window.setStyleSheet("background-color: #1E3B4D; color: white;")
        self.patient_list_window.patientSelected.connect(self.open_session_window)
        self.patient_list_window.startSession.connect(self.open_session_window)
        self.patient_list_window.removePatient.connect(self.remove_patient)
        self.patient_list_window.getData.connect(self.get_patient_data)
        self.patient_list_window.show()

    def open_session_window(self, patient_id):
        self.session_window = SessionWindow(patient_id)
        self.session_window.show()

    def remove_patient(self, patient_id):
        delete_patient_data(patient_id)
        self.patient_list_window.update_patient_list()

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
        patient_data = get_patient_data()
        self.list_widget = QListWidget()
        for patient in patient_data:
            id = patient["ID"]
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
            btn_remove_patient.clicked.connect(lambda _, id=id: self.removePatient.emit(id))
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(QLabel(item_text))
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
        msg = QMessageBox()
        msg.setWindowTitle("Confirm patient removal")
        msg.setText("Are you sure that you want to remove this patient?")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        x = msg.exec()

    def update_patient_list(self):
        self.list_widget.clear()
        patient_data = get_patient_data()
        for patient in patient_data:
            id = patient["ID"]
            name = patient["Name"]
            age = patient["Age"]
            sessions = patient["Sessions"]
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
            layout.addWidget(QLabel(item_text))
            layout.addWidget(btn_see_data)
            layout.addWidget(btn_start_session)
            layout.addWidget(btn_remove_patient)
            container_item = QListWidgetItem()
            container_item.setSizeHint(QSize(0, 80))
            self.list_widget.addItem(container_item)
            self.list_widget.setItemWidget(container_item, widget)

class SessionWindow(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        session_info = get_patient_session(patient_id)
        name = session_info["name"]
        self.nombre = name
        n_session = session_info["n_session"]
        self.nombre_CAL = f"CAL-EEG{name}{n_session}.csv"
        self.nombre_EV = f"EV-EEG{name}{n_session}.csv"
        self.value = 0
        self.period = 1
        self.setWindowTitle(f"NeuroBack - Session Controls for {name}")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")
        plot_duration = 5
        sample_frecuency = 250
        self.plot_length = int(plot_duration * sample_frecuency)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((18, 60, 790))
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.plot_widget)
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.addLayout(h_layout)
        self.period_label = QLabel("Press Start Calibration to begin")
        v_layout.addWidget(self.period_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        v_layout.addWidget(self.progress_bar)
        btn_start_recording = QPushButton("Start Calibration", self)
        btn_start_evaluation = QPushButton("Start Evaluation", self)
        btn_stop_session = QPushButton("Stop Session", self)
        btn_calc_PAF = QPushButton("Calculate PAF", self)
        btn_conectar = QPushButton("Connect Cyton", self)
        btn_start_recording.clicked.connect(self.start)
        btn_start_evaluation.clicked.connect(self.evaluation)
        btn_stop_session.clicked.connect(self.stop)
        btn_calc_PAF.clicked.connect(self.calc_PAF)
        btn_conectar.clicked.connect(self.connect_cyton)
        self.paf_label = QLabel("PAF: ", self)
        v_layout.addWidget(self.paf_label)
        v_layout.addWidget(btn_conectar)
        v_layout.addWidget(btn_start_recording)
        v_layout.addWidget(btn_start_evaluation)
        v_layout.addWidget(btn_stop_session)
        v_layout.addWidget(btn_calc_PAF)
        wav_file = open('beep.wav', 'rb')
        self.wav_data = wav_file.read()

    def connect_cyton(self):
        self.board = initialize_board('CYTON', '/dev/ttyUSB0')

    def start(self):
        self.board.start_stream(900000)
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
        if self.period < 10:
            DataFilter.write_file(data, self.nombre_CAL, 'a')
        else:
            DataFilter.write_file(data, self.nombre_EV, 'a')
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
        new_data = self.board.get_board_data()
        n = len(new_data[0])
        new_x = np.arange(self.x[-1] + 1, self.x[-1] + 1 + n)
        new_y = new_data[1]
        self.x = np.append(self.x, new_x)
        self.y = np.append(self.y, new_y)
        if len(self.y) > self.plot_length:
            y_plot = self.y[-self.plot_length:]
            x_plot = self.x[-self.plot_length:]
        else:
            y_plot = self.y
            x_plot = self.x
        self.data_line.setData(x_plot, y_plot)
        if self.period < 10:
            DataFilter.write_file(new_data, 'CAL-EEG.csv', 'a')
        else:
            DataFilter.write_file(new_data, 'EV-EEG.csv', 'a')

    def evaluation(self):
        # Implement the evaluation method
        pass

    def calc_PAF(self):
        lab = open(self.nombre_CAL)
        datos = np.loadtxt(lab, delimiter="\t")
        datos = np.transpose(datos)
        datos = datos[1:]
        muestras = datos.shape[1]
        t = np.linspace(0, muestras / 250, muestras)
        i = 0
        eeg = np.zeros([3, muestras])
        for c in [5, 6, 7]:
            eeg[i] = datos[c]
            i += 1
        eog = np.zeros([2, muestras])
        i = 0
        for c in [1, 2]:
            eog[i] = datos[c]
            i += 1
        fs = 250
        rest = eeg[0]
        sos = signal.butter(2 ** 5, [8, 12], 'band', analog=False, fs=250, output='sos')
        s_filt = signal.sosfiltfilt(sos, rest)
        nper = int(fs * 0.75)
        f, DSP = signal.welch(s_filt, fs, noverlap=nper // 2, nperseg=nper)
        self.PAF = f[np.argmax(DSP)]
        self.paf_label.setText(f"PAF: {self.PAF:.2f}")
        print(f"La frecuencia pico es {self.PAF} Hz")

class PatientDataWindow(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle(f"NeuroBack - Data Controls for {patient_id}")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #1E3B4D; color: white;")
        self.plot_power = pg.PlotWidget()
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.plot_power)
