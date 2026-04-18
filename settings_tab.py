from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
#this file should make the elements in the "settings_tabWidget" functional
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QSlider, QLineEdit, QHBoxLayout, QPushButton, QRadioButton, QMessageBox, QFileDialog, QTabWidget, QLabel, QComboBox, QCheckBox,QSizePolicy
from PyQt5 import uic, QtWidgets
import serial.tools.list_ports
import time
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainter, QBrush, QPen
from PyQt5 import QtTest

import argparse
import json
import os

import cv2
import numpy as np
# start by importing the necessary packages
import matplotlib.pyplot as plt
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QImage
import pyautogui
import sys
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider,QLineEdit, QHBoxLayout, QPushButton, QRadioButton, QMessageBox, QFileDialog, QTabWidget, QLabel, QComboBox,QCheckBox
from PyQt5 import uic
import serial.tools.list_ports
import time
#from moving_fun import fun_testEachAxisMoveLoop
from PyQt5 import QtTest

import sys
from pyMcc import MoCtrlCard
import time


from window_interaction_handler import WindowInteractionHandler
from temprature_control import TemperatureController
from pyMcc import MoCtrlCard

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("settings_tab.ui", self)

        #T for temprature, M for motion

        ######## Temprature controller init ##########
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.combo_connect_T.addItems(ports)
        self.push_connect_T.clicked.connect(self.connect_T_device)
        self.temperature_controller = None  # won't be None once connected
        self.push_setT.clicked.connect(self.set_T_as_txt)

        ####### Motion cpntroller init #######
        self.mccard = MoCtrlCard()
        self.combo_connect_M.addItems(ports)
        self.push_connect_M.clicked.connect(self.connect_M_device)
        self.motion_controller = None  # won't be None once connected
        self.xp.pressed.connect(self.xpf)
        self.xm.pressed.connect(self.xmf)
        self.yp.pressed.connect(self.ypf)
        self.ym.pressed.connect(self.ymf)
        self.zp.pressed.connect(self.zpf)
        self.zm.pressed.connect(self.zmf)
        self.ap.pressed.connect(self.apf)
        self.am.pressed.connect(self.amf)
        self.bp.pressed.connect(self.bpf)
        self.bm.pressed.connect(self.bmf)
        self.cp.pressed.connect(self.cpf)
        self.cm.pressed.connect(self.cmf)
        self.xp.released.connect(self.button_released)
        self.xm.released.connect(self.button_released)
        self.yp.released.connect(self.button_released)
        self.ym.released.connect(self.button_released)
        self.zp.released.connect(self.button_released)
        self.zm.released.connect(self.button_released)
        self.ap.released.connect(self.button_released)
        self.am.released.connect(self.button_released)
        self.bp.released.connect(self.button_released)
        self.bm.released.connect(self.button_released)
        self.cp.released.connect(self.button_released)
        self.cm.released.connect(self.button_released)

        #self.push_show_coords.pressed.connect(self.show_coords)

        QtTest.QTest.qWait(200)
        
    def show_coords(self):
        ret, pos = self.mccard.MoCtrCard_GetAxisPos(2)
        print(pos)
        if ret == self.mccard.FUNRESOK:
            return pos[0], pos[1], pos[2]
        else:
            print("Failed to get position")
            return None, None, None

    def connect_T_device(self):
        try:
            comPort=self.combo_connect_T.currentText()
            self.temperature_controller=TemperatureController(com=comPort)
            self.TController_status.setText("Connected")
            print(f"Successfully connected to temprature control card on {comPort}")
        except:
            self.TController_status.setText("Error!")

    def get_temperature(self): #
        if self.temperature_controller:
            return self.temperature_controller.get_temperature()
        return None

    def set_temperature(self, value):
        if self.temperature_controller:
            self.temperature_controller.set_temperature(value)

    def set_T_as_txt(self):
        self.set_temperature(value=float(self.setT_txt.toPlainText()))

    ######### Motion Controller ########
    def connect_M_device(self):
        print("b")
        comPort=self.combo_connect_M.currentText()
        if self.mccard.MoCtrCard_Initial(comPort) == self.mccard.FUNRESERR:
            print(f"Failed to initialize motion control card on {comPort}!")
            self.MController_status.setText("Error!")
            sys.exit(1)
        print(f"Successfully connected to motion control card on {comPort}")
        self.MController_status.setText("Connected")
    def xpf(self):
        speed=self.x_speed_bx.value()
        self.AXIS_ID=0
        self.mccard.MoCtrCard_MCrlAxisRelMove(0,1000,speed,0)
        self.show_coords()
        #if the speed is more than  3 times larger the distance it will not wrk
    def xmf(self):
        self.AXIS_ID=0
        speed=self.x_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(0,-1000,speed,0)
    def ypf(self):
        self.AXIS_ID=1
        speed=self.y_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(1,1000,speed,0)
    def ymf(self):
        self.AXIS_ID=1
        speed=self.y_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(1,-1000,speed,0)
    def zpf(self):
        self.AXIS_ID=2
        speed=self.z_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(2,1000,speed,0)
    def zmf(self):
        self.AXIS_ID=2
        speed=self.z_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(2,-1000,speed,0)

    def apf(self):
        speed=self.a_speed_bx.value()
        self.AXIS_ID=3
        self.mccard.MoCtrCard_MCrlAxisRelMove(3,1000,speed,0)
    def amf(self):
        self.AXIS_ID=3
        speed=self.a_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(3,-1000,speed,0)
    def bpf(self):
        self.AXIS_ID=4
        speed=self.b_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(4,1000,speed,0)
    def bmf(self):
        self.AXIS_ID=4
        speed=self.b_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(4,-1000,speed,0)
    def cpf(self):
        self.AXIS_ID=5
        speed=self.c_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(5,1000,speed,0)
    def cmf(self):
        self.AXIS_ID=5
        speed=self.c_speed_bx.value()
        self.mccard.MoCtrCard_MCrlAxisRelMove(5,-1000,speed,0)

    def button_released(self):
        # Stop the motion when button is released
        self.mccard.MoCtrCard_StopAxisMov(self.AXIS_ID,0)