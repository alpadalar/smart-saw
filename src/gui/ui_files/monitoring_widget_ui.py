# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monitoring_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1920, 1080)
        self.Container_3 = QFrame(Form)
        self.Container_3.setObjectName(u"Container_3")
        self.Container_3.setGeometry(QRect(1033, 127, 857, 281))
        self.Container_3.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_3.setFrameShape(QFrame.StyledPanel)
        self.Container_3.setFrameShadow(QFrame.Raised)
        self.FrameMalzemeCinsi = QFrame(self.Container_3)
        self.FrameMalzemeCinsi.setObjectName(u"FrameMalzemeCinsi")
        self.FrameMalzemeCinsi.setGeometry(QRect(20, 27, 260, 105))
        self.FrameMalzemeCinsi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMalzemeCinsi.setFrameShape(QFrame.StyledPanel)
        self.FrameMalzemeCinsi.setFrameShadow(QFrame.Raised)
        self.labelMalzemeCinsi = QLabel(self.FrameMalzemeCinsi)
        self.labelMalzemeCinsi.setObjectName(u"labelMalzemeCinsi")
        self.labelMalzemeCinsi.setGeometry(QRect(33, 20, 201, 20))
        self.labelMalzemeCinsi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelMalzemeCinsiValue = QLabel(self.FrameMalzemeCinsi)
        self.labelMalzemeCinsiValue.setObjectName(u"labelMalzemeCinsiValue")
        self.labelMalzemeCinsiValue.setGeometry(QRect(30, 43, 211, 50))
        font = QFont()
        font.setFamilies([u"Plus-Jakarta-Sans"])
        font.setBold(True)
        self.labelMalzemeCinsiValue.setFont(font)
        self.labelMalzemeCinsiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelMalzemeCinsiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameMalzemeSertligi = QFrame(self.Container_3)
        self.FrameMalzemeSertligi.setObjectName(u"FrameMalzemeSertligi")
        self.FrameMalzemeSertligi.setGeometry(QRect(300, 27, 260, 105))
        self.FrameMalzemeSertligi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMalzemeSertligi.setFrameShape(QFrame.StyledPanel)
        self.FrameMalzemeSertligi.setFrameShadow(QFrame.Raised)
        self.labelMalzemeSertligi = QLabel(self.FrameMalzemeSertligi)
        self.labelMalzemeSertligi.setObjectName(u"labelMalzemeSertligi")
        self.labelMalzemeSertligi.setGeometry(QRect(33, 20, 211, 31))
        self.labelMalzemeSertligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelMalzemeSertligi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelMalzemeSertligiValue = QLabel(self.FrameMalzemeSertligi)
        self.labelMalzemeSertligiValue.setObjectName(u"labelMalzemeSertligiValue")
        self.labelMalzemeSertligiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelMalzemeSertligiValue.setFont(font)
        self.labelMalzemeSertligiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelMalzemeSertligiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameKesitYapisi = QFrame(self.Container_3)
        self.FrameKesitYapisi.setObjectName(u"FrameKesitYapisi")
        self.FrameKesitYapisi.setGeometry(QRect(580, 27, 260, 105))
        self.FrameKesitYapisi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKesitYapisi.setFrameShape(QFrame.StyledPanel)
        self.FrameKesitYapisi.setFrameShadow(QFrame.Raised)
        self.labelKesitYapisi = QLabel(self.FrameKesitYapisi)
        self.labelKesitYapisi.setObjectName(u"labelKesitYapisi")
        self.labelKesitYapisi.setGeometry(QRect(33, 20, 201, 31))
        self.labelKesitYapisi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelKesitYapisi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelKesitYapisiValue = QLabel(self.FrameKesitYapisi)
        self.labelKesitYapisiValue.setObjectName(u"labelKesitYapisiValue")
        self.labelKesitYapisiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelKesitYapisiValue.setFont(font)
        self.labelKesitYapisiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelKesitYapisiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameABCD = QFrame(self.Container_3)
        self.FrameABCD.setObjectName(u"FrameABCD")
        self.FrameABCD.setGeometry(QRect(20, 154, 820, 105))
        self.FrameABCD.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameABCD.setFrameShape(QFrame.StyledPanel)
        self.FrameABCD.setFrameShadow(QFrame.Raised)
        self.labelA = QLabel(self.FrameABCD)
        self.labelA.setObjectName(u"labelA")
        self.labelA.setGeometry(QRect(24, 19, 131, 20))
        self.labelA.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelAValue = QLabel(self.FrameABCD)
        self.labelAValue.setObjectName(u"labelAValue")
        self.labelAValue.setGeometry(QRect(1, 43, 161, 50))
        self.labelAValue.setFont(font)
        self.labelAValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelAValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelB = QLabel(self.FrameABCD)
        self.labelB.setObjectName(u"labelB")
        self.labelB.setGeometry(QRect(237, 19, 131, 20))
        self.labelB.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelC = QLabel(self.FrameABCD)
        self.labelC.setObjectName(u"labelC")
        self.labelC.setGeometry(QRect(450, 19, 121, 20))
        self.labelC.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelD = QLabel(self.FrameABCD)
        self.labelD.setObjectName(u"labelD")
        self.labelD.setGeometry(QRect(663, 19, 141, 20))
        self.labelD.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBValue = QLabel(self.FrameABCD)
        self.labelBValue.setObjectName(u"labelBValue")
        self.labelBValue.setGeometry(QRect(210, 40, 161, 50))
        self.labelBValue.setFont(font)
        self.labelBValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelCValue = QLabel(self.FrameABCD)
        self.labelCValue.setObjectName(u"labelCValue")
        self.labelCValue.setGeometry(QRect(424, 40, 161, 50))
        self.labelCValue.setFont(font)
        self.labelCValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelCValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelDValue = QLabel(self.FrameABCD)
        self.labelDValue.setObjectName(u"labelDValue")
        self.labelDValue.setGeometry(QRect(640, 40, 161, 50))
        self.labelDValue.setFont(font)
        self.labelDValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelDValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.notificationFrame = QFrame(Form)
        self.notificationFrame.setObjectName(u"notificationFrame")
        self.notificationFrame.setGeometry(QRect(425, 38, 1465, 60))
        self.notificationFrame.setStyleSheet(u"QFrame#notificationFrame {\n"
"    background-color: rgba(26, 31, 55, 77);\n"
"    border-radius: 30px;\n"
"}")
        self.notificationFrame.setFrameShape(QFrame.StyledPanel)
        self.notificationFrame.setFrameShadow(QFrame.Raised)
        self.labelDate = QLabel(self.notificationFrame)
        self.labelDate.setObjectName(u"labelDate")
        self.labelDate.setGeometry(QRect(55, 13, 300, 34))
        self.labelDate.setStyleSheet(u"QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 24px;\n"
"    font-weight: light;\n"
"}\n"
"")
        self.labelTime = QLabel(self.notificationFrame)
        self.labelTime.setObjectName(u"labelTime")
        self.labelTime.setGeometry(QRect(1348, 13, 62, 34))
        self.labelTime.setStyleSheet(u"QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 24px;\n"
"    font-weight: light;\n"
"}\n"
"")
        self.Container_5 = QFrame(Form)
        self.Container_5.setObjectName(u"Container_5")
        self.Container_5.setGeometry(QRect(1033, 851, 857, 159))
        self.Container_5.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_5.setFrameShape(QFrame.StyledPanel)
        self.Container_5.setFrameShadow(QFrame.Raised)
        self.FrameKesilenParcaAdeti = QFrame(self.Container_5)
        self.FrameKesilenParcaAdeti.setObjectName(u"FrameKesilenParcaAdeti")
        self.FrameKesilenParcaAdeti.setGeometry(QRect(20, 27, 260, 105))
        self.FrameKesilenParcaAdeti.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKesilenParcaAdeti.setFrameShape(QFrame.StyledPanel)
        self.FrameKesilenParcaAdeti.setFrameShadow(QFrame.Raised)
        self.labelKesilenParcaAdeti = QLabel(self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdeti.setObjectName(u"labelKesilenParcaAdeti")
        self.labelKesilenParcaAdeti.setGeometry(QRect(33, 20, 211, 31))
        self.labelKesilenParcaAdeti.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelKesilenParcaAdeti.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelKesilenParcaAdetiValue = QLabel(self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdetiValue.setObjectName(u"labelKesilenParcaAdetiValue")
        self.labelKesilenParcaAdetiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelKesilenParcaAdetiValue.setFont(font)
        self.labelKesilenParcaAdetiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelKesilenParcaAdetiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameTestereDurum = QFrame(self.Container_5)
        self.FrameTestereDurum.setObjectName(u"FrameTestereDurum")
        self.FrameTestereDurum.setGeometry(QRect(300, 27, 260, 105))
        self.FrameTestereDurum.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTestereDurum.setFrameShape(QFrame.StyledPanel)
        self.FrameTestereDurum.setFrameShadow(QFrame.Raised)
        self.labelTestereDurum = QLabel(self.FrameTestereDurum)
        self.labelTestereDurum.setObjectName(u"labelTestereDurum")
        self.labelTestereDurum.setGeometry(QRect(33, 20, 201, 20))
        self.labelTestereDurum.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTestereDurumValue = QLabel(self.FrameTestereDurum)
        self.labelTestereDurumValue.setObjectName(u"labelTestereDurumValue")
        self.labelTestereDurumValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelTestereDurumValue.setFont(font)
        self.labelTestereDurumValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTestereDurumValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameAlarm = QFrame(self.Container_5)
        self.FrameAlarm.setObjectName(u"FrameAlarm")
        self.FrameAlarm.setGeometry(QRect(580, 27, 260, 105))
        self.FrameAlarm.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameAlarm.setFrameShape(QFrame.StyledPanel)
        self.FrameAlarm.setFrameShadow(QFrame.Raised)
        self.labelAlarm = QLabel(self.FrameAlarm)
        self.labelAlarm.setObjectName(u"labelAlarm")
        self.labelAlarm.setGeometry(QRect(33, 20, 211, 20))
        self.labelAlarm.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelAlarmValue = QLabel(self.FrameAlarm)
        self.labelAlarmValue.setObjectName(u"labelAlarmValue")
        self.labelAlarmValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelAlarmValue.setFont(font)
        self.labelAlarmValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelAlarmValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Container_2 = QFrame(Form)
        self.Container_2.setObjectName(u"Container_2")
        self.Container_2.setGeometry(QRect(425, 577, 582, 435))
        self.Container_2.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_2.setFrameShape(QFrame.StyledPanel)
        self.Container_2.setFrameShadow(QFrame.Raised)
        self.FrameSeritMotorHiz = QFrame(self.Container_2)
        self.FrameSeritMotorHiz.setObjectName(u"FrameSeritMotorHiz")
        self.FrameSeritMotorHiz.setGeometry(QRect(20, 27, 260, 105))
        self.FrameSeritMotorHiz.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorHiz.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritMotorHiz.setFrameShadow(QFrame.Raised)
        self.labelSeritMotorHiz = QLabel(self.FrameSeritMotorHiz)
        self.labelSeritMotorHiz.setObjectName(u"labelSeritMotorHiz")
        self.labelSeritMotorHiz.setGeometry(QRect(33, 20, 201, 20))
        self.labelSeritMotorHiz.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritMotorHizValue = QLabel(self.FrameSeritMotorHiz)
        self.labelSeritMotorHizValue.setObjectName(u"labelSeritMotorHizValue")
        self.labelSeritMotorHizValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritMotorHizValue.setFont(font)
        self.labelSeritMotorHizValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritMotorHizValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameInmeMotorHiz = QFrame(self.Container_2)
        self.FrameInmeMotorHiz.setObjectName(u"FrameInmeMotorHiz")
        self.FrameInmeMotorHiz.setGeometry(QRect(297, 27, 260, 105))
        self.FrameInmeMotorHiz.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorHiz.setFrameShape(QFrame.StyledPanel)
        self.FrameInmeMotorHiz.setFrameShadow(QFrame.Raised)
        self.labelInmeMotorHiz = QLabel(self.FrameInmeMotorHiz)
        self.labelInmeMotorHiz.setObjectName(u"labelInmeMotorHiz")
        self.labelInmeMotorHiz.setGeometry(QRect(33, 20, 201, 20))
        self.labelInmeMotorHiz.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelInmeMotorHizValue = QLabel(self.FrameInmeMotorHiz)
        self.labelInmeMotorHizValue.setObjectName(u"labelInmeMotorHizValue")
        self.labelInmeMotorHizValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelInmeMotorHizValue.setFont(font)
        self.labelInmeMotorHizValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelInmeMotorHizValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritMotorAkim = QFrame(self.Container_2)
        self.FrameSeritMotorAkim.setObjectName(u"FrameSeritMotorAkim")
        self.FrameSeritMotorAkim.setGeometry(QRect(20, 166, 260, 105))
        self.FrameSeritMotorAkim.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorAkim.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritMotorAkim.setFrameShadow(QFrame.Raised)
        self.labelSeritMotorAkim = QLabel(self.FrameSeritMotorAkim)
        self.labelSeritMotorAkim.setObjectName(u"labelSeritMotorAkim")
        self.labelSeritMotorAkim.setGeometry(QRect(33, 20, 211, 20))
        self.labelSeritMotorAkim.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritMotorAkimValue = QLabel(self.FrameSeritMotorAkim)
        self.labelSeritMotorAkimValue.setObjectName(u"labelSeritMotorAkimValue")
        self.labelSeritMotorAkimValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritMotorAkimValue.setFont(font)
        self.labelSeritMotorAkimValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritMotorAkimValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameInmeMotorAkim = QFrame(self.Container_2)
        self.FrameInmeMotorAkim.setObjectName(u"FrameInmeMotorAkim")
        self.FrameInmeMotorAkim.setGeometry(QRect(297, 166, 260, 105))
        self.FrameInmeMotorAkim.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorAkim.setFrameShape(QFrame.StyledPanel)
        self.FrameInmeMotorAkim.setFrameShadow(QFrame.Raised)
        self.labelInmeMotorAkim = QLabel(self.FrameInmeMotorAkim)
        self.labelInmeMotorAkim.setObjectName(u"labelInmeMotorAkim")
        self.labelInmeMotorAkim.setGeometry(QRect(33, 20, 211, 20))
        self.labelInmeMotorAkim.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelInmeMotorAkimValue = QLabel(self.FrameInmeMotorAkim)
        self.labelInmeMotorAkimValue.setObjectName(u"labelInmeMotorAkimValue")
        self.labelInmeMotorAkimValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelInmeMotorAkimValue.setFont(font)
        self.labelInmeMotorAkimValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelInmeMotorAkimValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritMotorTork = QFrame(self.Container_2)
        self.FrameSeritMotorTork.setObjectName(u"FrameSeritMotorTork")
        self.FrameSeritMotorTork.setGeometry(QRect(20, 306, 260, 105))
        self.FrameSeritMotorTork.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorTork.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritMotorTork.setFrameShadow(QFrame.Raised)
        self.labelSeritMotorTork = QLabel(self.FrameSeritMotorTork)
        self.labelSeritMotorTork.setObjectName(u"labelSeritMotorTork")
        self.labelSeritMotorTork.setGeometry(QRect(33, 20, 201, 20))
        self.labelSeritMotorTork.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritMotorTorkValue = QLabel(self.FrameSeritMotorTork)
        self.labelSeritMotorTorkValue.setObjectName(u"labelSeritMotorTorkValue")
        self.labelSeritMotorTorkValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritMotorTorkValue.setFont(font)
        self.labelSeritMotorTorkValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritMotorTorkValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameInmeMotorTork = QFrame(self.Container_2)
        self.FrameInmeMotorTork.setObjectName(u"FrameInmeMotorTork")
        self.FrameInmeMotorTork.setGeometry(QRect(297, 306, 260, 105))
        self.FrameInmeMotorTork.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorTork.setFrameShape(QFrame.StyledPanel)
        self.FrameInmeMotorTork.setFrameShadow(QFrame.Raised)
        self.labelInmeMotorTork = QLabel(self.FrameInmeMotorTork)
        self.labelInmeMotorTork.setObjectName(u"labelInmeMotorTork")
        self.labelInmeMotorTork.setGeometry(QRect(33, 20, 211, 20))
        self.labelInmeMotorTork.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelInmeMotorTorkValue = QLabel(self.FrameInmeMotorTork)
        self.labelInmeMotorTorkValue.setObjectName(u"labelInmeMotorTorkValue")
        self.labelInmeMotorTorkValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelInmeMotorTorkValue.setFont(font)
        self.labelInmeMotorTorkValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelInmeMotorTorkValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sidebarFrame = QFrame(Form)
        self.sidebarFrame.setObjectName(u"sidebarFrame")
        self.sidebarFrame.setGeometry(QRect(0, 0, 392, 1080))
        self.sidebarFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.sidebarFrame.setFrameShape(QFrame.StyledPanel)
        self.sidebarFrame.setFrameShadow(QFrame.Raised)
        self.labelSmart = QLabel(self.sidebarFrame)
        self.labelSmart.setObjectName(u"labelSmart")
        self.labelSmart.setGeometry(QRect(31, 32, 330, 73))
        self.labelSmart.setStyleSheet(u"QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"}\n"
"")
        self.labelSaw = QLabel(self.sidebarFrame)
        self.labelSaw.setObjectName(u"labelSaw")
        self.labelSaw.setGeometry(QRect(230, 32, 150, 73))
        self.labelSaw.setStyleSheet(u"QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-weight: 100\n"
";\n"
"}\n"
"")
        self.lineSmartSaw = QFrame(self.sidebarFrame)
        self.lineSmartSaw.setObjectName(u"lineSmartSaw")
        self.lineSmartSaw.setGeometry(QRect(30, 110, 332, 3))
        self.lineSmartSaw.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1: 0, y1: 0, x2: 1, y2: 0,\n"
"        stop: 0 rgba(255, 255, 255, 0),\n"
"        stop: 0.5 rgba(255, 255, 255, 100),\n"
"        stop: 1 rgba(255, 255, 255, 0)\n"
"    );\n"
"    border: none;\n"
"}\n"
"")
        self.lineSmartSaw.setFrameShadow(QFrame.Plain)
        self.lineSmartSaw.setLineWidth(1)
        self.lineSmartSaw.setFrameShape(QFrame.Shape.HLine)
        self.btnControlPanel = QPushButton(self.sidebarFrame)
        self.btnControlPanel.setObjectName(u"btnControlPanel")
        self.btnControlPanel.setGeometry(QRect(26, 165, 355, 110))
        font1 = QFont()
        font1.setFamilies([u"Plus Jakarta Sans"])
        font1.setBold(False)
        font1.setItalic(False)
        font1.setUnderline(False)
        font1.setStrikeOut(False)
        self.btnControlPanel.setFont(font1)
        self.btnControlPanel.setMouseTracking(True)
        self.btnControlPanel.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 25px;  /* simge i\u00e7in bo\u015fluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opakl\u0131k */\n"
