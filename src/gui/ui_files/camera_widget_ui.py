# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'camera_widget..ui'
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
        self.TestereSagligiFrame = QFrame(Form)
        self.TestereSagligiFrame.setObjectName(u"TestereSagligiFrame")
        self.TestereSagligiFrame.setGeometry(QRect(762, 961, 260, 105))
        self.TestereSagligiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TestereSagligiFrame.setFrameShape(QFrame.StyledPanel)
        self.TestereSagligiFrame.setFrameShadow(QFrame.Raised)
        self.labelTestereSagligi = QLabel(self.TestereSagligiFrame)
        self.labelTestereSagligi.setObjectName(u"labelTestereSagligi")
        self.labelTestereSagligi.setGeometry(QRect(23, 9, 231, 31))
        self.labelTestereSagligi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTestereSagligiValue = QLabel(self.TestereSagligiFrame)
        self.labelTestereSagligiValue.setObjectName(u"labelTestereSagligiValue")
        self.labelTestereSagligiValue.setGeometry(QRect(11, 43, 241, 50))
        font = QFont()
        font.setFamilies([u"Plus-Jakarta-Sans"])
        font.setBold(True)
        self.labelTestereSagligiValue.setFont(font)
        self.labelTestereSagligiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTestereSagligiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.KameraFrame = QFrame(Form)
        self.KameraFrame.setObjectName(u"KameraFrame")
        self.KameraFrame.setGeometry(QRect(425, 125, 934, 525))
        self.KameraFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.KameraFrame.setFrameShape(QFrame.StyledPanel)
        self.KameraFrame.setFrameShadow(QFrame.Raised)
        self.TespitEdilenKirikFrame = QFrame(self.KameraFrame)
        self.TespitEdilenKirikFrame.setObjectName(u"TespitEdilenKirikFrame")
        self.TespitEdilenKirikFrame.setGeometry(QRect(494, 400, 281, 105))
        self.TespitEdilenKirikFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TespitEdilenKirikFrame.setFrameShape(QFrame.StyledPanel)
        self.TespitEdilenKirikFrame.setFrameShadow(QFrame.Raised)
        self.labelTespitEdilenKirik = QLabel(self.TespitEdilenKirikFrame)
        self.labelTespitEdilenKirik.setObjectName(u"labelTespitEdilenKirik")
        self.labelTespitEdilenKirik.setGeometry(QRect(24, 20, 251, 20))
        self.labelTespitEdilenKirik.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTespitEdilenKirikValue = QLabel(self.TespitEdilenKirikFrame)
        self.labelTespitEdilenKirikValue.setObjectName(u"labelTespitEdilenKirikValue")
        self.labelTespitEdilenKirikValue.setGeometry(QRect(91, 43, 151, 50))
        self.labelTespitEdilenKirikValue.setFont(font)
        self.labelTespitEdilenKirikValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTespitEdilenKirikValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.TespitEdilenDisFrame = QFrame(self.KameraFrame)
        self.TespitEdilenDisFrame.setObjectName(u"TespitEdilenDisFrame")
        self.TespitEdilenDisFrame.setGeometry(QRect(158, 400, 281, 105))
        self.TespitEdilenDisFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TespitEdilenDisFrame.setFrameShape(QFrame.StyledPanel)
        self.TespitEdilenDisFrame.setFrameShadow(QFrame.Raised)
        self.labelTespitEdilenDis = QLabel(self.TespitEdilenDisFrame)
        self.labelTespitEdilenDis.setObjectName(u"labelTespitEdilenDis")
        self.labelTespitEdilenDis.setGeometry(QRect(24, 20, 251, 20))
        self.labelTespitEdilenDis.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTespitEdilenDisValue = QLabel(self.TespitEdilenDisFrame)
        self.labelTespitEdilenDisValue.setObjectName(u"labelTespitEdilenDisValue")
        self.labelTespitEdilenDisValue.setGeometry(QRect(91, 43, 151, 50))
        self.labelTespitEdilenDisValue.setFont(font)
        self.labelTespitEdilenDisValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTespitEdilenDisValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.SiraliGoruntuFrame = QFrame(Form)
        self.SiraliGoruntuFrame.setObjectName(u"SiraliGoruntuFrame")
        self.SiraliGoruntuFrame.setGeometry(QRect(427, 687, 934, 150))
        self.SiraliGoruntuFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SiraliGoruntuFrame.setFrameShape(QFrame.StyledPanel)
        self.SiraliGoruntuFrame.setFrameShadow(QFrame.Raised)
        self.TestereDurumuFrame = QFrame(Form)
        self.TestereDurumuFrame.setObjectName(u"TestereDurumuFrame")
        self.TestereDurumuFrame.setGeometry(QRect(1099, 961, 260, 105))
        self.TestereDurumuFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TestereDurumuFrame.setFrameShape(QFrame.StyledPanel)
        self.TestereDurumuFrame.setFrameShadow(QFrame.Raised)
        self.labelTestereDurumu = QLabel(self.TestereDurumuFrame)
        self.labelTestereDurumu.setObjectName(u"labelTestereDurumu")
        self.labelTestereDurumu.setGeometry(QRect(23, 9, 231, 31))
        self.labelTestereDurumu.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelTestereDurumuValue = QLabel(self.TestereDurumuFrame)
        self.labelTestereDurumuValue.setObjectName(u"labelTestereDurumuValue")
        self.labelTestereDurumuValue.setGeometry(QRect(11, 43, 241, 50))
        self.labelTestereDurumuValue.setFont(font)
        self.labelTestereDurumuValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelTestereDurumuValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
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
        self.TestereDegisimFrame = QFrame(Form)
        self.TestereDegisimFrame.setObjectName(u"TestereDegisimFrame")
        self.TestereDegisimFrame.setGeometry(QRect(425, 873, 934, 60))
        self.TestereDegisimFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.TestereDegisimFrame.setFrameShape(QFrame.StyledPanel)
        self.TestereDegisimFrame.setFrameShadow(QFrame.Raised)
        self.labelTestereDegisim = QLabel(self.TestereDegisimFrame)
        self.labelTestereDegisim.setObjectName(u"labelTestereDegisim")
        self.labelTestereDegisim.setGeometry(QRect(35, -1, 461, 61))
        self.labelTestereDegisim.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 22px;\n"
