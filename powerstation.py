# -*- coding: utf-8 -*-
# python 3 source code

import socket
import sys
import time
import datetime
import math
import logging as log
log.basicConfig(level=log.WARNING)
#log.basicConfig(level=log.INFO)

# import of tinkerforge modules
from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.brick_master import Master
from tinkerforge.bricklet_lcd_20x4 import LCD20x4
from tinkerforge.bricklet_voltage_current import VoltageCurrent



class PowerStation:
    HOST = "localhost"
    PORT = 4223

    # power measurement settings
    # interval in milli seconds
    INTERVAL = 2000

    ipcon = None
    lcd = None
    iuw = None

    filename = "power_measurements_%s.csv" % str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S'))

    def __init__(self):
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(PowerStation.HOST, PowerStation.PORT)
                break
            except Error as e:
                log.error('Connection Error: ' + str(e.description))
                time.sleep(1)
            except socket.error as e:
                log.error('Socket Error:' + str(e))
                time.sleep(1)
                
        # callback for bricklet registration
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE,
                                     self.cb_enumerate)
        # callback for master brick connection
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED,
                                     self.cb_connected)

        
        
        while True:
            try:
                self.ipcon.enumerate()
                break
            except Error as e:
                log.error('Enumerate Error: ' + str(e.description))
                time.sleep(1)

    def cb_enumerate(self, uid, connected_uid, position, hardware_version,
                     firmware_version, device_identifier, enumeration_type):
       log.info('callback enumerate called!')
       log.info('enum type: ' + str(enumeration_type))
       if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            log.info('enumeration type is correct!')
            if device_identifier == LCD20x4.DEVICE_IDENTIFIER:
                log.info('found LCD')
                try:
                    self.lcd = LCD20x4(uid, self.ipcon)
                    self.lcd.clear_display()
                    self.lcd.backlight_on()
                    log.info('LCD 20x4 initialized')
                except Error as e:
                    log.error('LCD 20x4 init failed: ' + str(e.description))
                    self.lcd = None
            elif device_identifier == VoltageCurrent.DEVICE_IDENTIFIER:
                log.info('found voltagecurrent bricklet')
                try:
                    self.iuw = VoltageCurrent(uid, self.ipcon)
                    # TODO
                    self.iuw.set_current_callback_period(self.INTERVAL)
                    self.iuw.register_callback(self.iuw.CALLBACK_CURRENT, self.cb_current)
                    #set_voltage_callback_period(self.INTERVAL)
                    #set_power_callback_period(self.INTERVAL)
                    log.info('I-U-W Bricklet initalized')
                except Error as e:
                    log.error('I-U-W Bricklet init failed: ' + str(e.description))
                    self.iuw = None
            
    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')
            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate Error: ' + str(e.description))
                    time.sleep(1)

    def cb_current(self, current):
        self.read_all_power_values()

    def cb_voltage(self, voltage):
        pass
    def cv_power(self, power):
        pass

    def read_all_power_values(self):
        ts = time.time()
        current = self.iuw.get_current()
        voltage = self.iuw.get_voltage()
        power = self.iuw.get_power()
        log.info('current: ' + str(current))
        log.info('voltage: ' + str(voltage))
        log.info('power: ' + str(power))
        self.lcd.write_line(0,0,'%s' % str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')))
        text = 'Current: %d mA' % (current)
        self.lcd.write_line(1, 0, text)
        text = 'Voltage: %d mV' % (voltage)
        self.lcd.write_line(2, 0, text)
        text = 'Power: %d mW' % (power)
        self.lcd.write_line(3, 0, text)
        with open (self.filename, 'a') as f:
            f.write('%s;%s;%s;%s\n' % (str(ts), str(current), str(voltage), str(power)))

def main():
    log.info("Power Station is starting...")

    power_station = PowerStation()
    
    #input('Press key to exit\n')

    #if power_station.ipcon != None:
    #    power_station.ipcon.disconnect()

    log.info('Power Station: End')

if __name__ == "__main__":
    main()
