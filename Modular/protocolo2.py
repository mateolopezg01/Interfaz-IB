from serial.tools import list_ports


# Identify the correct port
ports = list_ports.comports()
for port in ports: print(str(port))