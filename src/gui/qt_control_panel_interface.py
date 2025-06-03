from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.showFullScreen()
        MainWindow.setStyleSheet("")
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-image: url(\"src/gui/images/background.png\");\n"
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
        icon.addPixmap(QtGui.QPixmap("src/gui/images/control-panel-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("src/gui/images/control-panel-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon1.addPixmap(QtGui.QPixmap("src/gui/images/positioning-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("src/gui/images/positioning-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon2.addPixmap(QtGui.QPixmap("src/gui/images/camera-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("src/gui/images/camera-icon-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon3.addPixmap(QtGui.QPixmap("src/gui/images/sensor-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("src/gui/images/sensor-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon4.addPixmap(QtGui.QPixmap("src/gui/images/tracking-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap("src/gui/images/tracking-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        self.labelTime.setGeometry(QtCore.QRect(1348, 13, 80, 34))
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

        # Progress bar
        self.progressBarHeight = QtWidgets.QProgressBar(self.headHeightFrame)
        self.progressBarHeight.setGeometry(QtCore.QRect(27, 78, 50, 250))
        self.progressBarHeight.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 25px;
                background-color: rgba(149, 9, 82, 0.2);
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 25px;
                background-color: #950952;
            }
        """)
        self.progressBarHeight.setOrientation(QtCore.Qt.Vertical)
        self.progressBarHeight.setRange(0, 420)
        self.progressBarHeight.setValue(0)
        self.progressBarHeight.setTextVisible(False)
        self.progressBarHeight.setObjectName("progressBarHeight")

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
        self.labelBandDeviation = QtWidgets.QLabel(self.bandDeviationFrame)
        self.labelBandDeviation.setGeometry(QtCore.QRect(27, 26, 170, 34))
        self.labelBandDeviation.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelBandDeviation.setObjectName("labelBandDeviation")
        self.maxBandDeviationFrame = QtWidgets.QFrame(self.bandDeviationFrame)
        self.maxBandDeviationFrame.setGeometry(QtCore.QRect(59, 199, 285, 109))
        self.maxBandDeviationFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.maxBandDeviationFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.maxBandDeviationFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.maxBandDeviationFrame.setObjectName("maxBandDeviationFrame")
        self.labelMaxBandDeviation = QtWidgets.QLabel(self.maxBandDeviationFrame)
        self.labelMaxBandDeviation.setGeometry(QtCore.QRect(32, 20, 221, 20))
        self.labelMaxBandDeviation.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelMaxBandDeviation.setObjectName("labelMaxBandDeviation")
        self.labelMaxBandDeviationValue = QtWidgets.QLabel(self.maxBandDeviationFrame)
        self.labelMaxBandDeviationValue.setGeometry(QtCore.QRect(91, 46, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelMaxBandDeviationValue.setFont(font)
        self.labelMaxBandDeviationValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelMaxBandDeviationValue.setObjectName("labelMaxBandDeviationValue")
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
        self.labelSystemStatus = QtWidgets.QLabel(self.systemStatusFrame)
        self.labelSystemStatus.setGeometry(QtCore.QRect(27, 26, 190, 34))
        self.labelSystemStatus.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelSystemStatus.setObjectName("labelSystemStatus")
        self.labelSystemStatusInfo = QtWidgets.QLabel(self.systemStatusFrame)
        self.labelSystemStatusInfo.setGeometry(QtCore.QRect(61, 132, 191, 60))
        self.labelSystemStatusInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: rgba(244, 246, 252);\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: medium;\n"
"    font-size: 24px;\n"
"}")
        self.labelSystemStatusInfo.setWordWrap(True)
        self.labelSystemStatusInfo.setObjectName("labelSystemStatusInfo")
        self.iconStatus = QtWidgets.QLabel(self.systemStatusFrame)
        self.iconStatus.setGeometry(QtCore.QRect(121, 230, 71, 71))
        self.iconStatus.setStyleSheet("QLabel {\n"
"    border: none;\n"
"    background: transparent;\n"
"}\n"
"")
        self.iconStatus.setText("")
        self.iconStatus.setPixmap(QtGui.QPixmap("src/gui/images/okey-icon.svg"))
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
        self.labelBandCuttingSpeed = QtWidgets.QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingSpeed.setGeometry(QtCore.QRect(31, 27, 270, 45))
        self.labelBandCuttingSpeed.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelBandCuttingSpeed.setObjectName("labelBandCuttingSpeed")
        self.labelBandCuttingInfo = QtWidgets.QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingInfo.setGeometry(QtCore.QRect(31, 106, 255, 51))
        self.labelBandCuttingInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 22px;\n"
"}")
        self.labelBandCuttingInfo.setObjectName("labelBandCuttingInfo")
        self.labelBandCuttingSpeedValue = QtWidgets.QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingSpeedValue.setGeometry(QtCore.QRect(330, 156, 200, 55))
        self.labelBandCuttingSpeedValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 55px;\n"
"}")
        self.labelBandCuttingSpeedValue.setObjectName("labelBandCuttingSpeedValue")
        self.BandCuttingCurrentFrame = QtWidgets.QFrame(self.bandCuttingSpeedFrame)
        self.BandCuttingCurrentFrame.setGeometry(QtCore.QRect(31, 200, 217, 109))
        self.BandCuttingCurrentFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandCuttingCurrentFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.BandCuttingCurrentFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.BandCuttingCurrentFrame.setObjectName("BandCuttingCurrentFrame")
        self.labelBandCuttingCurrent = QtWidgets.QLabel(self.BandCuttingCurrentFrame)
        self.labelBandCuttingCurrent.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelBandCuttingCurrent.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelBandCuttingCurrent.setObjectName("labelBandCuttingCurrent")
        self.labelBandCuttingCurrentValue = QtWidgets.QLabel(self.BandCuttingCurrentFrame)
        self.labelBandCuttingCurrentValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelBandCuttingCurrentValue.setFont(font)
        self.labelBandCuttingCurrentValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelBandCuttingCurrentValue.setObjectName("labelBandCuttingCurrentValue")
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
        self.labelBandDescentSpeed = QtWidgets.QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentSpeed.setGeometry(QtCore.QRect(31, 27, 270, 45))
        self.labelBandDescentSpeed.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelBandDescentSpeed.setObjectName("labelBandDescentSpeed")
        self.labelBandDescentInfo = QtWidgets.QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentInfo.setGeometry(QtCore.QRect(31, 106, 255, 51))
        self.labelBandDescentInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 22px;\n"
"}")
        self.labelBandDescentInfo.setObjectName("labelBandDescentInfo")
        self.labelBandDescentSpeedValue = QtWidgets.QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentSpeedValue.setGeometry(QtCore.QRect(330, 156, 200, 55))
        self.labelBandDescentSpeedValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 55px;\n"
"}")
        self.labelBandDescentSpeedValue.setObjectName("labelBandDescentSpeedValue")
        self.BandDescentCurrentFrame = QtWidgets.QFrame(self.bandDescentSpeedFrame)
        self.BandDescentCurrentFrame.setGeometry(QtCore.QRect(31, 200, 217, 109))
        self.BandDescentCurrentFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandDescentCurrentFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.BandDescentCurrentFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.BandDescentCurrentFrame.setObjectName("BandDescentCurrentFrame")
        self.labelBandDescentCurrent = QtWidgets.QLabel(self.BandDescentCurrentFrame)
        self.labelBandDescentCurrent.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelBandDescentCurrent.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelBandDescentCurrent.setObjectName("labelBandDescentCurrent")
        self.labelBandDescentCurrentValue = QtWidgets.QLabel(self.BandDescentCurrentFrame)
        self.labelBandDescentCurrentValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelBandDescentCurrentValue.setFont(font)
        self.labelBandDescentCurrentValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelBandDescentCurrentValue.setObjectName("labelBandDescentCurrentValue")
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
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: bold;\n"
"    font-size: 24px;\n"
"}")
        self.labelLogViewer.setObjectName("labelLogViewer")
        self.logViewerScroll = QtWidgets.QScrollArea(self.logViewerFrame)
        self.logViewerScroll.setGeometry(QtCore.QRect(15, 90, 280, 461))
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
        self.toolBtnCuttingStart = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStart.setEnabled(True)
        self.toolBtnCuttingStart.setGeometry(QtCore.QRect(27, 27, 220, 170))
        self.toolBtnCuttingStart.setStyleSheet("QToolButton {\n"
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
        icon5.addPixmap(QtGui.QPixmap("src/gui/images/cutting-start-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolBtnCuttingStart.setIcon(icon5)
        self.toolBtnCuttingStart.setIconSize(QtCore.QSize(105, 105))
        self.toolBtnCuttingStart.setCheckable(True)
        self.toolBtnCuttingStart.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBtnCuttingStart.setObjectName("toolBtnCuttingStart")
        self.toolBtnCuttingStop = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStop.setGeometry(QtCore.QRect(312, 27, 220, 170))
        self.toolBtnCuttingStop.setStyleSheet("QToolButton {\n"
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
        icon6.addPixmap(QtGui.QPixmap("src/gui/images/cutting-stop-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolBtnCuttingStop.setIcon(icon6)
        self.toolBtnCuttingStop.setIconSize(QtCore.QSize(105, 105))
        self.toolBtnCuttingStop.setCheckable(True)
        self.toolBtnCuttingStop.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBtnCuttingStop.setObjectName("toolBtnCuttingStop")
        self.toolBtnCoolant = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolBtnCoolant.setGeometry(QtCore.QRect(596, 27, 220, 170))
        self.toolBtnCoolant.setStyleSheet("QToolButton {\n"
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
        icon7.addPixmap(QtGui.QPixmap("src/gui/images/coolant-liquid-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolBtnCoolant.setIcon(icon7)
        self.toolBtnCoolant.setIconSize(QtCore.QSize(105, 105))
        self.toolBtnCoolant.setCheckable(True)
        self.toolBtnCoolant.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBtnCoolant.setObjectName("toolBtnCoolant")
        self.toolBtnSawdustCleaning = QtWidgets.QToolButton(self.cuttingControlFrame)
        self.toolBtnSawdustCleaning.setGeometry(QtCore.QRect(881, 24, 220, 170))
        self.toolBtnSawdustCleaning.setStyleSheet("QToolButton {\n"
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
        icon8.addPixmap(QtGui.QPixmap("src/gui/images/sawdust-cleaning-icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolBtnSawdustCleaning.setIcon(icon8)
        self.toolBtnSawdustCleaning.setIconSize(QtCore.QSize(105, 105))
        self.toolBtnSawdustCleaning.setCheckable(True)
        self.toolBtnSawdustCleaning.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolBtnSawdustCleaning.setObjectName("toolBtnSawdustCleaning")
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
        self.labelBandDeviation.setText(_translate("MainWindow", "Şerit Sapması"))
        self.labelMaxBandDeviation.setText(_translate("MainWindow", "Şerit Sapması"))
        self.labelMaxBandDeviationValue.setText(_translate("MainWindow", "16.35"))
        self.labelSystemStatus.setText(_translate("MainWindow", "Sistem Durumu"))
        self.labelBandCuttingSpeed.setText(_translate("MainWindow", "Şerit Kesme Hızı"))
        self.labelBandCuttingInfo.setText(_translate("MainWindow", "Başlangıç hızını\n"
"belirlemek için tıklayın."))
        self.labelBandCuttingCurrent.setText(_translate("MainWindow", "Şerit Motor Akım"))
        self.labelBandCuttingCurrentValue.setText(_translate("MainWindow", "16.35"))
        self.labelBandDescentSpeed.setText(_translate("MainWindow", "Şerit İnme Hızı"))
        self.labelBandDescentInfo.setText(_translate("MainWindow", "Başlangıç hızını\n"
"belirlemek için tıklayın."))
        self.labelBandDescentCurrent.setText(_translate("MainWindow", "Şerit Motor Akım"))
        self.labelBandDescentCurrentValue.setText(_translate("MainWindow", "16.35"))
        self.labelLogViewer.setText(_translate("MainWindow", "Çalışma Günlüğü"))
        self.toolBtnCuttingStart.setText(_translate("MainWindow", "Kesim Başlat"))
        self.toolBtnCuttingStop.setText(_translate("MainWindow", "Kesim Durdur"))
        self.toolBtnCoolant.setText(_translate("MainWindow", "Soğutma Sıvısı"))
        self.toolBtnSawdustCleaning.setText(_translate("MainWindow", "Talaş Temizlik"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())