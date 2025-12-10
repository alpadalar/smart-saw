# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sensor_widget..ui'
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
    QSizePolicy, QToolButton, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1920, 1080)
        self.XEkseniFrame = QFrame(Form)
        self.XEkseniFrame.setObjectName(u"XEkseniFrame")
        self.XEkseniFrame.setGeometry(QRect(425, 724, 578, 342))
        self.XEkseniFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.XEkseniFrame.setFrameShape(QFrame.StyledPanel)
        self.XEkseniFrame.setFrameShadow(QFrame.Raised)
        self.labelXEkseni = QLabel(self.XEkseniFrame)
        self.labelXEkseni.setObjectName(u"labelXEkseni")
        self.labelXEkseni.setGeometry(QRect(34, 19, 295, 39))
        font = QFont()
        font.setFamilies([u"Plus-Jakarta-Sans"])
        font.setBold(True)
        self.labelXEkseni.setFont(font)
        self.labelXEkseni.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 28px;\n"
"}")
        self.btnKesmeHizi = QPushButton(self.XEkseniFrame)
        self.btnKesmeHizi.setObjectName(u"btnKesmeHizi")
        self.btnKesmeHizi.setGeometry(QRect(41, 82, 240, 69))
        self.btnKesmeHizi.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    border-radius: 30px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"\n"
"")
        self.btnKesmeHizi.setCheckable(True)
        self.btnIlerlemeHizi = QPushButton(self.XEkseniFrame)
        self.btnIlerlemeHizi.setObjectName(u"btnIlerlemeHizi")
        self.btnIlerlemeHizi.setGeometry(QRect(298, 82, 240, 69))
        self.btnIlerlemeHizi.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    border-radius: 30px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnIlerlemeHizi.setCheckable(True)
        self.btnSeritAkim = QPushButton(self.XEkseniFrame)
        self.btnSeritAkim.setObjectName(u"btnSeritAkim")
        self.btnSeritAkim.setGeometry(QRect(41, 162, 240, 69))
        self.btnSeritAkim.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    border-radius: 30px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        self.btnSeritAkim.setCheckable(True)
        self.btnSeritSapmasi = QPushButton(self.XEkseniFrame)
        self.btnSeritSapmasi.setObjectName(u"btnSeritSapmasi")
        self.btnSeritSapmasi.setGeometry(QRect(298, 162, 240, 69))
        self.btnSeritSapmasi.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    border-radius: 30px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        self.btnSeritSapmasi.setCheckable(True)
        self.btnSeritTork = QPushButton(self.XEkseniFrame)
        self.btnSeritTork.setObjectName(u"btnSeritTork")
        self.btnSeritTork.setGeometry(QRect(169, 239, 240, 69))
        self.btnSeritTork.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    border-radius: 30px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnSeritTork.setCheckable(True)
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
        self.AnomaliDurumuFrame = QFrame(Form)
        self.AnomaliDurumuFrame.setObjectName(u"AnomaliDurumuFrame")
        self.AnomaliDurumuFrame.setGeometry(QRect(1385, 127, 505, 941))
        self.AnomaliDurumuFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.AnomaliDurumuFrame.setFrameShape(QFrame.StyledPanel)
        self.AnomaliDurumuFrame.setFrameShadow(QFrame.Raised)
        self.labelAnomaliDurumu = QLabel(self.AnomaliDurumuFrame)
        self.labelAnomaliDurumu.setObjectName(u"labelAnomaliDurumu")
        self.labelAnomaliDurumu.setGeometry(QRect(34, 19, 295, 39))
        self.labelAnomaliDurumu.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.MotorVerileriFrame = QFrame(self.AnomaliDurumuFrame)
        self.MotorVerileriFrame.setObjectName(u"MotorVerileriFrame")
        self.MotorVerileriFrame.setGeometry(QRect(23, 77, 459, 839))
        self.MotorVerileriFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.MotorVerileriFrame.setFrameShape(QFrame.StyledPanel)
        self.MotorVerileriFrame.setFrameShadow(QFrame.Raised)
        self.KesmeHiziFrame = QFrame(self.MotorVerileriFrame)
        self.KesmeHiziFrame.setObjectName(u"KesmeHiziFrame")
        self.KesmeHiziFrame.setGeometry(QRect(8, 30, 443, 60))
        self.KesmeHiziFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad, \n"
