from PyQt6.QtWidgets import  QMessageBox, QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QHBoxLayout, QProgressBar
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
import pyaudio
import time
import serial
import threading