"}")
        self.labelTestereDegisimTarih = QLabel(self.TestereDegisimFrame)
        self.labelTestereDegisimTarih.setObjectName(u"labelTestereDegisimTarih")
        self.labelTestereDegisimTarih.setGeometry(QRect(670, 16, 231, 28))
        self.labelTestereDegisimTarih.setLayoutDirection(Qt.LeftToRight)
        self.labelTestereDegisimTarih.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 28px;\n"
"}")
        self.labelTestereDegisimTarih.setText(u"28.07.2025")
        self.labelTestereDegisimTarih.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.KirikTespitiFrame = QFrame(Form)
        self.KirikTespitiFrame.setObjectName(u"KirikTespitiFrame")
        self.KirikTespitiFrame.setGeometry(QRect(1385, 125, 505, 438))
        self.KirikTespitiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.KirikTespitiFrame.setFrameShape(QFrame.StyledPanel)
        self.KirikTespitiFrame.setFrameShadow(QFrame.Raised)
        self.labelKirikTespiti = QLabel(self.KirikTespitiFrame)
        self.labelKirikTespiti.setObjectName(u"labelKirikTespiti")
        self.labelKirikTespiti.setGeometry(QRect(34, 19, 461, 45))
        self.labelKirikTespiti.setFont(font)
        self.labelKirikTespiti.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.KirikTespitiInfoFrame = QFrame(self.KirikTespitiFrame)
        self.KirikTespitiInfoFrame.setObjectName(u"KirikTespitiInfoFrame")
        self.KirikTespitiInfoFrame.setGeometry(QRect(31, 94, 443, 60))
        self.KirikTespitiInfoFrame.setStyleSheet(u"QFrame {\n"
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
        self.KirikTespitiInfoFrame.setFrameShape(QFrame.StyledPanel)
        self.KirikTespitiInfoFrame.setFrameShadow(QFrame.Raised)
        self.labelIlerlemeHiziInfo = QLabel(self.KirikTespitiInfoFrame)
        self.labelIlerlemeHiziInfo.setObjectName(u"labelIlerlemeHiziInfo")
        self.labelIlerlemeHiziInfo.setGeometry(QRect(25, 22, 393, 31))
        self.labelIlerlemeHiziInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelIlerlemeHiziInfo.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.labelIlerlemeHizi = QLabel(self.KirikTespitiInfoFrame)
        self.labelIlerlemeHizi.setObjectName(u"labelIlerlemeHizi")
        self.labelIlerlemeHizi.setGeometry(QRect(25, 8, 393, 31))
        self.labelIlerlemeHizi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 20px;\n"
"}")
        self.labelIlerlemeHizi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.CatlakTespitiFrame = QFrame(Form)
        self.CatlakTespitiFrame.setObjectName(u"CatlakTespitiFrame")
        self.CatlakTespitiFrame.setGeometry(QRect(1385, 628, 505, 438))
        self.CatlakTespitiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.CatlakTespitiFrame.setFrameShape(QFrame.StyledPanel)
        self.CatlakTespitiFrame.setFrameShadow(QFrame.Raised)
        self.labelCatlakTespiti = QLabel(self.CatlakTespitiFrame)
        self.labelCatlakTespiti.setObjectName(u"labelCatlakTespiti")
        self.labelCatlakTespiti.setGeometry(QRect(34, 19, 461, 45))
        self.labelCatlakTespiti.setFont(font)
        self.labelCatlakTespiti.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.CatlakTespitInfoFrame = QFrame(self.CatlakTespitiFrame)
        self.CatlakTespitInfoFrame.setObjectName(u"CatlakTespitInfoFrame")
        self.CatlakTespitInfoFrame.setGeometry(QRect(31, 94, 443, 60))
        self.CatlakTespitInfoFrame.setStyleSheet(u"QFrame {\n"
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
        self.CatlakTespitInfoFrame.setFrameShape(QFrame.StyledPanel)
        self.CatlakTespitInfoFrame.setFrameShadow(QFrame.Raised)
        self.labelCatlakTespitInfo = QLabel(self.CatlakTespitInfoFrame)
        self.labelCatlakTespitInfo.setObjectName(u"labelCatlakTespitInfo")
        self.labelCatlakTespitInfo.setGeometry(QRect(33, 18, 391, 25))
        self.labelCatlakTespitInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.AsinmaYuzdesiFrame = QFrame(Form)
        self.AsinmaYuzdesiFrame.setObjectName(u"AsinmaYuzdesiFrame")
        self.AsinmaYuzdesiFrame.setGeometry(QRect(425, 961, 260, 105))
        self.AsinmaYuzdesiFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.AsinmaYuzdesiFrame.setFrameShape(QFrame.StyledPanel)
        self.AsinmaYuzdesiFrame.setFrameShadow(QFrame.Raised)
        self.labelAsinmaYuzdesi = QLabel(self.AsinmaYuzdesiFrame)
        self.labelAsinmaYuzdesi.setObjectName(u"labelAsinmaYuzdesi")
        self.labelAsinmaYuzdesi.setGeometry(QRect(23, 9, 231, 31))
        self.labelAsinmaYuzdesi.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color:	#F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelAsinmaYuzdesi.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.labelAsinmaYuzdesiValue = QLabel(self.AsinmaYuzdesiFrame)
        self.labelAsinmaYuzdesiValue.setObjectName(u"labelAsinmaYuzdesiValue")
        self.labelAsinmaYuzdesiValue.setGeometry(QRect(11, 43, 241, 50))
        self.labelAsinmaYuzdesiValue.setFont(font)
        self.labelAsinmaYuzdesiValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelAsinmaYuzdesiValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
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

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelTestereSagligi.setText(QCoreApplication.translate("Form", u"Testere Sa\u011fl\u0131\u011f\u0131 Y\u00fczdesi", None))
        self.labelTestereSagligiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelTespitEdilenKirik.setText(QCoreApplication.translate("Form", u"Tespit Edilen K\u0131r\u0131k Say\u0131s\u0131", None))
        self.labelTespitEdilenKirikValue.setText(QCoreApplication.translate("Form", u"12", None))
        self.labelTespitEdilenDis.setText(QCoreApplication.translate("Form", u"Tespit Edilen Di\u015f Say\u0131s\u0131", None))
        self.labelTespitEdilenDisValue.setText(QCoreApplication.translate("Form", u"235", None))
        self.labelTestereDurumu.setText(QCoreApplication.translate("Form", u"Testere Durumu", None))
        self.labelTestereDurumuValue.setText(QCoreApplication.translate("Form", u"Sa\u011fl\u0131kl\u0131", None))
        self.labelSmart.setText(QCoreApplication.translate("Form", u"SMART", None))
        self.labelSaw.setText(QCoreApplication.translate("Form", u"SAW", None))
        self.btnControlPanel.setText(QCoreApplication.translate("Form", u" Kontrol Paneli", None))
        self.btnPositioning.setText(QCoreApplication.translate("Form", u"Konumland\u0131rma", None))
        self.btnCamera.setText(QCoreApplication.translate("Form", u"Kamera Verileri", None))
        self.btnSensor.setText(QCoreApplication.translate("Form", u"Sens\u00f6r Verileri", None))
        self.btnTracking.setText(QCoreApplication.translate("Form", u"\u0130zleme", None))
        self.labelTestereDegisim.setText(QCoreApplication.translate("Form", u"\u015eerit Testerenin Son De\u011fi\u015fim Tarihi", None))
        self.labelKirikTespiti.setText(QCoreApplication.translate("Form", u"K\u0131r\u0131k Tespiti", None))
        self.labelIlerlemeHiziInfo.setText(QCoreApplication.translate("Form", u"12 adet k\u0131r\u0131k di\u015f tespit edildi.", None))
        self.labelIlerlemeHizi.setText(QCoreApplication.translate("Form", u"14.12.2025", None))
        self.labelCatlakTespiti.setText(QCoreApplication.translate("Form", u"\u00c7atlak Tespiti", None))
        self.labelCatlakTespitInfo.setText(QCoreApplication.translate("Form", u"\u00c7atlak tespit edilmedi.", None))
        self.labelAsinmaYuzdesi.setText(QCoreApplication.translate("Form", u"A\u015f\u0131nma Y\u00fczdesi", None))
        self.labelAsinmaYuzdesiValue.setText(QCoreApplication.translate("Form", u"16.35", None))
        self.labelDate.setText(QCoreApplication.translate("Form", u"14.12.2025 \u00c7ar\u015famba", None))
        self.labelTime.setText(QCoreApplication.translate("Form", u"12.30", None))
    # retranslateUi

