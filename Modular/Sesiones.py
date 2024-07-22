import sys
import sqlite3
import logging
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QMessageBox, QScrollArea
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages

logging.basicConfig(level=logging.INFO)

def save_session_data(patient_id, duration, phases_applied, record_channel, paf, powers):
    """
    Save session data to the SQLite database.

    Parameters:
    patient_id (int): ID of the patient.
    duration (float): Duration of the session.
    phases_applied (str): Phases applied during the session.
    record_channel (str): Recording channel used.
    paf (float): PAF value for the session.
    powers (str): Powers data for the session.
    """
    connection = None
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_num INTEGER PRIMARY KEY AUTOINCREMENT,
                id_patient INTEGER,
                duration FLOAT,
                phases_applied TEXT,
                record_channel TEXT,
                paf FLOAT,
                powers TEXT,
                FOREIGN KEY (id_patient) REFERENCES patients (id_patient)
            )
        """)
        
        cursor.execute("""
            INSERT INTO sessions (id_patient, duration, phases_applied, record_channel, paf, powers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, duration, phases_applied, record_channel, paf, powers))
        
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if connection:
            connection.close()

def get_sessions_by_patient_id(patient_id):
    """
    Retrieve all sessions for a given patient ID from the SQLite database.

    Parameters:
    patient_id (int): ID of the patient.

    Returns:
    list: A list of dictionaries containing session data.
    """
    connection = None
    sessions = []
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT session_num, id_patient, duration, phases_applied, record_channel, paf, powers
            FROM sessions
            WHERE id_patient = ?
        """, (patient_id,))
        
        rows = cursor.fetchall()
        for row in rows:
            session = {
                "session_num": row[0],
                "id_patient": row[1],
                "duration": row[2],
                "phases_applied": row[3],
                "record_channel": row[4],
                "paf": row[5],
                "powers": row[6]
            }
            sessions.append(session)
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if connection:
            connection.close()
    
    return sessions

class SessionViewer(QWidget):
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


if __name__ == "__main__":
    # Adding sample data for patient 8
    # save_session_data(8, 5, "0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0", "4", 10.1, "0.004082134411711152, 0.7695110938511753, 0.7372126561330138, -0.2989011746274714, -1.0659529839483846, -0.36743026151189945, 0.432655067679194, 0.881032970217394, 0.38308068590185934, -0.9612280491478534")
    # save_session_data(8, 5, "0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0", "4",10.5, "0.05773737809253615, 0.9307680317320296, 0.8498866196181067, -0.16976352945653467, -0.8225495676245911, -0.7037942096738107, 0.3854010203729452, 1.1087398074189327, 0.06657036152925744, -0.6592266947778167")
    # save_session_data(8, 5, "0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0", "4", 11.4, "-0.016864093921711898, 0.9648766860850753, 0.9132425540062626, -0.32291703012713285, -0.8635658833623019, -0.4076382794745105, 0.5820762952238858, 0.7808376231201525, 0.2280014667000983, -0.6436245942499622")

    app = QApplication(sys.argv)
    viewer = SessionViewer(8)
    viewer.resize(800, 600)
    
    viewer.show()
    sys.exit(app.exec())
