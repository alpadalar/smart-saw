from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QDateTime, QTime
from core.constants import TestereState


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-image: url('smart-saw/src/gui/images/background.png');\n"
"    background-repeat: no-repeat;\n"
"    background-position: center;\n"
"    background-attachment: fixed;\n"
"}\n"
"")
        self.centralwidget.setObjectName("centralwidget")
        self.sidebarFrame = QtWidgets.QFrame(self.centralwidget)
        self.sidebarFrame.setGeometry(QtCore.QRect(0, 0, 392, 1080))
        self.sidebarFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.sidebarFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.sidebarFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.sidebarFrame.setObjectName("sidebarFrame")
        self.labelSmart = QtWidgets.QLabel(self.sidebarFrame)
        self.labelSmart.setGeometry(QtCore.QRect(31, 32, 330, 73))
        self.labelSmart.setStyleSheet("QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"}\n"
"")
        self.labelSmart.setObjectName("labelSmart")
        self.labelSaw = QtWidgets.QLabel(self.sidebarFrame)
        self.labelSaw.setGeometry(QtCore.QRect(230, 32, 150, 73))
        self.labelSaw.setStyleSheet("QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: 100\n"
";\n"
"}\n"
"")
        self.labelSaw.setObjectName("labelSaw")
        self.lineSmartSaw = QtWidgets.QFrame(self.sidebarFrame)
        self.lineSmartSaw.setGeometry(QtCore.QRect(30, 110, 332, 3))
        self.lineSmartSaw.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1: 0, y1: 0, x2: 1, y2: 0,\n"
