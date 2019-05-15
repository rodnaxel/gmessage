# -*- coding: utf-8 -*-

import json
import os.path
import sys
import logging

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import app_rc

import model
from mywidgets import SpinDial

__title__ = "Генератор сообщений"
__version__ = "0.1.0"
__author__ = "Александр Смирнов"    


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        #logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
        logging.StreamHandler()
    ])
logger = logging.getLogger()


class Ui(QMainWindow):
    def __init__(self):
        super().__init__()

        self.model = model.Model()

        self.timer_id = 0
        self.isBlink = False
        self.status = {}

        self.createUI()

        # Connect signal/slot
        self.degausbox_widgets['channels'].currentTextChanged['QString'].connect(self._on_change_degaus_channels)
        self.degausbox_widgets['imax'].currentTextChanged['QString'].connect(self._on_change_degaus_imax)

    def _center(self):
        """ This method aligned main window related center screen """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def createUI(self):
        self.setWindowTitle("{0} (версия {1})".format(__title__, __version__))
        self.setWindowIcon(QIcon(":/rc/logo.png"))
        self.setMaximumSize(800, 500)
        
        centralWgt = QWidget(self)
        self.setCentralWidget(centralWgt)
        self.createStatusbar()

        # Create widgets        
        self.portbox = self.createPortbox()
        self.degausbox = self.createDegausBox()
        self.control = self.createButtons()

        user_group = QGroupBox("Пользовательские каналы", self)
        self.spindials = [SpinDial(initial=i) for i in range(4)]

        other_group = QGroupBox("Остальные", self)
        self.spindials.append(SpinDial(is_combo=False))

        # Layouts
        centralLayout = QVBoxLayout(centralWgt)
        
        settingsLayout = QHBoxLayout()
        settingsLayout.addWidget(self.portbox)
        settingsLayout.addWidget(self.degausbox, 2)
        centralLayout.addLayout(settingsLayout)

        user_layout = QHBoxLayout(user_group)
        for wgt in self.spindials[:-1]:
            user_layout.addWidget(wgt)

        other_layout = QHBoxLayout(other_group)
        other_layout.addWidget(self.spindials[-1])

        data_layout = QHBoxLayout()
        data_layout.addWidget(user_group)
        data_layout.addWidget(other_group)

        centralLayout.addLayout(data_layout)

        centralLayout.addWidget(self.control)

        self._center()
        self.show()

    def createButtons(self):
        wgt = QWidget()
        layout = QHBoxLayout(wgt)

        self.buttons = {}
        for (name, key, enabled, action, icon) in (
                ('старт', 'start', True, self._on_start, ':/rc/red-start.png'),
                ('стоп', 'stop',  False, self._on_stop, ':/rc/red-stop.png'),
                ('сброс', 'reset', True, self._on_reset, ':/rc/red-stop.png'),
                ('справка', 'about',  True, None, ':/rc/red-about.png'),
                ('выход', 'exit', True, self._on_quit, ':/rc/red-quit.png')
        ):
            button = QPushButton(name.capitalize())
            button.setEnabled(enabled)
            button.setFixedSize(80, 25)
            
            if icon: 
                button.setIcon(QIcon(icon))
            
            button.setStyleSheet("text-align: left")
            
            if action:
                button.clicked.connect(action)

            layout.addWidget(button)
            layout.setSpacing(1)

            self.buttons[key] = button
        return wgt

    def createPortbox(self):
        """ Port configuration"""
        wgt = QGroupBox('Настройки порта', self)
        layout = QGridLayout(wgt)

        # Port name
        name = QComboBox()
        name.setObjectName("name")
        name.setFixedWidth(60)
        
        if available_ports:
            name.addItems(available_ports)
        else:
            name.setDisabled(True)

        btnRescan = QPushButton("Обновить")
        btnRescan.setFixedWidth(60)
        #btnRescan.setIcon(QIcon('rc/magnifier.png'))

        layout.addWidget(QLabel('Порт:'), 0, 0)
        layout.addWidget(name, 0, 1)
        layout.addWidget(btnRescan, 0, 2)

        # Baudrate
        bd = QComboBox()
        bd.setObjectName("baudrate")
        bd.addItems(cfg['port']['baudrates'])
        bd.setCurrentText("9600")
        bd.setFixedWidth(name.width())

        layout.addWidget(QLabel("Скорость:"), 1, 0)
        layout.addWidget(bd, 1, 1)

        layout.setColumnStretch(2, 2)
        layout.setRowStretch(3, 2)

        # Slots
        def _update_data():
            self.portbox_data = { "name": wgt.findChild(QComboBox, "name").currentText(),
                                  "baudrate": int(wgt.findChild(QComboBox, "baudrate").currentText())
            }

        def _on_find_ports():
            name.clear()
            name.addItems(model.serial_ports())

        # Connect signal/slot
        name.currentTextChanged['QString'].connect(_update_data)
        bd.currentTextChanged['QString'].connect(_update_data)
        btnRescan.clicked.connect(_on_find_ports)

        _update_data()

        return wgt
    
    def createDegausBox(self):
        """
        Widget degaus settings
        """
        wgt = QGroupBox('Настройки сообщения', self)
        layout = QGridLayout(wgt)

        # Slot
        def _update_data():
            self.degausbox_data = {
                "header": wgt.findChild(QComboBox, 'header').currentText(),
                "channels": int(wgt.findChild(QComboBox,'channels').currentText()),
                "channels_byte": bool(wgt.findChild(QCheckBox,'channels_byte').checkState()),
                "imax": int(wgt.findChild(QComboBox,'imax').currentText()),
                "imax_byte": bool(wgt.findChild(QCheckBox,'imax_byte').checkState()),
                "interval": int(wgt.findChild(QComboBox, 'interval').currentText())
            }
            print(self.degausbox_data)        

        # Create widgets
        self.degausbox_widgets = {} 
        row, col = (0,0)
        for key, name, items in (
                ('header', 'заголовок', cfg['degaus']['headers']),
                ('channels', 'каналы', cfg['degaus']['channels']),
                ('imax', 'макс. ток, а', cfg['degaus']['currents']),
                ('interval', 'интервал, мс', cfg['degaus']['interval'])
        ):
            combo = QComboBox()
            combo.setObjectName(key)
            combo.setFixedWidth(65)
            combo.addItems(items)
            combo.setStyleSheet("text-align: right") 

            # Signal/Slot
            combo.currentTextChanged['QString'].connect(_update_data)
            layout.addWidget(QLabel(name.capitalize() + ":"), row, 0)
            layout.addWidget(combo, row, 1)

            self.degausbox_widgets[key] = combo

            # If check byte include in header message
            if key in ['channels', 'imax']:
                check = QCheckBox("Доп. байт")
                check.setObjectName("{}_byte".format(key))
                if key == "channels":
                    check.setChecked(True)
                layout.addWidget(check, row, 2)
                check.stateChanged['int'].connect(_update_data)
                self.degausbox_widgets["{}_byte".format(key)] = check
                
            layout.setColumnStretch(2, 2)
            row += 1

        _update_data()

        return wgt

    def createStatusbar(self):
        '''
        for (key, text) in (
                ['tx', 'сообщений'],
        ):
            wgt = QLabel(' {}: {}'.format(text, 0))
            wgt.setFixedWidth(90)
            stretch = 2 if key == 'er' else 0
            self.statusBar().addPermanentWidget(wgt, stretch)
            self.status[key] = wgt
        '''
        pix = QLabel()
        self.statusBar().addPermanentWidget(pix)
        self.status['pixmap'] = pix
        self.updatePixmap('noconnect')

    def _on_change_degaus_channels(self, text):
        for wgt in self.spindials[:-1]:
            wgt.set_number_channels(int(text))

    def _on_change_degaus_imax(self, text):
        for wgt in self.spindials:
            wgt.set_range(int(text))

    def _on_start(self):
        self._lock(True)
        logger.info(self.portbox_data)
        logger.info(self.degausbox_data)
        self.databox_data = self.get_data()
        self.model.configure(self.portbox_data, self.degausbox_data, self.databox_data)
        self.timer_id = self.startTimer(1000, timerType=QtCore.Qt.PreciseTimer)

    def _on_stop(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
            self.timer_id = 0
        self.model.disconnect()
        self._lock(False)
        self.message_count = 0
        self.updatePixmap('idle')

    def _on_reset(self):
        for wgt in self.spindials:
            wgt.set_value(0)

    def _on_quit(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
        QtCore.QCoreApplication.exit(0)

    def closeEvent(self, event):
        self._on_quit()

    def timerEvent(self, event):
        data = self.get_data()
        self.model.send(data)
        self.blinkPixmap()

    def _lock(self, is_lock):
        self.portbox.setDisabled(is_lock)
        self.degausbox.setDisabled(is_lock)
        self.buttons['start'].setDisabled(is_lock)
        self.buttons['stop'].setEnabled(is_lock)

    def get_data(self):
        """ The method used to get data from spindial widget"""
        *customs, other = self.spindials

        d_ = {'custom': {"channel": [wgt.channel() for wgt in customs],
                         "value": [wgt.value() for wgt in customs]},
              'other': {"channel": "other",
                        "value": other.value()}}
        return d_

    def blinkPixmap(self):
        if self.isBlink:
            self.updatePixmap('tx')
            self.isBlink = False
        else:
            self.updatePixmap('rx')
            self.isBlink = True

    def updatePixmap(self, state=None):
        if not state:
            state = "noconnect"
        pixmaps = {
            'noconnect': {'ico': ":/rc/network-offline.png", 'description': 'нет подключения'},
            'idle': {'ico': ":/rc/network-idle.png", 'description': 'ожидание'},
            'rx': {'ico': ":/rc/network-receive.png", 'description': 'прием'},
            'tx': {'ico': ":/rc/network-transmit.png", 'description': 'передача'},
            'error': {'ico': ":/rc/network-error.png", 'description': 'ошибка'}
        }
        self.status['pixmap'].setPixmap(QPixmap(pixmaps[state]['ico']))
        self.status['pixmap'].setToolTip(pixmaps[state]['description'])

    def updateStatus(self, key, value):
        self.status[key].setText(' {}: {}'.format('отп', value))


class UserialMainWindow(Ui):
    pass


if __name__ == '__main__':
    
    with open(os.path.join(PROJECT_DIR, "degaus.json")) as json_file:
        cfg = json.load(json_file)

    available_ports = model.serial_ports()

    app = QApplication(sys.argv)

    # Add icon in the taskbar (only windows))
    if sys.platform == 'win32':
        import ctypes
        myappid = u'navi-dals.kf1-m.udegausswer.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    ex = UserialMainWindow()


    sys.exit(app.exec_())
