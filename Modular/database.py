import sqlite3
import logging

def save_patient_data(name, age, treatment, sessions):
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id_patient INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                treatment TEXT,
                sessions INTEGER
            )
        """)
        cursor.execute("INSERT INTO patients (name, age, treatment, sessions) VALUES (?, ?, ?, ?)", (name, age, treatment, sessions))
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {name}(session_num INTEGER PRIMARY KEY AUTOINCREMENT,PAF FLOAT,cal_route TEXT,ev_route TEXT)")
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

def get_patient_data():
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM patients")
        patient_data = []
        for row in cursor.fetchall():
            id = row[0]
            name = row[1]
            age = row[2]
            treatment = row[3]
            sessions = row[4]
            patient_data.append({"ID": id, "Name": name, "Age": age, "Treatment": treatment, "Sessions": sessions})
        cursor.close()
        connection.close()
        return patient_data
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return []

def delete_patient_data(patient_id):
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        cursor.execute("DELETE FROM patients WHERE id_patient=?", (patient_id,))
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")


def get_patient_session(patient_id):
    try:
        connection = sqlite3.connect("patient_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM patients WHERE id_patient=?", (patient_id,))
        row = cursor.fetchone()
        id = row[0]
        name = row[1]
        sessions = row[4]
        cursor.execute(f"SELECT * FROM {name} ORDER BY session_num DESC LIMIT 1")
        registro = cursor.fetchone()
        n_session = registro[0] + 1 if registro else 1
        connection.commit()
        connection.close()
        return {"name": name, "n_session": n_session}
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {"name": "", "n_session": 1}
    

def save_session_data(patient_id, duration, phases_applied, record_channel):
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
                FOREIGN KEY (id_patient) REFERENCES patients (id_patient)
            )
        """)
        cursor.execute("INSERT INTO sessions (id_patient, duration, phases_applied, record_channel) VALUES (?, ?, ?, ?)", 
                       (patient_id, duration, phases_applied, record_channel))
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