"    x1:0, y1:0, \n"
"    x2:1, y2:1, \n"
"    stop:0 rgba(0, 0, 0, 255), \n"
"    stop:1 rgba(124, 4, 66, 255)\n"
");\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.KesmeHiziFrame.setFrameShape(QFrame.StyledPanel)
        self.KesmeHiziFrame.setFrameShadow(QFrame.Raised)
        self.labelKesmeHizi = QLabel(self.KesmeHiziFrame)
        self.labelKesmeHizi.setObjectName(u"labelKesmeHizi")
        self.labelKesmeHizi.setGeometry(QRect(28, 8, 393, 20))
        self.labelKesmeHizi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.labelKesmeHiziInfo = QLabel(self.KesmeHiziFrame)
        self.labelKesmeHiziInfo.setObjectName(u"labelKesmeHiziInfo")
        self.labelKesmeHiziInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelKesmeHiziInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelKesmeHiziInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.IlerlemeHiziFrame = QFrame(self.MotorVerileriFrame)
        self.IlerlemeHiziFrame.setObjectName(u"IlerlemeHiziFrame")
        self.IlerlemeHiziFrame.setGeometry(QRect(8, 110, 443, 60))
        self.IlerlemeHiziFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.IlerlemeHiziFrame.setFrameShape(QFrame.StyledPanel)
        self.IlerlemeHiziFrame.setFrameShadow(QFrame.Raised)
        self.labelIlerlemeHiziInfo = QLabel(self.IlerlemeHiziFrame)
        self.labelIlerlemeHiziInfo.setObjectName(u"labelIlerlemeHiziInfo")
        self.labelIlerlemeHiziInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelIlerlemeHiziInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelIlerlemeHiziInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelIlerlemeHizi = QLabel(self.IlerlemeHiziFrame)
        self.labelIlerlemeHizi.setObjectName(u"labelIlerlemeHizi")
        self.labelIlerlemeHizi.setGeometry(QRect(25, 8, 393, 20))
        self.labelIlerlemeHizi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.SeritAkimFrame = QFrame(self.MotorVerileriFrame)
        self.SeritAkimFrame.setObjectName(u"SeritAkimFrame")
        self.SeritAkimFrame.setGeometry(QRect(8, 190, 443, 60))
        self.SeritAkimFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SeritAkimFrame.setFrameShape(QFrame.StyledPanel)
        self.SeritAkimFrame.setFrameShadow(QFrame.Raised)
        self.labelSeritAkimInfo = QLabel(self.SeritAkimFrame)
        self.labelSeritAkimInfo.setObjectName(u"labelSeritAkimInfo")
        self.labelSeritAkimInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelSeritAkimInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelSeritAkimInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelSeritAkim = QLabel(self.SeritAkimFrame)
        self.labelSeritAkim.setObjectName(u"labelSeritAkim")
        self.labelSeritAkim.setGeometry(QRect(25, 8, 393, 20))
        self.labelSeritAkim.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.SeritTorkFrame = QFrame(self.MotorVerileriFrame)
        self.SeritTorkFrame.setObjectName(u"SeritTorkFrame")
        self.SeritTorkFrame.setGeometry(QRect(8, 270, 443, 60))
        self.SeritTorkFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SeritTorkFrame.setFrameShape(QFrame.StyledPanel)
        self.SeritTorkFrame.setFrameShadow(QFrame.Raised)
        self.labelSeritTorkInfo = QLabel(self.SeritTorkFrame)
        self.labelSeritTorkInfo.setObjectName(u"labelSeritTorkInfo")
        self.labelSeritTorkInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelSeritTorkInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelSeritTorkInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelSeritTork = QLabel(self.SeritTorkFrame)
        self.labelSeritTork.setObjectName(u"labelSeritTork")
        self.labelSeritTork.setGeometry(QRect(25, 8, 393, 20))
        self.labelSeritTork.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.SeritGerginligiFrame = QFrame(self.MotorVerileriFrame)
        self.SeritGerginligiFrame.setObjectName(u"SeritGerginligiFrame")
        self.SeritGerginligiFrame.setGeometry(QRect(8, 350, 443, 60))
        self.SeritGerginligiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SeritGerginligiFrame.setFrameShape(QFrame.StyledPanel)
        self.SeritGerginligiFrame.setFrameShadow(QFrame.Raised)
        self.labelSeritGerginligiInfo = QLabel(self.SeritGerginligiFrame)
        self.labelSeritGerginligiInfo.setObjectName(u"labelSeritGerginligiInfo")
        self.labelSeritGerginligiInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelSeritGerginligiInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelSeritGerginligiInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelSeritGerginligi = QLabel(self.SeritGerginligiFrame)
        self.labelSeritGerginligi.setObjectName(u"labelSeritGerginligi")
        self.labelSeritGerginligi.setGeometry(QRect(25, 8, 393, 20))
        self.labelSeritGerginligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.SeritSapmasiFrame = QFrame(self.MotorVerileriFrame)
        self.SeritSapmasiFrame.setObjectName(u"SeritSapmasiFrame")
        self.SeritSapmasiFrame.setGeometry(QRect(8, 430, 443, 60))
        self.SeritSapmasiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SeritSapmasiFrame.setFrameShape(QFrame.StyledPanel)
        self.SeritSapmasiFrame.setFrameShadow(QFrame.Raised)
        self.labelSeritSapmasiInfo = QLabel(self.SeritSapmasiFrame)
        self.labelSeritSapmasiInfo.setObjectName(u"labelSeritSapmasiInfo")
        self.labelSeritSapmasiInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelSeritSapmasiInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelSeritSapmasiInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelSeritSapmasi = QLabel(self.SeritSapmasiFrame)
        self.labelSeritSapmasi.setObjectName(u"labelSeritSapmasi")
        self.labelSeritSapmasi.setGeometry(QRect(25, 8, 393, 20))
        self.labelSeritSapmasi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.TitresimXFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimXFrame.setObjectName(u"TitresimXFrame")
        self.TitresimXFrame.setGeometry(QRect(8, 510, 443, 60))
        self.TitresimXFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TitresimXFrame.setFrameShape(QFrame.StyledPanel)
        self.TitresimXFrame.setFrameShadow(QFrame.Raised)
        self.labelTitresimXInfo = QLabel(self.TitresimXFrame)
        self.labelTitresimXInfo.setObjectName(u"labelTitresimXInfo")
        self.labelTitresimXInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelTitresimXInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelTitresimXInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelTitresimX = QLabel(self.TitresimXFrame)
        self.labelTitresimX.setObjectName(u"labelTitresimX")
        self.labelTitresimX.setGeometry(QRect(25, 8, 393, 20))
        self.labelTitresimX.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.TitresimYFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimYFrame.setObjectName(u"TitresimYFrame")
        self.TitresimYFrame.setGeometry(QRect(8, 590, 443, 60))
        self.TitresimYFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TitresimYFrame.setFrameShape(QFrame.StyledPanel)
        self.TitresimYFrame.setFrameShadow(QFrame.Raised)
        self.labelTitresimYInfo = QLabel(self.TitresimYFrame)
        self.labelTitresimYInfo.setObjectName(u"labelTitresimYInfo")
        self.labelTitresimYInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelTitresimYInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelTitresimYInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelTitresimY = QLabel(self.TitresimYFrame)
        self.labelTitresimY.setObjectName(u"labelTitresimY")
        self.labelTitresimY.setGeometry(QRect(25, 8, 393, 20))
        self.labelTitresimY.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.TitresimZFrame = QFrame(self.MotorVerileriFrame)
        self.TitresimZFrame.setObjectName(u"TitresimZFrame")
        self.TitresimZFrame.setGeometry(QRect(8, 670, 443, 60))
        self.TitresimZFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"    spread:pad,\n"
