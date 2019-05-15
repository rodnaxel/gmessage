# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class SpinDial(QWidget):
	def __init__(self, initial=1,is_combo=True, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.is_combo = is_combo
		self.initial_channel = initial
		self._range = (-9.99, 9.99)

		self._value = 0
		self._channel = 43

		self._createUi()

	def channel(self):
		return int(self.combo.currentText())

	def value(self):
		return self.dial.value()

	def set_value(self, value):
		self.dial.setValue(value)

	def set_range(self, value):
		min, max = -float(value), float(value)
		self.dspin.setRange(min, max)
		self.dial.setRange(min * 100, max * 100)

	def set_number_channels(self, value):
		self.combo.clear()
		self.combo.addItems([str(i) for i in range(1, value + 1)])

	def _createUi(self):
		vbox = QVBoxLayout(self)

		# Channel
		self.combo = combo = QComboBox()

		combo.setFixedWidth(60)
		combo.addItems([str(i) for i in range(1, self._channel+1)])
		combo.setCurrentIndex(self.initial_channel)

		# Spinbox
		self.dspin = dspin = QDoubleSpinBox()
		dspin.setRange(-10.0, 10.0)
		dspin.setSingleStep(0.1)
		dspin.setFixedWidth(combo.width())

		# Dial
		self.dial = dial = QDial()
		dial.setFixedWidth(combo.width())
		dial.setRange(-999, 999)
		dial.setSingleStep(10)
		dial.setNotchesVisible(True)

		# Layout
		vbox.setAlignment(QtCore.Qt.AlignCenter)

		if not self.is_combo:
			combo.setVisible(False)
			vbox.addStretch(2)

		vbox.setSpacing(1)
		vbox.addWidget(combo)
		vbox.addWidget(dial)
		vbox.addWidget(dspin)

		# Connect signal/slot
		dial.valueChanged.connect(self._on_change_spin)
		dspin.valueChanged.connect(self._on_change_dial)
		combo.currentIndexChanged['int'].connect(self._on_select_channel)

	def _on_change_spin(self):
		self.dspin.setValue(self.dial.value() / 100)

	def _on_change_dial(self):
		self.dial.setValue(self.dspin.value() * 100)

	def _on_select_channel(self):
		if not self.combo.count():
			return
		self._channel = int(self.combo.currentText())