"        stop: 0 rgba(255, 255, 255, 0),\n"
"        stop: 0.5 rgba(255, 255, 255, 100),\n"
"        stop: 1 rgba(255, 255, 255, 0)\n"
"    );\n"
"    border: none;\n"
"}\n"
"")
        self.lineSmartSaw.setFrameShadow(QtWidgets.QFrame.Plain)
        self.lineSmartSaw.setLineWidth(1)
        self.lineSmartSaw.setFrameShape(QtWidgets.QFrame.HLine)
        self.lineSmartSaw.setObjectName("lineSmartSaw")
        self.btnControlPanel = QtWidgets.QPushButton(self.sidebarFrame)
        self.btnControlPanel.setGeometry(QtCore.QRect(26, 165, 355, 110))
        font = QtGui.QFont()
        font.setFamily("Plus Jakarta Sans")
        font.setPointSize(-1)
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(50)
        font.setStrikeOut(False)
        self.btnControlPanel.setFont(font)
        self.btnControlPanel.setMouseTracking(False)
        self.btnControlPanel.setStyleSheet("QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
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
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\control-panel-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\control-panel-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.btnControlPanel.setIcon(icon)
        self.btnControlPanel.setIconSize(QtCore.QSize(70, 70))
        self.btnControlPanel.setObjectName("btnControlPanel")
        self.btnPositioning = QtWidgets.QPushButton(self.sidebarFrame)
        self.btnPositioning.setGeometry(QtCore.QRect(26, 286, 355, 110))
        self.btnPositioning.setStyleSheet("QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
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
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\positioning-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\positioning-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.btnPositioning.setIcon(icon1)
        self.btnPositioning.setIconSize(QtCore.QSize(80, 80))
        self.btnPositioning.setObjectName("btnPositioning")
        self.btnCamera = QtWidgets.QPushButton(self.sidebarFrame)
        self.btnCamera.setGeometry(QtCore.QRect(26, 407, 355, 110))
        self.btnCamera.setStyleSheet("QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
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
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\camera-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\camera-icon-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.btnCamera.setIcon(icon2)
        self.btnCamera.setIconSize(QtCore.QSize(80, 80))
        self.btnCamera.setObjectName("btnCamera")
        self.btnSensor = QtWidgets.QPushButton(self.sidebarFrame)
        self.btnSensor.setGeometry(QtCore.QRect(26, 528, 355, 110))
        self.btnSensor.setStyleSheet("QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
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
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\sensor-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\sensor-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.btnSensor.setIcon(icon3)
        self.btnSensor.setIconSize(QtCore.QSize(80, 80))
        self.btnSensor.setObjectName("btnSensor")
        self.btnTracking = QtWidgets.QPushButton(self.sidebarFrame)
        self.btnTracking.setGeometry(QtCore.QRect(27, 649, 355, 110))
        self.btnTracking.setStyleSheet("QPushButton {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
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
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(r"smart-saw\src\gui\images\tracking-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap(r"smart-saw\src\gui\images\tracking-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.btnTracking.setIcon(icon4)
        self.btnTracking.setIconSize(QtCore.QSize(80, 80))
        self.btnTracking.setObjectName("btnTracking")
        self.notificationFrame = QtWidgets.QFrame(self.centralwidget)
        self.notificationFrame.setGeometry(QtCore.QRect(425, 38, 1465, 60))
        self.notificationFrame.setStyleSheet("QFrame#notificationFrame {\n"
"    background-color: rgba(26, 31, 55, 77);\n"
"    border-radius: 30px;\n"
"}")
        self.notificationFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.notificationFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.notificationFrame.setObjectName("notificationFrame")
        self.labelDate = QtWidgets.QLabel(self.notificationFrame)
        self.labelDate.setGeometry(QtCore.QRect(55, 13, 300, 34))
        self.labelDate.setStyleSheet("QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 24px;\n"
"    font-weight: light;\n"
"}\n"
"")
        self.labelDate.setObjectName("labelDate")
        self.labelTime = QtWidgets.QLabel(self.notificationFrame)
        self.labelTime.setGeometry(QtCore.QRect(1348, 13, 62, 34))
        self.labelTime.setStyleSheet("QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 24px;\n"
"    font-weight: light;\n"
"}\n"
"")
        self.labelTime.setObjectName("labelTime")
        self.cuttingFrame = QtWidgets.QFrame(self.centralwidget)
        self.cuttingFrame.setGeometry(QtCore.QRect(425, 127, 440, 344))
        self.cuttingFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.cuttingFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.cuttingFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.cuttingFrame.setObjectName("cuttingFrame")
        self.labelCuttingMode = QtWidgets.QLabel(self.cuttingFrame)
        self.labelCuttingMode.setGeometry(QtCore.QRect(27, 26, 150, 34))
        self.labelCuttingMode.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelCuttingMode.setObjectName("labelCuttingMode")
        self.btnManualMode = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnManualMode.setGeometry(QtCore.QRect(18, 87, 180, 45))
        self.btnManualMode.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 52px;\n"
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
        self.btnManualMode.setCheckable(True)
        self.btnManualMode.setObjectName("btnManualMode")
        self.btnAiMode = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnAiMode.setGeometry(QtCore.QRect(241, 87, 180, 45))
        self.btnAiMode.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 32px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnAiMode.setCheckable(True)
        self.btnAiMode.setObjectName("btnAiMode")
        self.btnFuzzyMode = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnFuzzyMode.setGeometry(QtCore.QRect(18, 150, 180, 45))
        self.btnFuzzyMode.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 60px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnFuzzyMode.setCheckable(True)
        self.btnFuzzyMode.setObjectName("btnFuzzyMode")
        self.btnExpertSystemMode = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnExpertSystemMode.setGeometry(QtCore.QRect(241, 150, 180, 45))
        self.btnExpertSystemMode.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 22px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnExpertSystemMode.setCheckable(True)
        self.btnExpertSystemMode.setObjectName("btnExpertSystemMode")
        self.labelCuttingSpeed = QtWidgets.QLabel(self.cuttingFrame)
        self.labelCuttingSpeed.setGeometry(QtCore.QRect(27, 222, 150, 34))
        self.labelCuttingSpeed.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelCuttingSpeed.setObjectName("labelCuttingSpeed")
        self.btnSlowSpeed = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnSlowSpeed.setGeometry(QtCore.QRect(19, 274, 120, 45))
        self.btnSlowSpeed.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 30px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnSlowSpeed.setCheckable(True)
        self.btnSlowSpeed.setObjectName("btnSlowSpeed")
        self.btnNormalSpeed = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnNormalSpeed.setGeometry(QtCore.QRect(160, 274, 120, 45))
        self.btnNormalSpeed.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 16px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnNormalSpeed.setCheckable(True)
        self.btnNormalSpeed.setObjectName("btnNormalSpeed")
        self.btnFastSpeed = QtWidgets.QPushButton(self.cuttingFrame)
        self.btnFastSpeed.setGeometry(QtCore.QRect(300, 274, 120, 45))
        self.btnFastSpeed.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"    border: 2px solid #F4F6FC;\n"
"    padding-left: 38px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnFastSpeed.setCheckable(True)
        self.btnFastSpeed.setObjectName("btnFastSpeed")
        self.headHeightFrame = QtWidgets.QFrame(self.centralwidget)
        self.headHeightFrame.setGeometry(QtCore.QRect(892, 127, 229, 344))
        self.headHeightFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.headHeightFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.headHeightFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.headHeightFrame.setObjectName("headHeightFrame")
        self.labelHeadHeight = QtWidgets.QLabel(self.headHeightFrame)
        self.labelHeadHeight.setGeometry(QtCore.QRect(27, 26, 200, 34))
        self.labelHeadHeight.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelHeadHeight.setObjectName("labelHeadHeight")
        self.labelValue = QtWidgets.QLabel(self.headHeightFrame)
        self.labelValue.setGeometry(QtCore.QRect(148, 175, 60, 54))
        self.labelValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelValue.setObjectName("labelValue")
        self.labelmm = QtWidgets.QLabel(self.headHeightFrame)
        self.labelmm.setGeometry(QtCore.QRect(170, 210, 41, 34))
        self.labelmm.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: light;\n"
"    font-size: 24px;\n"
"}")
        self.labelmm.setObjectName("labelmm")
        self.bandDeviationFrame = QtWidgets.QFrame(self.centralwidget)
        self.bandDeviationFrame.setGeometry(QtCore.QRect(1148, 127, 401, 344))
        self.bandDeviationFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandDeviationFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.bandDeviationFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bandDeviationFrame.setObjectName("bandDeviationFrame")
        self.labelHeadHeight_2 = QtWidgets.QLabel(self.bandDeviationFrame)
        self.labelHeadHeight_2.setGeometry(QtCore.QRect(27, 26, 170, 34))
        self.labelHeadHeight_2.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelHeadHeight_2.setObjectName("labelHeadHeight_2")
        self.infoFrame = QtWidgets.QFrame(self.bandDeviationFrame)
        self.infoFrame.setGeometry(QtCore.QRect(59, 199, 285, 109))
        self.infoFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.infoFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.infoFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.infoFrame.setObjectName("infoFrame")
        self.label = QtWidgets.QLabel(self.infoFrame)
        self.label.setGeometry(QtCore.QRect(32, 20, 221, 20))
        self.label.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252, 151);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.infoFrame)
        self.label_2.setGeometry(QtCore.QRect(91, 46, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.label_2.setObjectName("label_2")
        self.systemStatusFrame = QtWidgets.QFrame(self.centralwidget)
        self.systemStatusFrame.setGeometry(QtCore.QRect(1576, 127, 313, 344))
        self.systemStatusFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.systemStatusFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.systemStatusFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.systemStatusFrame.setObjectName("systemStatusFrame")
        self.labelHeadHeight_3 = QtWidgets.QLabel(self.systemStatusFrame)
        self.labelHeadHeight_3.setGeometry(QtCore.QRect(27, 26, 190, 34))
        self.labelHeadHeight_3.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelHeadHeight_3.setObjectName("labelHeadHeight_3")
        self.label_3 = QtWidgets.QLabel(self.systemStatusFrame)
        self.label_3.setGeometry(QtCore.QRect(61, 132, 191, 31))
        self.label_3.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 24px;\n"
"}")
        self.label_3.setObjectName("label_3")
        self.iconStatus = QtWidgets.QLabel(self.systemStatusFrame)
        self.iconStatus.setGeometry(QtCore.QRect(121, 230, 71, 71))
        self.iconStatus.setStyleSheet("QLabel {\n"
"    border: none;\n"
"    background: transparent;\n"
"}\n"
"")
        self.iconStatus.setText("")
        self.iconStatus.setPixmap(QtGui.QPixmap("smart-saw\src\gui\images\okey-icon.svg"))
        self.iconStatus.setObjectName("iconStatus")
        self.bandCuttingSpeedFrame = QtWidgets.QFrame(self.centralwidget)
        self.bandCuttingSpeedFrame.setGeometry(QtCore.QRect(425, 486, 551, 344))
        self.bandCuttingSpeedFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandCuttingSpeedFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.bandCuttingSpeedFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bandCuttingSpeedFrame.setObjectName("bandCuttingSpeedFrame")
        self.labelHeadHeight_4 = QtWidgets.QLabel(self.bandCuttingSpeedFrame)
        self.labelHeadHeight_4.setGeometry(QtCore.QRect(31, 27, 270, 45))
        self.labelHeadHeight_4.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelHeadHeight_4.setObjectName("labelHeadHeight_4")
        self.label_4 = QtWidgets.QLabel(self.bandCuttingSpeedFrame)
        self.label_4.setGeometry(QtCore.QRect(31, 106, 255, 51))
        self.label_4.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252, 151);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 22px;\n"
"}")
        self.label_4.setObjectName("label_4")
        self.infoFrame_2 = QtWidgets.QFrame(self.bandCuttingSpeedFrame)
        self.infoFrame_2.setGeometry(QtCore.QRect(31, 200, 217, 109))
        self.infoFrame_2.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.infoFrame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.infoFrame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.infoFrame_2.setObjectName("infoFrame_2")
        self.label_6 = QtWidgets.QLabel(self.infoFrame_2)
        self.label_6.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.label_6.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252, 151);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.infoFrame_2)
        self.label_7.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.label_7.setFont(font)
        self.label_7.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.label_7.setObjectName("label_7")
        self.bandDescentSpeedFrame = QtWidgets.QFrame(self.centralwidget)
        self.bandDescentSpeedFrame.setGeometry(QtCore.QRect(998, 486, 551, 344))
        self.bandDescentSpeedFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandDescentSpeedFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.bandDescentSpeedFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bandDescentSpeedFrame.setObjectName("bandDescentSpeedFrame")
        self.labelHeadHeight_5 = QtWidgets.QLabel(self.bandDescentSpeedFrame)
        self.labelHeadHeight_5.setGeometry(QtCore.QRect(31, 27, 270, 45))
        self.labelHeadHeight_5.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelHeadHeight_5.setObjectName("labelHeadHeight_5")
        self.label_5 = QtWidgets.QLabel(self.bandDescentSpeedFrame)
        self.label_5.setGeometry(QtCore.QRect(31, 106, 255, 51))
        self.label_5.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252, 151);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 22px;\n"