"    x1:0, y1:0,\n"
"    x2:1, y2:1,\n"
"    stop:0 rgba(0, 0, 0, 255),\n"
"    stop:0.480769 rgba(9, 139, 7, 255),\n"
"    stop:1 rgba(9, 139, 7, 255)\n"
");\n"
"\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TitresimZFrame.setFrameShape(QFrame.StyledPanel)
        self.TitresimZFrame.setFrameShadow(QFrame.Raised)
        self.labelTitresimZInfo = QLabel(self.TitresimZFrame)
        self.labelTitresimZInfo.setObjectName(u"labelTitresimZInfo")
        self.labelTitresimZInfo.setGeometry(QRect(25, 33, 401, 20))
        self.labelTitresimZInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 18px;\n"
"}")
        self.labelTitresimZInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelTitresimZ = QLabel(self.TitresimZFrame)
        self.labelTitresimZ.setObjectName(u"labelTitresimZ")
        self.labelTitresimZ.setGeometry(QRect(25, 8, 393, 20))
        self.labelTitresimZ.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:\t#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.toolButton = QToolButton(self.MotorVerileriFrame)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setGeometry(QRect(8, 750, 443, 60))
        self.toolButton.setStyleSheet("    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,\n"
"                                stop: 0 #000000, \n"
"                                stop: 0.38 rgba(26, 31, 55, 200));\n"
"    border: 1px solid #F4F6FC;\n"
"    border-radius: 20px;\n"
"    color:    #F4F6FC;\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: medium;\n"
"    font-size:19px;")
        self.kesimGrafigiFrame = QFrame(Form)
        self.kesimGrafigiFrame.setObjectName(u"kesimGrafigiFrame")
        self.kesimGrafigiFrame.setGeometry(QRect(425, 127, 934, 568))
        self.kesimGrafigiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.kesimGrafigiFrame.setFrameShape(QFrame.StyledPanel)
        self.kesimGrafigiFrame.setFrameShadow(QFrame.Raised)
        self.labelKesimGrafigi = QLabel(self.kesimGrafigiFrame)
        self.labelKesimGrafigi.setObjectName(u"labelKesimGrafigi")
        self.labelKesimGrafigi.setGeometry(QRect(34, 19, 461, 45))
        self.labelKesimGrafigi.setFont(font)
        self.labelKesimGrafigi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.labelKesimGrafigiInfo = QLabel(self.kesimGrafigiFrame)
        self.labelKesimGrafigiInfo.setObjectName(u"labelKesimGrafigiInfo")
        self.labelKesimGrafigiInfo.setGeometry(QRect(296, 23, 631, 31))
        font1 = QFont()
        font1.setFamilies([u"Plus-Jakarta-Sans"])
        font1.setBold(False)
        self.labelKesimGrafigiInfo.setFont(font1)
        self.labelKesimGrafigiInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 100;\n"