"}")
        icon = QIcon()
        icon.addFile(u"src/gui/images/control-panel-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u"src/gui/images/control-panel-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnControlPanel.setIcon(icon)
        self.btnControlPanel.setIconSize(QSize(70, 70))
        self.btnPositioning = QPushButton(self.sidebarFrame)
        self.btnPositioning.setObjectName(u"btnPositioning")
        self.btnPositioning.setGeometry(QRect(26, 286, 355, 110))
        self.btnPositioning.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 20px;  /* simge i\u00e7in bo\u015fluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opakl\u0131k */\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u"src/gui/images/positioning-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon1.addFile(u"src/gui/images/positioning-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnPositioning.setIcon(icon1)
        self.btnPositioning.setIconSize(QSize(80, 80))
        self.btnCamera = QPushButton(self.sidebarFrame)
        self.btnCamera.setObjectName(u"btnCamera")
        self.btnCamera.setGeometry(QRect(26, 407, 355, 110))
        self.btnCamera.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 20px;  /* simge i\u00e7in bo\u015fluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opakl\u0131k */\n"
"}\n"
"")
        icon2 = QIcon()
        icon2.addFile(u"src/gui/images/camera-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon2.addFile(u"src/gui/images/camera-icon-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnCamera.setIcon(icon2)
        self.btnCamera.setIconSize(QSize(80, 80))
        self.btnSensor = QPushButton(self.sidebarFrame)
        self.btnSensor.setObjectName(u"btnSensor")
        self.btnSensor.setGeometry(QRect(26, 528, 355, 110))
        self.btnSensor.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 20px;  /* simge i\u00e7in bo\u015fluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opakl\u0131k */\n"
"}")
        icon3 = QIcon()
        icon3.addFile(u"src/gui/images/sensor-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon3.addFile(u"src/gui/images/sensor-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnSensor.setIcon(icon3)
        self.btnSensor.setIconSize(QSize(80, 80))
        self.btnTracking = QPushButton(self.sidebarFrame)
        self.btnTracking.setObjectName(u"btnTracking")
        self.btnTracking.setGeometry(QRect(27, 649, 355, 110))
        self.btnTracking.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 20px;  /* simge i\u00e7in bo\u015fluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opakl\u0131k */\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u"src/gui/images/tracking-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon4.addFile(u"src/gui/images/tracking-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnTracking.setIcon(icon4)
        self.btnTracking.setIconSize(QSize(80, 80))
        self.Container = QFrame(Form)
        self.Container.setObjectName(u"Container")
        self.Container.setGeometry(QRect(425, 127, 582, 435))
        self.Container.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container.setFrameShape(QFrame.StyledPanel)
        self.Container.setFrameShadow(QFrame.Raised)
        self.FrameMakineID = QFrame(self.Container)
        self.FrameMakineID.setObjectName(u"FrameMakineID")
        self.FrameMakineID.setGeometry(QRect(20, 27, 260, 105))
        self.FrameMakineID.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMakineID.setFrameShape(QFrame.StyledPanel)
        self.FrameMakineID.setFrameShadow(QFrame.Raised)
        self.labelMakineID = QLabel(self.FrameMakineID)
        self.labelMakineID.setObjectName(u"labelMakineID")
        self.labelMakineID.setGeometry(QRect(33, 20, 201, 20))
        self.labelMakineID.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelMakineIDValue = QLabel(self.FrameMakineID)
        self.labelMakineIDValue.setObjectName(u"labelMakineIDValue")
        self.labelMakineIDValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelMakineIDValue.setFont(font)
        self.labelMakineIDValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelMakineIDValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritID = QFrame(self.Container)
        self.FrameSeritID.setObjectName(u"FrameSeritID")
        self.FrameSeritID.setGeometry(QRect(297, 27, 260, 105))
        self.FrameSeritID.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritID.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritID.setFrameShadow(QFrame.Raised)
        self.labelSeritID = QLabel(self.FrameSeritID)
        self.labelSeritID.setObjectName(u"labelSeritID")
        self.labelSeritID.setGeometry(QRect(33, 20, 201, 20))
        self.labelSeritID.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritIDValue = QLabel(self.FrameSeritID)
        self.labelSeritIDValue.setObjectName(u"labelSeritIDValue")
        self.labelSeritIDValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritIDValue.setFont(font)
        self.labelSeritIDValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritIDValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritDisOlcusu = QFrame(self.Container)
        self.FrameSeritDisOlcusu.setObjectName(u"FrameSeritDisOlcusu")
        self.FrameSeritDisOlcusu.setGeometry(QRect(20, 166, 260, 105))
        self.FrameSeritDisOlcusu.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritDisOlcusu.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritDisOlcusu.setFrameShadow(QFrame.Raised)
        self.labelSeritDisOlcusu = QLabel(self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusu.setObjectName(u"labelSeritDisOlcusu")
        self.labelSeritDisOlcusu.setGeometry(QRect(33, 20, 201, 20))
        self.labelSeritDisOlcusu.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritDisOlcusuValue = QLabel(self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusuValue.setObjectName(u"labelSeritDisOlcusuValue")
        self.labelSeritDisOlcusuValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritDisOlcusuValue.setFont(font)
        self.labelSeritDisOlcusuValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritDisOlcusuValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritTipi = QFrame(self.Container)
        self.FrameSeritTipi.setObjectName(u"FrameSeritTipi")
        self.FrameSeritTipi.setGeometry(QRect(297, 166, 260, 105))
        self.FrameSeritTipi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritTipi.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritTipi.setFrameShadow(QFrame.Raised)
        self.labelSeritTipi = QLabel(self.FrameSeritTipi)
        self.labelSeritTipi.setObjectName(u"labelSeritTipi")
        self.labelSeritTipi.setGeometry(QRect(33, 20, 201, 20))
        self.labelSeritTipi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritTipiValue = QLabel(self.FrameSeritTipi)
        self.labelSeritTipiValue.setObjectName(u"labelSeritTipiValue")
        self.labelSeritTipiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritTipiValue.setFont(font)
        self.labelSeritTipiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritTipiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritMarkasi = QFrame(self.Container)
        self.FrameSeritMarkasi.setObjectName(u"FrameSeritMarkasi")
        self.FrameSeritMarkasi.setGeometry(QRect(20, 306, 260, 105))
        self.FrameSeritMarkasi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMarkasi.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritMarkasi.setFrameShadow(QFrame.Raised)
        self.labelSeritMarkasi = QLabel(self.FrameSeritMarkasi)
        self.labelSeritMarkasi.setObjectName(u"labelSeritMarkasi")
        self.labelSeritMarkasi.setGeometry(QRect(33, 20, 211, 20))
        self.labelSeritMarkasi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritMarkasiValue = QLabel(self.FrameSeritMarkasi)
        self.labelSeritMarkasiValue.setObjectName(u"labelSeritMarkasiValue")
        self.labelSeritMarkasiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritMarkasiValue.setFont(font)
        self.labelSeritMarkasiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritMarkasiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritMalzemesi = QFrame(self.Container)
        self.FrameSeritMalzemesi.setObjectName(u"FrameSeritMalzemesi")
        self.FrameSeritMalzemesi.setGeometry(QRect(297, 306, 260, 105))
        self.FrameSeritMalzemesi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMalzemesi.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritMalzemesi.setFrameShadow(QFrame.Raised)
        self.labelBandSeritMalzemesi = QLabel(self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesi.setObjectName(u"labelBandSeritMalzemesi")
        self.labelBandSeritMalzemesi.setGeometry(QRect(33, 20, 201, 20))
        self.labelBandSeritMalzemesi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBandSeritMalzemesiValue = QLabel(self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesiValue.setObjectName(u"labelBandSeritMalzemesiValue")
        self.labelBandSeritMalzemesiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelBandSeritMalzemesiValue.setFont(font)
        self.labelBandSeritMalzemesiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBandSeritMalzemesiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Container_4 = QFrame(Form)
        self.Container_4.setObjectName(u"Container_4")
        self.Container_4.setGeometry(QRect(1033, 423, 857, 413))
        self.Container_4.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_4.setFrameShape(QFrame.StyledPanel)
        self.Container_4.setFrameShadow(QFrame.Raised)
        self.FrameSeritSapmasi = QFrame(self.Container_4)
        self.FrameSeritSapmasi.setObjectName(u"FrameSeritSapmasi")
        self.FrameSeritSapmasi.setGeometry(QRect(20, 27, 260, 105))
        self.FrameSeritSapmasi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritSapmasi.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritSapmasi.setFrameShadow(QFrame.Raised)
        self.labelSeritSapmasi = QLabel(self.FrameSeritSapmasi)
        self.labelSeritSapmasi.setObjectName(u"labelSeritSapmasi")
        self.labelSeritSapmasi.setGeometry(QRect(33, 20, 201, 31))
        self.labelSeritSapmasi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritSapmasi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelSeritSapmasiValue = QLabel(self.FrameSeritSapmasi)
        self.labelSeritSapmasiValue.setObjectName(u"labelSeritSapmasiValue")
        self.labelSeritSapmasiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritSapmasiValue.setFont(font)
        self.labelSeritSapmasiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritSapmasiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameSeritGerginligi = QFrame(self.Container_4)
        self.FrameSeritGerginligi.setObjectName(u"FrameSeritGerginligi")
        self.FrameSeritGerginligi.setGeometry(QRect(300, 27, 260, 105))
        self.FrameSeritGerginligi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritGerginligi.setFrameShape(QFrame.StyledPanel)
        self.FrameSeritGerginligi.setFrameShadow(QFrame.Raised)
        self.labelSeritGerginligi = QLabel(self.FrameSeritGerginligi)
        self.labelSeritGerginligi.setObjectName(u"labelSeritGerginligi")
        self.labelSeritGerginligi.setGeometry(QRect(33, 20, 201, 31))
        self.labelSeritGerginligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelSeritGerginligi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelSeritGerginligiValue = QLabel(self.FrameSeritGerginligi)
        self.labelSeritGerginligiValue.setObjectName(u"labelSeritGerginligiValue")
        self.labelSeritGerginligiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelSeritGerginligiValue.setFont(font)
        self.labelSeritGerginligiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelSeritGerginligiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameKafaYuksekligi = QFrame(self.Container_4)
        self.FrameKafaYuksekligi.setObjectName(u"FrameKafaYuksekligi")
        self.FrameKafaYuksekligi.setGeometry(QRect(580, 27, 260, 105))
        self.FrameKafaYuksekligi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKafaYuksekligi.setFrameShape(QFrame.StyledPanel)
        self.FrameKafaYuksekligi.setFrameShadow(QFrame.Raised)
        self.labelKafaYuksekligi = QLabel(self.FrameKafaYuksekligi)
        self.labelKafaYuksekligi.setObjectName(u"labelKafaYuksekligi")
        self.labelKafaYuksekligi.setGeometry(QRect(33, 20, 201, 31))
        self.labelKafaYuksekligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelKafaYuksekligi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelKafaYuksekligiValue = QLabel(self.FrameKafaYuksekligi)
        self.labelKafaYuksekligiValue.setObjectName(u"labelKafaYuksekligiValue")
        self.labelKafaYuksekligiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelKafaYuksekligiValue.setFont(font)
        self.labelKafaYuksekligiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelKafaYuksekligiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameTitresimX = QFrame(self.Container_4)
        self.FrameTitresimX.setObjectName(u"FrameTitresimX")
        self.FrameTitresimX.setGeometry(QRect(20, 154, 260, 105))
        self.FrameTitresimX.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimX.setFrameShape(QFrame.StyledPanel)
        self.FrameTitresimX.setFrameShadow(QFrame.Raised)
        self.labelTitresimX = QLabel(self.FrameTitresimX)
        self.labelTitresimX.setObjectName(u"labelTitresimX")
        self.labelTitresimX.setGeometry(QRect(33, 20, 201, 31))
        self.labelTitresimX.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTitresimX.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelTitresimXValue = QLabel(self.FrameTitresimX)
        self.labelTitresimXValue.setObjectName(u"labelTitresimXValue")
        self.labelTitresimXValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelTitresimXValue.setFont(font)
        self.labelTitresimXValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTitresimXValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameTitresimY = QFrame(self.Container_4)
        self.FrameTitresimY.setObjectName(u"FrameTitresimY")
        self.FrameTitresimY.setGeometry(QRect(300, 154, 260, 105))
        self.FrameTitresimY.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimY.setFrameShape(QFrame.StyledPanel)
        self.FrameTitresimY.setFrameShadow(QFrame.Raised)
        self.labelTitresimY = QLabel(self.FrameTitresimY)
        self.labelTitresimY.setObjectName(u"labelTitresimY")
        self.labelTitresimY.setGeometry(QRect(33, 20, 201, 31))
        self.labelTitresimY.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTitresimY.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelTitresimYValue = QLabel(self.FrameTitresimY)
        self.labelTitresimYValue.setObjectName(u"labelTitresimYValue")
        self.labelTitresimYValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelTitresimYValue.setFont(font)
        self.labelTitresimYValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTitresimYValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameTitresimZ = QFrame(self.Container_4)
        self.FrameTitresimZ.setObjectName(u"FrameTitresimZ")
        self.FrameTitresimZ.setGeometry(QRect(580, 154, 260, 105))
        self.FrameTitresimZ.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimZ.setFrameShape(QFrame.StyledPanel)
        self.FrameTitresimZ.setFrameShadow(QFrame.Raised)
        self.labelTitresimZ = QLabel(self.FrameTitresimZ)
        self.labelTitresimZ.setObjectName(u"labelTitresimZ")
        self.labelTitresimZ.setGeometry(QRect(33, 20, 201, 31))
        self.labelTitresimZ.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTitresimZ.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelTitresimZValue = QLabel(self.FrameTitresimZ)
        self.labelTitresimZValue.setObjectName(u"labelTitresimZValue")
        self.labelTitresimZValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelTitresimZValue.setFont(font)
        self.labelTitresimZValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTitresimZValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameMengeneBasinc = QFrame(self.Container_4)
        self.FrameMengeneBasinc.setObjectName(u"FrameMengeneBasinc")
        self.FrameMengeneBasinc.setGeometry(QRect(20, 280, 260, 105))
        self.FrameMengeneBasinc.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMengeneBasinc.setFrameShape(QFrame.StyledPanel)
        self.FrameMengeneBasinc.setFrameShadow(QFrame.Raised)
        self.labelMengeneBasinc = QLabel(self.FrameMengeneBasinc)
        self.labelMengeneBasinc.setObjectName(u"labelMengeneBasinc")
        self.labelMengeneBasinc.setGeometry(QRect(33, 20, 201, 31))
        self.labelMengeneBasinc.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelMengeneBasinc.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelMengeneBasincValue = QLabel(self.FrameMengeneBasinc)
        self.labelMengeneBasincValue.setObjectName(u"labelMengeneBasincValue")
        self.labelMengeneBasincValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelMengeneBasincValue.setFont(font)
        self.labelMengeneBasincValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelMengeneBasincValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameOrtamSicakligi = QFrame(self.Container_4)
        self.FrameOrtamSicakligi.setObjectName(u"FrameOrtamSicakligi")
        self.FrameOrtamSicakligi.setGeometry(QRect(300, 280, 260, 105))
        self.FrameOrtamSicakligi.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameOrtamSicakligi.setFrameShape(QFrame.StyledPanel)
        self.FrameOrtamSicakligi.setFrameShadow(QFrame.Raised)
        self.labelOrtamSicakligi = QLabel(self.FrameOrtamSicakligi)
        self.labelOrtamSicakligi.setObjectName(u"labelOrtamSicakligi")
        self.labelOrtamSicakligi.setGeometry(QRect(33, 20, 201, 31))
        self.labelOrtamSicakligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelOrtamSicakligi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelOrtamSicakligiValue = QLabel(self.FrameOrtamSicakligi)
        self.labelOrtamSicakligiValue.setObjectName(u"labelOrtamSicakligiValue")
        self.labelOrtamSicakligiValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelOrtamSicakligiValue.setFont(font)
        self.labelOrtamSicakligiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelOrtamSicakligiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.FrameOrtamNem = QFrame(self.Container_4)
        self.FrameOrtamNem.setObjectName(u"FrameOrtamNem")
        self.FrameOrtamNem.setGeometry(QRect(580, 280, 260, 105))
        self.FrameOrtamNem.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameOrtamNem.setFrameShape(QFrame.StyledPanel)
        self.FrameOrtamNem.setFrameShadow(QFrame.Raised)
        self.labelOrtamNem = QLabel(self.FrameOrtamNem)
        self.labelOrtamNem.setObjectName(u"labelOrtamNem")
        self.labelOrtamNem.setGeometry(QRect(33, 20, 201, 31))
        self.labelOrtamNem.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: rgba(244, 246, 252, 151);\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelOrtamNem.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelOrtamNemValue = QLabel(self.FrameOrtamNem)
        self.labelOrtamNemValue.setObjectName(u"labelOrtamNemValue")
        self.labelOrtamNemValue.setGeometry(QRect(30, 43, 211, 50))
        self.labelOrtamNemValue.setFont(font)
        self.labelOrtamNemValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelOrtamNemValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelMalzemeCinsi.setText(QCoreApplication.translate("Form", u"Malzeme Cinsi", None))
        self.labelMalzemeCinsiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelMalzemeSertligi.setText(QCoreApplication.translate("Form", u"Malzeme Sertli\u011fi", None))
        self.labelMalzemeSertligiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelKesitYapisi.setText(QCoreApplication.translate("Form", u"Kesit Yap\u0131s\u0131", None))
        self.labelKesitYapisiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelA.setText(QCoreApplication.translate("Form", u"A (mm)", None))
        self.labelAValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelB.setText(QCoreApplication.translate("Form", u"B (mm)", None))
        self.labelC.setText(QCoreApplication.translate("Form", u"C (mm)", None))
        self.labelD.setText(QCoreApplication.translate("Form", u"D (mm)", None))
        self.labelBValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelCValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelDValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelDate.setText(QCoreApplication.translate("Form", u"14.12.2025 \u00c7ar\u015famba", None))
        self.labelTime.setText(QCoreApplication.translate("Form", u"12.30", None))
        self.labelKesilenParcaAdeti.setText(QCoreApplication.translate("Form", u"Kesilen Par\u00e7a Adeti", None))
        self.labelKesilenParcaAdetiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelTestereDurum.setText(QCoreApplication.translate("Form", u"Testere Durum", None))
        self.labelTestereDurumValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelAlarm.setText(QCoreApplication.translate("Form", u"Alarm", None))
        self.labelAlarmValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritMotorHiz.setText(QCoreApplication.translate("Form", u"\u015eerit Motor H\u0131z", None))
        self.labelSeritMotorHizValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelInmeMotorHiz.setText(QCoreApplication.translate("Form", u"\u0130nme Motor H\u0131z", None))
        self.labelInmeMotorHizValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritMotorAkim.setText(QCoreApplication.translate("Form", u"\u015eerit Motor Ak\u0131m", None))
        self.labelSeritMotorAkimValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelInmeMotorAkim.setText(QCoreApplication.translate("Form", u"\u0130nme Motor Ak\u0131m", None))
        self.labelInmeMotorAkimValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritMotorTork.setText(QCoreApplication.translate("Form", u"\u015eerit Motor Tork", None))
        self.labelSeritMotorTorkValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelInmeMotorTork.setText(QCoreApplication.translate("Form", u"\u0130nme Motor Tork", None))
        self.labelInmeMotorTorkValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSmart.setText(QCoreApplication.translate("Form", u"SMART", None))
        self.labelSaw.setText(QCoreApplication.translate("Form", u"SAW", None))
        self.btnControlPanel.setText(QCoreApplication.translate("Form", u" Kontrol Paneli", None))
        self.btnPositioning.setText(QCoreApplication.translate("Form", u"Konumland\u0131rma", None))
        self.btnCamera.setText(QCoreApplication.translate("Form", u"Kamera Verileri", None))
        self.btnSensor.setText(QCoreApplication.translate("Form", u"Sens\u00f6r Verileri", None))
        self.btnTracking.setText(QCoreApplication.translate("Form", u"\u0130zleme", None))
        self.labelMakineID.setText(QCoreApplication.translate("Form", u"Makine ID", None))
        self.labelMakineIDValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritID.setText(QCoreApplication.translate("Form", u"\u015eerit ID", None))
        self.labelSeritIDValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritDisOlcusu.setText(QCoreApplication.translate("Form", u"\u015eerit Di\u015f \u00d6l\u00e7\u00fcs\u00fc", None))
        self.labelSeritDisOlcusuValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritTipi.setText(QCoreApplication.translate("Form", u"\u015eerit Tipi", None))
        self.labelSeritTipiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritMarkasi.setText(QCoreApplication.translate("Form", u"\u015eerit Markas\u0131", None))
        self.labelSeritMarkasiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelBandSeritMalzemesi.setText(QCoreApplication.translate("Form", u"\u015eerit Malzemesi", None))
        self.labelBandSeritMalzemesiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritSapmasi.setText(QCoreApplication.translate("Form", u"\u015eerit Sapmas\u0131", None))
        self.labelSeritSapmasiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelSeritGerginligi.setText(QCoreApplication.translate("Form", u"\u015eerit Gerginli\u011fi", None))
        self.labelSeritGerginligiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelKafaYuksekligi.setText(QCoreApplication.translate("Form", u"Kafa Y\u00fcksekli\u011fi", None))
        self.labelKafaYuksekligiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelTitresimX.setText(QCoreApplication.translate("Form", u"Titre\u015fim (X)", None))
        self.labelTitresimXValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelTitresimY.setText(QCoreApplication.translate("Form", u"Titre\u015fim (Y)", None))
        self.labelTitresimYValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelTitresimZ.setText(QCoreApplication.translate("Form", u"Titre\u015fim (Z)", None))
        self.labelTitresimZValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelMengeneBasinc.setText(QCoreApplication.translate("Form", u"Mengene Bas\u0131n\u00e7", None))
        self.labelMengeneBasincValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelOrtamSicakligi.setText(QCoreApplication.translate("Form", u"Ortam S\u0131cakl\u0131\u011f\u0131", None))
        self.labelOrtamSicakligiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelOrtamNem.setText(QCoreApplication.translate("Form", u"Ortam Nem", None))
        self.labelOrtamNemValue.setText(QCoreApplication.translate("Form", u"16.35", None))
    # retranslateUi