"}")
        self.label_5.setObjectName("label_5")
        self.infoFrame_3 = QtWidgets.QFrame(self.bandDescentSpeedFrame)
        self.infoFrame_3.setGeometry(QtCore.QRect(31, 200, 217, 109))
        self.infoFrame_3.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.infoFrame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.infoFrame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.infoFrame_3.setObjectName("infoFrame_3")
        self.label_8 = QtWidgets.QLabel(self.infoFrame_3)
        self.label_8.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.label_8.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252, 151);\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.infoFrame_3)
        self.label_9.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.label_9.setObjectName("label_9")
        self.logViewerFrame = QtWidgets.QFrame(self.centralwidget)
        self.logViewerFrame.setGeometry(QtCore.QRect(1576, 486, 313, 580))
        self.logViewerFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.logViewerFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.logViewerFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.logViewerFrame.setObjectName("logViewerFrame")
        self.labelLogViewer = QtWidgets.QLabel(self.logViewerFrame)
        self.labelLogViewer.setGeometry(QtCore.QRect(27, 26, 210, 34))
        self.labelLogViewer.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelLogViewer.setObjectName("labelLogViewer")
        self.logViewerScroll = QtWidgets.QScrollArea(self.logViewerFrame)
        self.logViewerScroll.setGeometry(QtCore.QRect(30, 90, 251, 461))
        self.logViewerScroll.setStyleSheet("QScrollArea {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}\n"
"\n"
"QWidget#scrollAreaWidgetContents {\n"
"    background-color: transparent;\n"
"}\n"
"")
        self.logViewerScroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.logViewerScroll.setWidgetResizable(True)
        self.logViewerScroll.setObjectName("logViewerScroll")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 251, 461))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_10 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_10.setStyleSheet("QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20px;\n"
"    font-weight: normal;\n"
"    background-color: rgba(6, 12, 41, 0.2); /* %20 opak */\n"
"    border-radius: 20px;\n"
"    padding: 10px 15px;\n"
"}\n"
"")
        self.label_10.setObjectName("label_10")
        self.verticalLayout.addWidget(self.label_10)
        self.label_12 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_12.setStyleSheet("QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20px;\n"
"    font-weight: normal;\n"
"    background-color: rgba(6, 12, 41, 0.2); /* %20 opak */\n"
"    border-radius: 20px;\n"
"    padding: 10px 15px;\n"
"}\n"
"")
        self.label_12.setObjectName("label_12")
        self.verticalLayout.addWidget(self.label_12)
        self.label_11 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_11.setStyleSheet("QLabel {\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20px;\n"
"    font-weight: normal;\n"
"    background-color: rgba(6, 12, 41, 0.2); /* %20 opak */\n"
"    border-radius: 20px;\n"
"    padding: 10px 15px;\n"
"}\n"
"")
        self.label_11.setObjectName("label_11")
        self.logViewerScroll.setWidget(self.scrollAreaWidgetContents)
        self.cuttingControlFrame = QtWidgets.QFrame(self.centralwidget)
        self.cuttingControlFrame.setGeometry(QtCore.QRect(425, 845, 1127, 221))
        self.cuttingControlFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.cuttingControlFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.cuttingControlFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.cuttingControlFrame.setObjectName("cuttingControlFrame")
        self.toolButton = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolButton.setEnabled(True)
        self.toolButton.setGeometry(QtCore.QRect(27, 27, 220, 170))
        self.toolButton.setStyleSheet("QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"    border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20pt;\n"
"    font-weight: 100;\n"
"    icon-size: 115px;\n"
"    padding-top: 7px;\n"
"    padding-bottom: 15px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\cutting-start-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon5)
        self.toolButton.setIconSize(QtCore.QSize(105, 105))
        self.toolButton.setCheckable(True)
        self.toolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolButton.setObjectName("toolButton")
        self.toolButton_2 = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolButton_2.setGeometry(QtCore.QRect(312, 27, 220, 170))
        self.toolButton_2.setStyleSheet("QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"    border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20pt;\n"
"    font-weight: 100;\n"
"    icon-size: 115px;\n"
"    padding-top: 7px;\n"
"    padding-bottom: 15px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"    border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20pt;\n"
"    font-weight: 100;\n"
"    icon-size: 115px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\cutting-stop-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_2.setIcon(icon6)
        self.toolButton_2.setIconSize(QtCore.QSize(105, 105))
        self.toolButton_2.setCheckable(True)
        self.toolButton_2.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolButton_2.setObjectName("toolButton_2")
        self.toolButton_3 = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolButton_3.setGeometry(QtCore.QRect(596, 27, 220, 170))
        self.toolButton_3.setStyleSheet("QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"    border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20pt;\n"
"    font-weight: 100;\n"
"    icon-size: 115px;\n"
"    padding-top: 7px;\n"
"    padding-bottom: 15px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\coolant-liquid-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_3.setIcon(icon7)
        self.toolButton_3.setIconSize(QtCore.QSize(105, 105))
        self.toolButton_3.setCheckable(True)
        self.toolButton_3.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolButton_3.setObjectName("toolButton_3")
        self.toolButton_4 = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolButton_4.setGeometry(QtCore.QRect(881, 24, 220, 170))
        self.toolButton_4.setStyleSheet("QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"    border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-size: 20pt;\n"
"    font-weight: 100;\n"
"    icon-size: 115px;\n"
"    padding-top: 7px;\n"
"    padding-bottom: 15px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"    background-color: #950952;\n"
"}")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("smart-saw\src\gui\images\sawdust-cleaning-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_4.setIcon(icon8)
        self.toolButton_4.setIconSize(QtCore.QSize(105, 105))
        self.toolButton_4.setCheckable(True)
        self.toolButton_4.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolButton_4.setObjectName("toolButton_4")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1920, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.headHeightBar = QtWidgets.QProgressBar(self.headHeightFrame)
        self.headHeightBar.setGeometry(QtCore.QRect(27, 78, 54, 250))
        self.headHeightBar.setOrientation(QtCore.Qt.Vertical)
        self.headHeightBar.setMinimum(0)
        self.headHeightBar.setMaximum(300)
        self.headHeightBar.setValue(108)  # Varsayılan değer
        self.headHeightBar.setTextVisible(False)
        self.headHeightBar.setStyleSheet('''
            QProgressBar {
                border: none;
                border-radius: 25px;
                background-color: rgba(149,9,82,0.2);
            }
            QProgressBar::chunk {
                background-color: #950952;
                border-radius: 25px;
                margin: 0px;
            }
        ''')

        # --- Kafa yüksekliği label'ları ---
        bar_x = 27
        bar_y = 78
        bar_width = 54
        bar_height = 250
        label_x = bar_x + bar_width + 10
        label_width = 40
        # MAX
        self.headHeightMaxValue = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightMaxValue.setText(str(self.headHeightBar.maximum()))
        self.headHeightMaxValue.setStyleSheet('color: #BFC3D9; font-size: 20px; font-weight: 600; background: transparent;')
        self.headHeightMaxValue.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.headHeightMaxValue.setGeometry(label_x, bar_y - 5, label_width, 20)
        self.headHeightMaxMM = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightMaxMM.setText("mm")
        self.headHeightMaxMM.setStyleSheet('color: #BFC3D9; font-size: 14px; font-weight: 400; background: transparent;')
        self.headHeightMaxMM.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.headHeightMaxMM.setGeometry(label_x, bar_y + 13, label_width, 15)
        # MID
        mid_val = int(self.headHeightBar.maximum() / 2)
        mid_y = bar_y + bar_height // 2 - 10
        self.headHeightMidValue = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightMidValue.setText(str(mid_val))
        self.headHeightMidValue.setStyleSheet('color: #BFC3D9; font-size: 20px; font-weight: 600; background: transparent;')
        self.headHeightMidValue.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.headHeightMidValue.setGeometry(label_x, mid_y, label_width, 20)
        self.headHeightMidMM = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightMidMM.setText("mm")
        self.headHeightMidMM.setStyleSheet('color: #BFC3D9; font-size: 14px; font-weight: 400; background: transparent;')
        self.headHeightMidMM.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.headHeightMidMM.setGeometry(label_x, mid_y + 18, label_width, 15)
        # ZERO
        zero_y = bar_y + bar_height - 20
        self.headHeightZeroValue = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightZeroValue.setText("0")
        self.headHeightZeroValue.setStyleSheet('color: #BFC3D9; font-size: 20px; font-weight: 600; background: transparent;')
        self.headHeightZeroValue.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.headHeightZeroValue.setGeometry(label_x, zero_y, label_width, 20)
        self.headHeightZeroMM = QtWidgets.QLabel(self.headHeightFrame)
        self.headHeightZeroMM.setText("mm")
        self.headHeightZeroMM.setStyleSheet('color: #BFC3D9; font-size: 14px; font-weight: 400; background: transparent;')
        self.headHeightZeroMM.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.headHeightZeroMM.setGeometry(label_x, zero_y + 18, label_width, 15)

        # bandDeviationFrame içine SVG ekle
        self.bandDeviationLines = QtWidgets.QLabel(self.bandDeviationFrame)
        self.bandDeviationLines.setGeometry(QtCore.QRect(27, 78, 278, 76))
        self.bandDeviationLines.setPixmap(QtGui.QPixmap('smart-saw/src/gui/images/band-deviation-lines.svg'))
        self.bandDeviationLines.setScaledContents(True)
        self.bandDeviationLines.setStyleSheet("background: transparent;")

        self.bandDeviationGraph = BandDeviationGraphWidget(self.bandDeviationFrame)
        self.bandDeviationGraph.setGeometry(QtCore.QRect(27, 78, 278, 76))
        # Örnek veri ile test (sonra dışarıdan set_data ile güncellenecek)
        self.bandDeviationGraph.set_data([0, 0.2, -0.1, 0.3, -0.2, 0, 0.1, -0.3, 0.2, 0])

        # Şerit sapması max/min label'ları (güncellenmiş x pozisyonu)
        label_font = 'font-size: 16px; font-weight: 600;'
        label_color = 'color: rgba(244,246,252,0.6); background: transparent;'
        label_style = f'{label_color} {label_font}'
        label_width = 60
        label_x = 300  # Daha sağda, grafiğin sağındaki boş alanda
        # Üstteki label
        self.bandDeviationMaxLabel = QtWidgets.QLabel(self.bandDeviationFrame)
        self.bandDeviationMaxLabel.setText("3.20")
        self.bandDeviationMaxLabel.setStyleSheet(label_style)
        self.bandDeviationMaxLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.bandDeviationMaxLabel.setGeometry(label_x, 78, label_width, 24)
        # Alttaki label
        self.bandDeviationMinLabel = QtWidgets.QLabel(self.bandDeviationFrame)
        self.bandDeviationMinLabel.setText("-3.50")
        self.bandDeviationMinLabel.setStyleSheet(label_style)
        self.bandDeviationMinLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.bandDeviationMinLabel.setGeometry(label_x, 138, label_width, 24)

        # Şerit Kesme Hızı için progress bar zaten ekli
        self.circularProgressBar = CircularProgressBar(self.bandCuttingSpeedFrame, min_value=0, max_value=100, value=78)
        self.circularProgressBar.move(276, 49)
        self.circularProgressBar.show()
        # Şerit İnme Hızı için de aynı progress barı ekle
        self.descentCircularProgressBar = CircularProgressBar(self.bandDescentSpeedFrame, min_value=0, max_value=100, value=50)
        self.descentCircularProgressBar.move(276, 49)
        self.descentCircularProgressBar.show()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.labelSmart.setText(_translate("MainWindow", "SMART"))
        self.labelSaw.setText(_translate("MainWindow", "SAW"))
        self.btnControlPanel.setText(_translate("MainWindow", " Kontrol Paneli"))
        self.btnPositioning.setText(_translate("MainWindow", "Konumlandırma"))
        self.btnCamera.setText(_translate("MainWindow", "Kamera Verileri"))
        self.btnSensor.setText(_translate("MainWindow", "Sensör Verileri"))
        self.btnTracking.setText(_translate("MainWindow", "İzleme"))
        self.labelDate.setText(_translate("MainWindow", "14.12.2025 Çarşamba"))
        self.labelTime.setText(_translate("MainWindow", "12.30"))
        self.labelCuttingMode.setText(_translate("MainWindow", "Kesim Modu"))
        self.btnManualMode.setText(_translate("MainWindow", "Manuel"))
        self.btnAiMode.setText(_translate("MainWindow", "Yapay Zeka"))
        self.btnFuzzyMode.setText(_translate("MainWindow", "Fuzzy"))
        self.btnExpertSystemMode.setText(_translate("MainWindow", "Uzman Sistem"))
        self.labelCuttingSpeed.setText(_translate("MainWindow", "Kesim Hızı"))
        self.btnSlowSpeed.setText(_translate("MainWindow", "Yavaş"))
        self.btnNormalSpeed.setText(_translate("MainWindow", "Standart"))
        self.btnFastSpeed.setText(_translate("MainWindow", "Hızlı"))
        self.labelHeadHeight.setText(_translate("MainWindow", "Kafa Yüksekliği"))
        self.labelValue.setText(_translate("MainWindow", "108"))
        self.labelmm.setText(_translate("MainWindow", "mm"))
        self.labelHeadHeight_2.setText(_translate("MainWindow", "Şerit Sapması"))
        self.label.setText(_translate("MainWindow", "Maksimum Şerit Sapması"))
        self.label_2.setText(_translate("MainWindow", "16.35"))
        self.labelHeadHeight_3.setText(_translate("MainWindow", "Sistem Durumu"))
        self.label_3.setText(_translate("MainWindow", "Her Şey Yolunda !"))
        self.labelHeadHeight_4.setText(_translate("MainWindow", "Şerit Kesme Hızı"))
        self.label_4.setText(_translate("MainWindow", "Başlangıç hızını\n"
"belirlemek için tıklayın."))
        self.label_6.setText(_translate("MainWindow", "Şerit Motor Akım"))
        self.label_7.setText(_translate("MainWindow", "16.35"))
        self.labelHeadHeight_5.setText(_translate("MainWindow", "Şerit İnme Hızı"))
        self.label_5.setText(_translate("MainWindow", "Başlangıç hızını\n"
"belirlemek için tıklayın."))
        self.label_8.setText(_translate("MainWindow", "Şerit Motor Akım"))
        self.label_9.setText(_translate("MainWindow", "16.35"))
        self.labelLogViewer.setText(_translate("MainWindow", "Çalışma Günlüğü"))
        self.label_10.setText(_translate("MainWindow", "TextLabel"))
        self.label_12.setText(_translate("MainWindow", "TextLabel"))
        self.label_11.setText(_translate("MainWindow", "TextLabel"))
        self.toolButton.setText(_translate("MainWindow", "Kesim Başlat"))
        self.toolButton_2.setText(_translate("MainWindow", "Kesim Durdur"))
        self.toolButton_3.setText(_translate("MainWindow", "Soğutma Sıvısı"))
        self.toolButton_4.setText(_translate("MainWindow", "Talaş Temizlik"))

    def update_max_band_deviation(self, sapma_listesi):
        if not sapma_listesi:
            self.label_2.setText("-")
            return
        max_val = max(sapma_listesi)
        self.label_2.setText(f"{max_val:.2f}")

class CircularProgressBar(QtWidgets.QWidget):
    def __init__(self, parent=None, min_value=0, max_value=100, value=0):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.setMinimumSize(270, 270)
        self.setMaximumSize(270, 270)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        margin = 20
        arc_rect = rect.adjusted(margin, margin, -margin, -margin)
        # Arka plan çemberi (çok koyu ve şeffaf)
        pen_bg = QtGui.QPen(QtGui.QColor(60, 6, 33, 60))  # Çok koyu ve şeffaf
        pen_bg.setWidth(18)
        pen_bg.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(arc_rect, 225 * 16, -270 * 16)
        # Progress bar (linear gradient, yukarıdan aşağıya)
        linear_gradient = QtGui.QLinearGradient(arc_rect.center().x(), arc_rect.top(), arc_rect.center().x(), arc_rect.bottom())
        linear_gradient.setColorAt(0.0, QtGui.QColor('#950952'))
        linear_gradient.setColorAt(1.0, QtGui.QColor(149, 9, 82, 0))
        pen = QtGui.QPen(QtGui.QBrush(linear_gradient), 18)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        angle_span = int(270 * 16 * (self.value - self.min_value) / (self.max_value - self.min_value))
        painter.drawArc(arc_rect, 225 * 16, -angle_span)
        # Ortadaki değer
        painter.setPen(QtGui.QColor('#F4F6FC'))
        font = QtGui.QFont('Plus Jakarta Sans', 40, QtGui.QFont.Bold)
        painter.setFont(font)
        value_str = f"{self.value:.2f}"
        text_rect = rect.adjusted(0, 60, 0, -60)
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, value_str)
        painter.end()

class ControlPanelWindow(QtWidgets.QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Timer'ı başlat (tarih ve saat güncellemesi için)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # her saniye güncelle
        
        # Button bağlantıları
        self.setup_connections()
        
        # Log viewer'ı temizle
        self.clear_log_viewer()
        
    def clear_log_viewer(self):
        """Log viewer'daki örnek label'ları temizle"""
        while self.ui.verticalLayout.count():
            item = self.ui.verticalLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
    def setup_connections(self):
        # Kesim modu butonları
        self.ui.btnManualMode.setCheckable(True)
        self.ui.btnAiMode.setCheckable(True)
        self.ui.btnFuzzyMode.setCheckable(True)
        self.ui.btnExpertSystemMode.setCheckable(True)
        self.mode_buttons = [
            self.ui.btnManualMode,
            self.ui.btnAiMode,
            self.ui.btnFuzzyMode,
            self.ui.btnExpertSystemMode
        ]
        for btn in self.mode_buttons:
            btn.clicked.connect(self.handle_mode_buttons)
        
        # Hız butonları
        self.ui.btnSlowSpeed.setCheckable(True)
        self.ui.btnNormalSpeed.setCheckable(True)
        self.ui.btnFastSpeed.setCheckable(True)
        self.speed_buttons = [
            self.ui.btnSlowSpeed,
            self.ui.btnNormalSpeed,
            self.ui.btnFastSpeed
        ]
        for btn in self.speed_buttons:
            btn.clicked.connect(self.handle_speed_buttons)
        self.ui.btnSlowSpeed.clicked.connect(lambda: self.set_speed_and_log(50, 25))
        self.ui.btnNormalSpeed.clicked.connect(lambda: self.set_speed_and_log(80, 50))
        self.ui.btnFastSpeed.clicked.connect(lambda: self.set_speed_and_log(100, 65))
        
        # Kesim başlat/durdur butonları
        self.ui.toolButton.setCheckable(True)
        self.ui.toolButton_2.setCheckable(True)
        self.ui.toolButton.clicked.connect(self.handle_start_stop_buttons)
        self.ui.toolButton_2.clicked.connect(self.handle_start_stop_buttons)
        self.ui.toolButton.clicked.connect(lambda: self.add_log_message('Kesim Başladı !'))
        self.ui.toolButton_2.clicked.connect(lambda: self.add_log_message('Kesim Bitti !'))
        
        # Soğutma sıvısı ve talaş temizlik butonları için bağlantı
        self.ui.toolButton_3.clicked.connect(self.handle_coolant_button)
        self.ui.toolButton_4.clicked.connect(self.handle_cleaning_button)
        self.reset_button_states()

    def handle_mode_buttons(self):
        sender = self.sender()
        for btn in self.mode_buttons:
            btn.setChecked(btn == sender)
        # Log mesajı
        if sender == self.ui.btnManualMode:
            self.add_log_message('Kesim modu "Manuel" olarak değiştirildi.')
        elif sender == self.ui.btnAiMode:
            self.add_log_message('Kesim modu "Yapay Zeka" olarak değiştirildi.')
        elif sender == self.ui.btnFuzzyMode:
            self.add_log_message('Kesim modu "Fuzzy" olarak değiştirildi.')
        elif sender == self.ui.btnExpertSystemMode:
            self.add_log_message('Kesim modu "Uzman Sistem" olarak değiştirildi.')

    def handle_speed_buttons(self):
        sender = self.sender()
        for btn in self.speed_buttons:
            btn.setChecked(btn == sender)
        # Hız logları zaten set_speed_and_log ile ekleniyor

    def handle_start_stop_buttons(self):
        sender = self.sender()
        if sender == self.ui.toolButton:
            self.ui.toolButton_2.setChecked(False)
        elif sender == self.ui.toolButton_2:
            self.ui.toolButton.setChecked(False)

    def set_speed_and_log(self, kesme_hizi, inme_hizi):
        self.add_log_message(f'Şerit Kesme Hızı "{kesme_hizi:.2f}" olarak ayarlandı!')
        self.add_log_message(f'Şerit İnme Hızı "{inme_hizi:.2f}" olarak ayarlandı!')
        # Burada ileride: self.controller.controller_factory.set_kesme_hizi(kesme_hizi) gibi fonksiyonlar çağrılabilir

    def reset_button_states(self):
        """Tüm butonları başlangıç durumuna getirir"""
        # Mode butonlarını sıfırla
        for btn in self.mode_buttons:
            btn.setChecked(False)
        
        # Hız butonlarını sıfırla
        for btn in self.speed_buttons:
            btn.setChecked(False)
        
        # Kontrol butonlarını sıfırla
        self.ui.toolButton.setChecked(False)
        self.ui.toolButton_2.setChecked(False)
        self.ui.toolButton_3.setChecked(False)
        self.ui.toolButton_4.setChecked(False)

    def update_datetime(self):
        current_datetime = QDateTime.currentDateTime()
        self.ui.labelDate.setText(current_datetime.toString("dd.MM.yyyy dddd"))
        self.ui.labelTime.setText(current_datetime.toString("HH:mm"))
        
    def add_log_message(self, message: str, level: str = 'INFO'):
        """Log mesajı ekler"""
        try:
            # Saat bilgisi için label
            now = QTime.currentTime().toString('HH:mm')
            saat_label = QtWidgets.QLabel(now)
            saat_label.setStyleSheet('color: #F4F6FC; font-size: 18px; font-weight: bold; background: transparent;')
            self.ui.verticalLayout.addWidget(saat_label)
            # Mesaj için label
            msg_label = QtWidgets.QLabel(message)
            msg_label.setStyleSheet('color: #F4F6FC; font-size: 18px; font-weight: normal; background: transparent;')
            msg_label.setWordWrap(True)  # Uzun mesajları alt satıra geçir
            self.ui.verticalLayout.addWidget(msg_label)
            # Scroll alanını en alta kaydır
            scroll_bar = self.ui.logViewerScroll.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())
        except Exception as e:
            print(f"Log ekleme hatası: {e}", file=sys.stderr)

    def handle_coolant_button(self):
        if self.ui.toolButton_3.isChecked():
            self.add_log_message('Soğutma Sıvısı aktif edildi.')
        else:
            self.add_log_message('Soğutma Sıvısı durduruldu.')

    def handle_cleaning_button(self):
        if self.ui.toolButton_4.isChecked():
            self.add_log_message('Talaş Temizlik aktif edildi.')
        else:
            self.add_log_message('Talaş Temizlik durduruldu.')
            
class BandDeviationGraphWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sapma_listesi = []  # Şerit sapması verileri
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMinimumSize(278, 76)
        self.setMaximumSize(278, 76)

    def set_data(self, sapma_listesi):
        self.sapma_listesi = sapma_listesi
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor('#F4F6FC'))
        pen.setWidth(5)
        painter.setPen(pen)
        # X ve Y aralığı
        x_start = 0
        x_end = 230
        y_min = 90
        y_max = 137
        n = len(self.sapma_listesi)
        if n < 2:
            return
        # X aralığını veriye böl
        for i in range(n-1):
            x1 = 31 + int((x_end - x_start) * i / (n-1))
            x2 = 31 + int((x_end - x_start) * (i+1) / (n-1))
            # Sapma değerini y aralığına ölçekle
            s1 = self.sapma_listesi[i]
            s2 = self.sapma_listesi[i+1]
            # -1 ile 1 arası normalize, 0 ortada
            y1 = int((y_max + y_min)/2 - s1 * (y_max - y_min)/2)
            y2 = int((y_max + y_min)/2 - s2 * (y_max - y_min)/2)
            painter.drawLine(x1, y1, x2, y2)
        painter.end()