"	font-size: 22px;\n"
"}")
        self.labelKesimGrafigiInfo.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.YEkseniFrame = QFrame(Form)
        self.YEkseniFrame.setObjectName(u"YEkseniFrame")
        self.YEkseniFrame.setGeometry(QRect(1030, 724, 329, 342))
        self.YEkseniFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.YEkseniFrame.setFrameShape(QFrame.StyledPanel)
        self.YEkseniFrame.setFrameShadow(QFrame.Raised)
        self.labelYEkseni = QLabel(self.YEkseniFrame)
        self.labelYEkseni.setObjectName(u"labelYEkseni")
        self.labelYEkseni.setGeometry(QRect(34, 19, 295, 39))
        self.labelYEkseni.setFont(font)
        self.labelYEkseni.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 28px;\n"
"}")
        self.btnZaman = QPushButton(self.YEkseniFrame)
        self.btnZaman.setObjectName(u"btnZaman")
        self.btnZaman.setGeometry(QRect(53, 82, 223, 90))
        self.btnZaman.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 30px;\n"
"    border-radius: 45px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"\n"
"")
        self.btnZaman.setCheckable(True)
        self.btnYukseklik = QPushButton(self.YEkseniFrame)
        self.btnYukseklik.setObjectName(u"btnYukseklik")
        self.btnYukseklik.setGeometry(QRect(53, 218, 223, 90))
        self.btnYukseklik.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 30px;\n"
"    border-radius: 45px;\n"
"	border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnYukseklik.setCheckable(True)
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
        font2 = QFont()
        font2.setFamilies([u"Plus Jakarta Sans"])
        font2.setBold(False)
        font2.setItalic(False)
        font2.setUnderline(False)
        font2.setStrikeOut(False)
        self.btnControlPanel.setFont(font2)
        self.btnControlPanel.setMouseTracking(True)
        self.btnControlPanel.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: semibold;\n"
