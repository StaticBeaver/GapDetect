import serial
import serial.tools.list_ports
import time
from usbprint_raw import list_usbprint_device_paths, list_usbprint_devices_with_names, RawUsbPrinter

class PrinterInterface:
    def __init__(self):
        self.connection = None
        self.conn_type = None

    @staticmethod
    def get_com_ports():
        return [port.device for port in serial.tools.list_ports.comports()]

    @staticmethod
    def get_windows_printers():
        try:
            return list_usbprint_devices_with_names()
        except Exception:
            return []

    def connect_serial(self, port, baudrate=9600):
        try:
            self.connection = serial.Serial(port, baudrate, timeout=2, write_timeout=2)
            try:
                self.connection.setDTR(True)
                self.connection.setRTS(True)
            except Exception:
                pass
            self.conn_type = 'serial'
            return True, "Connected to serial port"
        except Exception as e:
            return False, str(e)

    def connect_spooler(self, device_path):
        try:
            self.connection = RawUsbPrinter(device_path)
            self.connection.open()
            self.conn_type = 'raw_usb'
            return True, "Connected directly to the USB interface (RAW). Reading enabled."
        except Exception as e:
            return False, f"USB RAW connection error: {e}"

    def send_command(self, cmd_str):
        if not self.connection:
            return False, "Not connected"
        
        cmd_str = cmd_str.replace('\\r', '\r').replace('\\n', '\n')
        if not cmd_str.endswith('\n'):
            cmd_str += '\r\n'
            
        data = cmd_str.encode('utf-8')
        try:
            if self.conn_type == 'serial':
                self.connection.write(data)
                self.connection.flush()
                return True, "Command sent."
            elif self.conn_type == 'raw_usb':
                n, err = self.connection.write(data)
                if err:
                    return False, str(err)
                return True, "Command sent."
        except serial.SerialTimeoutException:
            return False, "Write timeout (port is not responding)"
        except Exception as e:
            return False, str(e)

    def read_response(self):
        if not self.connection:
            return ""
        
        if self.conn_type == 'serial':
            try:
                time.sleep(0.2) 
                response = b""
                while True:
                    chunk = self.connection.read_all()
                    if chunk:
                        response += chunk
                        time.sleep(0.1)
                    else:
                        break
                if not response:
                    return ""
                return response.decode('utf-8', errors='ignore')
            except Exception as e:
                return f"Read error: {e}"
        elif self.conn_type == 'raw_usb':
            try:
                full_data = b""
                # The first read should wait longer for the printer to start
                # responding (there may be a flash/EEPROM read delay); later
                # reads use a short timeout just to detect that the data has
                # ended.
                timeout = 2.5
                while True:
                    data, err = self.connection.read(1024, timeout=timeout)
                    if data:
                        full_data += data
                        timeout = 0.2
                    else:
                        break

                if full_data:
                    return full_data.decode('utf-8', errors='ignore')
                # No data arrived (timeout or another read error) - instead of
                # passing this up as fake "data", return empty so the UI shows
                # the correct "could not read" warning.
                return ""
            except Exception as e:
                return f"Unexpected read error: {e}"
            
    def close(self):
        if self.connection:
            if self.conn_type == 'serial':
                self.connection.close()
            elif self.conn_type == 'raw_usb':
                self.connection.close()
        self.connection = None
