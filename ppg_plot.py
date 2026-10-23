import csv
import sys
import time
from datetime import datetime
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QGroupBox, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
)
import matplotlib.backends.backend_qt5agg as qt_agg
from matplotlib.figure import Figure
import serial

MODERN_STYLE = """
QWidget {
    background-color: #1E1E2E;
    color: #CDD6F4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}
QGroupBox {
    border: 2px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #89B4FA;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 5px;
    padding: 6px;
    color: #CDD6F4;
}
QPushButton {
    background-color: #89B4FA;
    color: #1E1E2E;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover { background-color: #B4BEFE; }
QPushButton:disabled { background-color: #45475A; color: #A6ADC8; }
#recordBtn { background-color: #F38BA8; }
#recordBtn:hover { background-color: #EBA0AC; }
#recordBtn[recording="true"] { background-color: #A6E3A1; }
#recordBtn[recording="true"]:hover { background-color: #94E2D5; }
"""

class PPGRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.is_recording = False
        self.csv_file = None
        self.csv_writer = None
        self.sample_count = 0
        self.start_time = None
        self.duration_limit_sec = 0

        # Buffer for incomplete serial lines
        self.serial_buffer = ""

        # Hz Calculation
        self.last_hz_check = time.time()
        self.hz_sample_counter = 0

        self.ir_data = []
        self.red_data = []
        self.max_points = 300

        self.init_ui()

        # Fast Timer for Serial Data Reading (10 ms / 100 Hz polling)
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.read_serial_data)

        # Separate Slow Timer for Plot Redrawing (50 ms / 20 FPS to prevent GUI lag)
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(50)

    def init_ui(self):
        self.setWindowTitle('MAX30102 PPG Recorder')
        self.resize(1050, 700)
        self.setStyleSheet(MODERN_STYLE)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Connection & Recording Header
        top_layout = QHBoxLayout()

        conn_group = QGroupBox("Hardware Connection")
        conn_layout = QGridLayout()
        self.port_input = QLineEdit('/dev/ttyACM0')
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.conn_status = QLabel('⬤ Disconnected')
        self.conn_status.setStyleSheet("color: #F38BA8; font-weight: bold;")
        
        conn_layout.addWidget(QLabel('Port:'), 0, 0)
        conn_layout.addWidget(self.port_input, 0, 1)
        conn_layout.addWidget(self.connect_btn, 0, 2)
        conn_layout.addWidget(self.conn_status, 1, 0, 1, 3)
        conn_group.setLayout(conn_layout)

        rec_group = QGroupBox("Recording Settings")
        rec_layout = QGridLayout()
        
        self.path_input = QLineEdit(f"ppg_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        self.browse_btn = QPushButton('Browse')
        self.browse_btn.clicked.connect(self.browse_file)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["Continuous", "1 Minute", "2 Minutes", "5 Minutes"])
        
        self.record_btn = QPushButton('START RECORDING')
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setProperty("recording", "false")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self.toggle_recording)

        rec_layout.addWidget(QLabel('Save To:'), 0, 0)
        rec_layout.addWidget(self.path_input, 0, 1)
        rec_layout.addWidget(self.browse_btn, 0, 2)
        rec_layout.addWidget(QLabel('Duration:'), 1, 0)
        rec_layout.addWidget(self.duration_combo, 1, 1)
        rec_layout.addWidget(self.record_btn, 1, 2)
        rec_group.setLayout(rec_layout)

        top_layout.addWidget(conn_group, 1)
        top_layout.addWidget(rec_group, 2)
        main_layout.addLayout(top_layout)

        # Matplotlib Canvas
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor('#1E1E2E')
        self.canvas = qt_agg.FigureCanvasQTAgg(self.fig)
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#181825')
        self.ax.tick_params(colors='#CDD6F4')
        for spine in self.ax.spines.values():
            spine.set_color('#45475A')
            
        self.ir_line, = self.ax.plot([], [], label='IR Channel', color='#89B4FA', linewidth=1.5)
        self.red_line, = self.ax.plot([], [], label='Red Channel', color='#F38BA8', linewidth=1.5)
        self.ax.legend(loc='upper right', facecolor='#313244', edgecolor='#45475A', labelcolor='#CDD6F4')
        self.fig.tight_layout()

        main_layout.addWidget(self.canvas, 1)

        # Live Telemetry Layout
        telemetry_layout = QHBoxLayout()
        self.samples_label = QLabel('SAMPLES: 0')
        self.samples_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #A6ADC8;")
        
        self.hz_label = QLabel('RATE: 0.0 Hz')
        self.hz_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #89B4FA;")

        self.timer_label = QLabel('ELAPSED: 00:00')
        self.timer_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #A6ADC8;")
        self.timer_label.setAlignment(Qt.AlignRight)

        telemetry_layout.addWidget(self.samples_label)
        telemetry_layout.addWidget(self.hz_label)
        telemetry_layout.addWidget(self.timer_label)
        main_layout.addLayout(telemetry_layout)

        self.setLayout(main_layout)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_input.text().strip()
        try:
            # Open serial port with minimal timeout for high throughput
            self.ser = serial.Serial(port, 115200, timeout=0.005)
            self.conn_status.setText(f'⬤ Connected to {port}')
            self.conn_status.setStyleSheet("color: #A6E3A1; font-weight: bold;")
            self.connect_btn.setText('Disconnect')
            self.record_btn.setEnabled(True)
            self.port_input.setEnabled(False)
            self.serial_buffer = ""
            self.data_timer.start(10)
        except Exception as e:
            self.conn_status.setText('⬤ Connection Failed')
            self.conn_status.setStyleSheet("color: #F38BA8; font-weight: bold;")

    def disconnect_serial(self):
        if self.is_recording:
            self.toggle_recording()
        if self.ser:
            self.data_timer.stop()
            self.ser.close()
        self.conn_status.setText('⬤ Disconnected')
        self.conn_status.setStyleSheet("color: #F38BA8; font-weight: bold;")
        self.connect_btn.setText('Connect')
        self.record_btn.setEnabled(False)
        self.port_input.setEnabled(True)

    def browse_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save CSV Log', '', 'CSV Files (*.csv)')
        if filename:
            if not filename.endswith('.csv'):
                filename += '.csv'
            self.path_input.setText(filename)

    def toggle_recording(self):
        if not self.is_recording:
            try:
                filepath = self.path_input.text().strip()
                self.csv_file = open(filepath, mode='w', newline='')
                self.csv_writer = csv.writer(self.csv_file)
                self.csv_writer.writerow(['Timestamp', 'IR', 'Red'])

                idx = self.duration_combo.currentIndex()
                limits = [0, 60, 120, 300]
                self.duration_limit_sec = limits[idx]

                self.is_recording = True
                self.sample_count = 0
                self.start_time = datetime.now()
                
                self.record_btn.setProperty("recording", "true")
                self.record_btn.style().unpolish(self.record_btn)
                self.record_btn.style().polish(self.record_btn)
                self.record_btn.setText('STOP RECORDING')
                
                self.path_input.setEnabled(False)
                self.browse_btn.setEnabled(False)
                self.duration_combo.setEnabled(False)
                self.timer_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #F38BA8;")
            except Exception as e:
                print(f"Error opening CSV file: {e}")
        else:
            self.is_recording = False
            if self.csv_file:
                self.csv_file.close()
            
            self.record_btn.setProperty("recording", "false")
            self.record_btn.style().unpolish(self.record_btn)
            self.record_btn.style().polish(self.record_btn)
            self.record_btn.setText('START RECORDING')
            
            self.path_input.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.duration_combo.setEnabled(True)
            self.timer_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #A6ADC8;")

    def read_serial_data(self):
        if not self.ser or not self.ser.is_open:
            return

        # Check Elapsed Timer
        if self.is_recording and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            mins, secs = divmod(int(elapsed), 60)
            self.timer_label.setText(f"ELAPSED: {mins:02d}:{secs:02d}")

            if self.duration_limit_sec > 0 and elapsed >= self.duration_limit_sec:
                self.toggle_recording()

        # Read Raw Bytes into Buffer
        try:
            waiting_bytes = self.ser.in_waiting
            if waiting_bytes > 0:
                raw_data = self.ser.read(waiting_bytes).decode('utf-8', errors='ignore')
                self.serial_buffer += raw_data

                # Extract complete lines separated by '\n'
                while '\n' in self.serial_buffer:
                    line, self.serial_buffer = self.serial_buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(',')
                    if len(parts) == 2:
                        try:
                            ir_val = int(parts[0])
                            red_val = int(parts[1])

                            # Rate calculation
                            self.hz_sample_counter += 1

                            if self.is_recording and self.csv_writer:
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                self.csv_writer.writerow([timestamp, ir_val, red_val])
                                self.sample_count += 1
                                self.samples_label.setText(f'SAMPLES: {self.sample_count}')

                            self.ir_data.append(ir_val)
                            self.red_data.append(red_val)

                            if len(self.ir_data) > self.max_points:
                                self.ir_data.pop(0)
                                self.red_data.pop(0)
                        except ValueError:
                            pass # Skip single corrupted packet without aborting

            # Update Live Hz Counter every 1 second
            now = time.time()
            dt = now - self.last_hz_check
            if dt >= 1.0:
                hz = self.hz_sample_counter / dt
                self.hz_label.setText(f"RATE: {hz:.1f} Hz")
                self.hz_sample_counter = 0
                self.last_hz_check = now

        except Exception as e:
            print(f"Serial Read Error: {e}")

    def update_plot(self):
        """Separate 20 FPS timer callback for rendering chart"""
        if len(self.ir_data) > 0:
            x_vals = list(range(len(self.ir_data)))
            self.ir_line.set_data(x_vals, self.ir_data)
            self.red_line.set_data(x_vals, self.red_data)

            self.ax.set_xlim(0, self.max_points)
            c_min = min(min(self.ir_data), min(self.red_data))
            c_max = max(max(self.ir_data), max(self.red_data))
            margin = (c_max - c_min) * 0.1 if c_max != c_min else 1
            self.ax.set_ylim(c_min - margin, c_max + margin)
            
            # Non-blocking redraw
            self.canvas.draw_idle()

    def closeEvent(self, event):
        if self.is_recording and self.csv_file:
            self.csv_file.close()
        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PPGRecorderApp()
    window.show()
    sys.exit(app.exec_())