"    font-size: 32px;\n"
"    text-align: left;\n"
"    padding: 12px 10px 12px 25px;  /* simge için boşluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opaklık */\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u"src/gui/images/control-panel-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon1.addFile(u"src/gui/images/control-panel-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnControlPanel.setIcon(icon1)
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
"    padding: 12px 10px 12px 20px;  /* simge için boşluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opaklık */\n"
"}")
        icon2 = QIcon()
        icon2.addFile(u"src/gui/images/positioning-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon2.addFile(u"src/gui/images/positioning-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnPositioning.setIcon(icon2)
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
"    padding: 12px 10px 12px 20px;  /* simge için boşluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opaklık */\n"
"}\n"
"")
        icon3 = QIcon()
        icon3.addFile(u"src/gui/images/camera-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon3.addFile(u"src/gui/images/camera-icon-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnCamera.setIcon(icon3)
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
"    padding: 12px 10px 12px 20px;  /* simge için boşluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opaklık */\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u"src/gui/images/sensor-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon4.addFile(u"src/gui/images/sensor-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnSensor.setIcon(icon4)
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
"    padding: 12px 10px 12px 20px;  /* simge için boşluk */\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: rgba(26, 31, 55, 128); /* %50 opaklık */\n"
"}")
        icon5 = QIcon()
        icon5.addFile(u"src/gui/images/tracking-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon5.addFile(u"src/gui/images/tracking-icon2-active.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        self.btnTracking.setIcon(icon5)
        self.btnTracking.setIconSize(QSize(80, 80))

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelXEkseni.setText(QCoreApplication.translate("Form", u"Y Ekseni", None))
        self.btnKesmeHizi.setText(QCoreApplication.translate("Form", u"Kesme\n"
"H\u0131z\u0131", None))
        self.btnIlerlemeHizi.setText(QCoreApplication.translate("Form", u"\u0130lerleme\n"
"H\u0131z\u0131", None))
        self.btnSeritAkim.setText(QCoreApplication.translate("Form", u"\u015eerit\n"
"Ak\u0131m", None))
        self.btnSeritSapmasi.setText(QCoreApplication.translate("Form", u"\u015eerit\n"
"Sapmas\u0131", None))
        self.btnSeritTork.setText(QCoreApplication.translate("Form", u"\u015eerit\n"
"Tork", None))
        self.labelDate.setText(QCoreApplication.translate("Form", u"14.12.2025 \u00c7ar\u015famba", None))
        self.labelTime.setText(QCoreApplication.translate("Form", u"12.30", None))
        self.labelAnomaliDurumu.setText(QCoreApplication.translate("Form", u"Anomali Durumu", None))
        self.labelKesmeHizi.setText(QCoreApplication.translate("Form", u"Kesme H\u0131z\u0131", None))
        self.labelKesmeHiziInfo.setText(QCoreApplication.translate("Form", u"14.12.2025 tarihinde anomali tespit edildi.", None))
        self.labelIlerlemeHiziInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelIlerlemeHizi.setText(QCoreApplication.translate("Form", u"\u0130lerleme H\u0131z\u0131", None))
        self.labelSeritAkimInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelSeritAkim.setText(QCoreApplication.translate("Form", u"\u015eerit Ak\u0131m", None))
        self.labelSeritTorkInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelSeritTork.setText(QCoreApplication.translate("Form", u"\u015eerit Tork", None))
        self.labelSeritGerginligiInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelSeritGerginligi.setText(QCoreApplication.translate("Form", u"\u015eerit Gerginli\u011fi", None))
        self.labelSeritSapmasiInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelSeritSapmasi.setText(QCoreApplication.translate("Form", u"\u015eerit Sapmas\u0131", None))
        self.labelTitresimXInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelTitresimX.setText(QCoreApplication.translate("Form", u"Titre\u015fim X Ekseni", None))
        self.labelTitresimYInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelTitresimY.setText(QCoreApplication.translate("Form", u"Titre\u015fim Y Ekseni", None))
        self.labelTitresimZInfo.setText(QCoreApplication.translate("Form", u"Her \u015fey yolunda.", None))
        self.labelTitresimZ.setText(QCoreApplication.translate("Form", u"Titre\u015fim Z Ekseni", None))
        self.toolButton.setText(QCoreApplication.translate("Form", "Anomali tespitlerini temizlemek için tıklayın."))
        self.labelKesimGrafigi.setText(QCoreApplication.translate("Form", u"Kesim Grafi\u011fi", None))
        self.labelKesimGrafigiInfo.setText(QCoreApplication.translate("Form", u"G\u00f6r\u00fcnt\u00fclemek istedi\u011finiz grafi\u011fin X ve Y eksenini se\u00e7in.", None))
        self.labelYEkseni.setText(QCoreApplication.translate("Form", u"X Ekseni", None))
        self.btnZaman.setText(QCoreApplication.translate("Form", u"Zaman", None))
        self.btnYukseklik.setText(QCoreApplication.translate("Form", u"Y\u00fckseklik", None))
        self.labelSmart.setText(QCoreApplication.translate("Form", u"SMART", None))
        self.labelSaw.setText(QCoreApplication.translate("Form", u"SAW", None))
        self.btnControlPanel.setText(QCoreApplication.translate("Form", u" Kontrol Paneli", None))
        self.btnPositioning.setText(QCoreApplication.translate("Form", u"Konumland\u0131rma", None))
        self.btnCamera.setText(QCoreApplication.translate("Form", u"Kamera Verileri", None))
        self.btnSensor.setText(QCoreApplication.translate("Form", u"Sens\u00f6r Verileri", None))
        self.btnTracking.setText(QCoreApplication.translate("Form", u"\u0130zleme", None))
    # retranslateUi

