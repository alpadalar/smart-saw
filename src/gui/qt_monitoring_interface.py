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
        icon.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/control-panel-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/control-panel-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon1.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/positioning-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/positioning-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon2.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/camera-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/camera-icon-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon3.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/sensor-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/sensor-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon4.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/tracking-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap("src/gui\\../../../../../icons/tracking-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        self.Container = QtWidgets.QFrame(self.centralwidget)
        self.Container.setGeometry(QtCore.QRect(425, 127, 582, 435))
        self.Container.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Container.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Container.setObjectName("Container")
        self.FrameMakineID = QtWidgets.QFrame(self.Container)
        self.FrameMakineID.setGeometry(QtCore.QRect(20, 27, 260, 105))
        self.FrameMakineID.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMakineID.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameMakineID.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameMakineID.setObjectName("FrameMakineID")
        self.labelMakineID = QtWidgets.QLabel(self.FrameMakineID)
        self.labelMakineID.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelMakineID.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelMakineID.setObjectName("labelMakineID")
        self.labelMakineIDValue = QtWidgets.QLabel(self.FrameMakineID)
        self.labelMakineIDValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelMakineIDValue.setFont(font)
        self.labelMakineIDValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelMakineIDValue.setObjectName("labelMakineIDValue")
        self.FrameSeritID = QtWidgets.QFrame(self.Container)
        self.FrameSeritID.setGeometry(QtCore.QRect(297, 27, 260, 105))
        self.FrameSeritID.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritID.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritID.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritID.setObjectName("FrameSeritID")
        self.labelSeritID = QtWidgets.QLabel(self.FrameSeritID)
        self.labelSeritID.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritID.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritID.setObjectName("labelSeritID")
        self.labelSeritIDValue = QtWidgets.QLabel(self.FrameSeritID)
        self.labelSeritIDValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritIDValue.setFont(font)
        self.labelSeritIDValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritIDValue.setObjectName("labelSeritIDValue")
        self.FrameSeritDisOlcusu = QtWidgets.QFrame(self.Container)
        self.FrameSeritDisOlcusu.setGeometry(QtCore.QRect(20, 166, 260, 105))
        self.FrameSeritDisOlcusu.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritDisOlcusu.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritDisOlcusu.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritDisOlcusu.setObjectName("FrameSeritDisOlcusu")
        self.labelSeritDisOlcusu = QtWidgets.QLabel(self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusu.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritDisOlcusu.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritDisOlcusu.setObjectName("labelSeritDisOlcusu")
        self.labelSeritDisOlcusuValue = QtWidgets.QLabel(self.FrameSeritDisOlcusu)
        self.labelSeritDisOlcusuValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritDisOlcusuValue.setFont(font)
        self.labelSeritDisOlcusuValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritDisOlcusuValue.setObjectName("labelSeritDisOlcusuValue")
        self.FrameSeritTipi = QtWidgets.QFrame(self.Container)
        self.FrameSeritTipi.setGeometry(QtCore.QRect(297, 166, 260, 105))
        self.FrameSeritTipi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritTipi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritTipi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritTipi.setObjectName("FrameSeritTipi")
        self.labelSeritTipi = QtWidgets.QLabel(self.FrameSeritTipi)
        self.labelSeritTipi.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritTipi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritTipi.setObjectName("labelSeritTipi")
        self.labelSeritTipiValue = QtWidgets.QLabel(self.FrameSeritTipi)
        self.labelSeritTipiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritTipiValue.setFont(font)
        self.labelSeritTipiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritTipiValue.setObjectName("labelSeritTipiValue")
        self.FrameSeritMarkasi = QtWidgets.QFrame(self.Container)
        self.FrameSeritMarkasi.setGeometry(QtCore.QRect(20, 306, 260, 105))
        self.FrameSeritMarkasi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMarkasi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritMarkasi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritMarkasi.setObjectName("FrameSeritMarkasi")
        self.labelSeritMarkasi = QtWidgets.QLabel(self.FrameSeritMarkasi)
        self.labelSeritMarkasi.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritMarkasi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritMarkasi.setObjectName("labelSeritMarkasi")
        self.labelSeritMarkasiValue = QtWidgets.QLabel(self.FrameSeritMarkasi)
        self.labelSeritMarkasiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritMarkasiValue.setFont(font)
        self.labelSeritMarkasiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritMarkasiValue.setObjectName("labelSeritMarkasiValue")
        self.FrameSeritMalzemesi = QtWidgets.QFrame(self.Container)
        self.FrameSeritMalzemesi.setGeometry(QtCore.QRect(297, 306, 260, 105))
        self.FrameSeritMalzemesi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMalzemesi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritMalzemesi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritMalzemesi.setObjectName("FrameSeritMalzemesi")
        self.labelBandSeritMalzemesi = QtWidgets.QLabel(self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesi.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelBandSeritMalzemesi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelBandSeritMalzemesi.setObjectName("labelBandSeritMalzemesi")
        self.labelBandSeritMalzemesiValue = QtWidgets.QLabel(self.FrameSeritMalzemesi)
        self.labelBandSeritMalzemesiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelBandSeritMalzemesiValue.setFont(font)
        self.labelBandSeritMalzemesiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelBandSeritMalzemesiValue.setObjectName("labelBandSeritMalzemesiValue")
        self.Container_3 = QtWidgets.QFrame(self.centralwidget)
        self.Container_3.setGeometry(QtCore.QRect(1033, 127, 857, 281))
        self.Container_3.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Container_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Container_3.setObjectName("Container_3")
        self.FrameMalzemeCinsi = QtWidgets.QFrame(self.Container_3)
        self.FrameMalzemeCinsi.setGeometry(QtCore.QRect(20, 27, 260, 105))
        self.FrameMalzemeCinsi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMalzemeCinsi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameMalzemeCinsi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameMalzemeCinsi.setObjectName("FrameMalzemeCinsi")
        self.labelMalzemeCinsi = QtWidgets.QLabel(self.FrameMalzemeCinsi)
        self.labelMalzemeCinsi.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelMalzemeCinsi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelMalzemeCinsi.setObjectName("labelMalzemeCinsi")
        self.labelMalzemeCinsiValue = QtWidgets.QLabel(self.FrameMalzemeCinsi)
        self.labelMalzemeCinsiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelMalzemeCinsiValue.setFont(font)
        self.labelMalzemeCinsiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelMalzemeCinsiValue.setObjectName("labelMalzemeCinsiValue")
        self.FrameMalzemeSertligi = QtWidgets.QFrame(self.Container_3)
        self.FrameMalzemeSertligi.setGeometry(QtCore.QRect(300, 27, 260, 105))
        self.FrameMalzemeSertligi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMalzemeSertligi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameMalzemeSertligi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameMalzemeSertligi.setObjectName("FrameMalzemeSertligi")
        self.labelMalzemeSertligi = QtWidgets.QLabel(self.FrameMalzemeSertligi)
        self.labelMalzemeSertligi.setGeometry(QtCore.QRect(33, 20, 161, 31))
        self.labelMalzemeSertligi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelMalzemeSertligi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelMalzemeSertligi.setObjectName("labelMalzemeSertligi")
        self.labelMalzemeSertligiValue = QtWidgets.QLabel(self.FrameMalzemeSertligi)
        self.labelMalzemeSertligiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelMalzemeSertligiValue.setFont(font)
        self.labelMalzemeSertligiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelMalzemeSertligiValue.setObjectName("labelMalzemeSertligiValue")
        self.FrameKesitYapisi = QtWidgets.QFrame(self.Container_3)
        self.FrameKesitYapisi.setGeometry(QtCore.QRect(580, 27, 260, 105))
        self.FrameKesitYapisi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKesitYapisi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameKesitYapisi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameKesitYapisi.setObjectName("FrameKesitYapisi")
        self.labelKesitYapisi = QtWidgets.QLabel(self.FrameKesitYapisi)
        self.labelKesitYapisi.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelKesitYapisi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelKesitYapisi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelKesitYapisi.setObjectName("labelKesitYapisi")
        self.labelKesitYapisiValue = QtWidgets.QLabel(self.FrameKesitYapisi)
        self.labelKesitYapisiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelKesitYapisiValue.setFont(font)
        self.labelKesitYapisiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelKesitYapisiValue.setObjectName("labelKesitYapisiValue")
        self.FrameABCD = QtWidgets.QFrame(self.Container_3)
        self.FrameABCD.setGeometry(QtCore.QRect(20, 154, 820, 105))
        self.FrameABCD.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameABCD.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameABCD.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameABCD.setObjectName("FrameABCD")
        self.labelA = QtWidgets.QLabel(self.FrameABCD)
        self.labelA.setGeometry(QtCore.QRect(24, 19, 81, 20))
        self.labelA.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelA.setObjectName("labelA")
        self.labelAValue = QtWidgets.QLabel(self.FrameABCD)
        self.labelAValue.setGeometry(QtCore.QRect(52, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelAValue.setFont(font)
        self.labelAValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelAValue.setObjectName("labelAValue")
        self.labelB = QtWidgets.QLabel(self.FrameABCD)
        self.labelB.setGeometry(QtCore.QRect(237, 19, 81, 20))
        self.labelB.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelB.setObjectName("labelB")
        self.labelC = QtWidgets.QLabel(self.FrameABCD)
        self.labelC.setGeometry(QtCore.QRect(450, 19, 81, 20))
        self.labelC.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelC.setObjectName("labelC")
        self.labelD = QtWidgets.QLabel(self.FrameABCD)
        self.labelD.setGeometry(QtCore.QRect(663, 19, 81, 20))
        self.labelD.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelD.setObjectName("labelD")
        self.labelBValue = QtWidgets.QLabel(self.FrameABCD)
        self.labelBValue.setGeometry(QtCore.QRect(261, 40, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelBValue.setFont(font)
        self.labelBValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelBValue.setObjectName("labelBValue")
        self.labelCValue = QtWidgets.QLabel(self.FrameABCD)
        self.labelCValue.setGeometry(QtCore.QRect(475, 40, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelCValue.setFont(font)
        self.labelCValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelCValue.setObjectName("labelCValue")
        self.labelDValue = QtWidgets.QLabel(self.FrameABCD)
        self.labelDValue.setGeometry(QtCore.QRect(690, 40, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelDValue.setFont(font)
        self.labelDValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelDValue.setObjectName("labelDValue")
        self.Container_4 = QtWidgets.QFrame(self.centralwidget)
        self.Container_4.setGeometry(QtCore.QRect(1033, 423, 857, 413))
        self.Container_4.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Container_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Container_4.setObjectName("Container_4")
        self.FrameSeritSapmasi = QtWidgets.QFrame(self.Container_4)
        self.FrameSeritSapmasi.setGeometry(QtCore.QRect(20, 27, 260, 105))
        self.FrameSeritSapmasi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritSapmasi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritSapmasi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritSapmasi.setObjectName("FrameSeritSapmasi")
        self.labelSeritSapmasi = QtWidgets.QLabel(self.FrameSeritSapmasi)
        self.labelSeritSapmasi.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelSeritSapmasi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritSapmasi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelSeritSapmasi.setObjectName("labelSeritSapmasi")
        self.labelSeritSapmasiValue = QtWidgets.QLabel(self.FrameSeritSapmasi)
        self.labelSeritSapmasiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritSapmasiValue.setFont(font)
        self.labelSeritSapmasiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritSapmasiValue.setObjectName("labelSeritSapmasiValue")
        self.FrameSeritGerginligi = QtWidgets.QFrame(self.Container_4)
        self.FrameSeritGerginligi.setGeometry(QtCore.QRect(300, 27, 260, 105))
        self.FrameSeritGerginligi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritGerginligi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritGerginligi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritGerginligi.setObjectName("FrameSeritGerginligi")
        self.labelSeritGerginligi = QtWidgets.QLabel(self.FrameSeritGerginligi)
        self.labelSeritGerginligi.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelSeritGerginligi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritGerginligi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelSeritGerginligi.setObjectName("labelSeritGerginligi")
        self.labelSeritGerginligiValue = QtWidgets.QLabel(self.FrameSeritGerginligi)
        self.labelSeritGerginligiValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritGerginligiValue.setFont(font)
        self.labelSeritGerginligiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritGerginligiValue.setObjectName("labelSeritGerginligiValue")
        self.FrameKafaYuksekligi = QtWidgets.QFrame(self.Container_4)
        self.FrameKafaYuksekligi.setGeometry(QtCore.QRect(580, 27, 260, 105))
        self.FrameKafaYuksekligi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKafaYuksekligi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameKafaYuksekligi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameKafaYuksekligi.setObjectName("FrameKafaYuksekligi")
        self.labelKafaYuksekligi = QtWidgets.QLabel(self.FrameKafaYuksekligi)
        self.labelKafaYuksekligi.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelKafaYuksekligi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelKafaYuksekligi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelKafaYuksekligi.setObjectName("labelKafaYuksekligi")
        self.labelKafaYuksekligiValue = QtWidgets.QLabel(self.FrameKafaYuksekligi)
        self.labelKafaYuksekligiValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelKafaYuksekligiValue.setFont(font)
        self.labelKafaYuksekligiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelKafaYuksekligiValue.setObjectName("labelKafaYuksekligiValue")
        self.FrameTitresimX = QtWidgets.QFrame(self.Container_4)
        self.FrameTitresimX.setGeometry(QtCore.QRect(20, 154, 260, 105))
        self.FrameTitresimX.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimX.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameTitresimX.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameTitresimX.setObjectName("FrameTitresimX")
        self.labelTitresimX = QtWidgets.QLabel(self.FrameTitresimX)
        self.labelTitresimX.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelTitresimX.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimX.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelTitresimX.setObjectName("labelTitresimX")
        self.labelTitresimXValue = QtWidgets.QLabel(self.FrameTitresimX)
        self.labelTitresimXValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelTitresimXValue.setFont(font)
        self.labelTitresimXValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelTitresimXValue.setObjectName("labelTitresimXValue")
        self.FrameTitresimY = QtWidgets.QFrame(self.Container_4)
        self.FrameTitresimY.setGeometry(QtCore.QRect(300, 154, 260, 105))
        self.FrameTitresimY.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimY.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameTitresimY.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameTitresimY.setObjectName("FrameTitresimY")
        self.labelTitresimY = QtWidgets.QLabel(self.FrameTitresimY)
        self.labelTitresimY.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelTitresimY.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimY.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelTitresimY.setObjectName("labelTitresimY")
        self.labelTitresimYValue = QtWidgets.QLabel(self.FrameTitresimY)
        self.labelTitresimYValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelTitresimYValue.setFont(font)
        self.labelTitresimYValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelTitresimYValue.setObjectName("labelTitresimYValue")
        self.FrameTitresimZ = QtWidgets.QFrame(self.Container_4)
        self.FrameTitresimZ.setGeometry(QtCore.QRect(580, 154, 260, 105))
        self.FrameTitresimZ.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTitresimZ.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameTitresimZ.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameTitresimZ.setObjectName("FrameTitresimZ")
        self.labelTitresimZ = QtWidgets.QLabel(self.FrameTitresimZ)
        self.labelTitresimZ.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelTitresimZ.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimZ.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelTitresimZ.setObjectName("labelTitresimZ")
        self.labelTitresimZValue = QtWidgets.QLabel(self.FrameTitresimZ)
        self.labelTitresimZValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelTitresimZValue.setFont(font)
        self.labelTitresimZValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelTitresimZValue.setObjectName("labelTitresimZValue")
        self.FrameMengeneBasinc = QtWidgets.QFrame(self.Container_4)
        self.FrameMengeneBasinc.setGeometry(QtCore.QRect(20, 280, 260, 105))
        self.FrameMengeneBasinc.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameMengeneBasinc.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameMengeneBasinc.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameMengeneBasinc.setObjectName("FrameMengeneBasinc")
        self.labelMengeneBasinc = QtWidgets.QLabel(self.FrameMengeneBasinc)
        self.labelMengeneBasinc.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelMengeneBasinc.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelMengeneBasinc.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelMengeneBasinc.setObjectName("labelMengeneBasinc")
        self.labelMengeneBasincValue = QtWidgets.QLabel(self.FrameMengeneBasinc)
        self.labelMengeneBasincValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelMengeneBasincValue.setFont(font)
        self.labelMengeneBasincValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelMengeneBasincValue.setObjectName("labelMengeneBasincValue")
        self.FrameOrtamSicakligi = QtWidgets.QFrame(self.Container_4)
        self.FrameOrtamSicakligi.setGeometry(QtCore.QRect(300, 280, 260, 105))
        self.FrameOrtamSicakligi.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameOrtamSicakligi.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameOrtamSicakligi.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameOrtamSicakligi.setObjectName("FrameOrtamSicakligi")
        self.labelOrtamSicakligi = QtWidgets.QLabel(self.FrameOrtamSicakligi)
        self.labelOrtamSicakligi.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelOrtamSicakligi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelOrtamSicakligi.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelOrtamSicakligi.setObjectName("labelOrtamSicakligi")
        self.labelOrtamSicakligiValue = QtWidgets.QLabel(self.FrameOrtamSicakligi)
        self.labelOrtamSicakligiValue.setGeometry(QtCore.QRect(91, 43, 251, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelOrtamSicakligiValue.setFont(font)
        self.labelOrtamSicakligiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelOrtamSicakligiValue.setObjectName("labelOrtamSicakligiValue")
        self.FrameOrtamNem = QtWidgets.QFrame(self.Container_4)
        self.FrameOrtamNem.setGeometry(QtCore.QRect(580, 280, 260, 105))
        self.FrameOrtamNem.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameOrtamNem.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameOrtamNem.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameOrtamNem.setObjectName("FrameOrtamNem")
        self.labelOrtamNem = QtWidgets.QLabel(self.FrameOrtamNem)
        self.labelOrtamNem.setGeometry(QtCore.QRect(33, 20, 151, 31))
        self.labelOrtamNem.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelOrtamNem.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelOrtamNem.setObjectName("labelOrtamNem")
        self.labelOrtamNemValue = QtWidgets.QLabel(self.FrameOrtamNem)
        self.labelOrtamNemValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelOrtamNemValue.setFont(font)
        self.labelOrtamNemValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelOrtamNemValue.setObjectName("labelOrtamNemValue")
        self.Container_5 = QtWidgets.QFrame(self.centralwidget)
        self.Container_5.setGeometry(QtCore.QRect(1033, 851, 857, 159))
        self.Container_5.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Container_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Container_5.setObjectName("Container_5")
        self.FrameKesilenParcaAdeti = QtWidgets.QFrame(self.Container_5)
        self.FrameKesilenParcaAdeti.setGeometry(QtCore.QRect(20, 27, 260, 105))
        self.FrameKesilenParcaAdeti.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameKesilenParcaAdeti.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameKesilenParcaAdeti.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameKesilenParcaAdeti.setObjectName("FrameKesilenParcaAdeti")
        self.labelKesilenParcaAdeti = QtWidgets.QLabel(self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdeti.setGeometry(QtCore.QRect(33, 20, 201, 31))
        self.labelKesilenParcaAdeti.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelKesilenParcaAdeti.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelKesilenParcaAdeti.setObjectName("labelKesilenParcaAdeti")
        self.labelKesilenParcaAdetiValue = QtWidgets.QLabel(self.FrameKesilenParcaAdeti)
        self.labelKesilenParcaAdetiValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelKesilenParcaAdetiValue.setFont(font)
        self.labelKesilenParcaAdetiValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelKesilenParcaAdetiValue.setObjectName("labelKesilenParcaAdetiValue")
        self.FrameTestereDurum = QtWidgets.QFrame(self.Container_5)
        self.FrameTestereDurum.setGeometry(QtCore.QRect(300, 27, 260, 105))
        self.FrameTestereDurum.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameTestereDurum.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameTestereDurum.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameTestereDurum.setObjectName("FrameTestereDurum")
        self.labelTestereDurum = QtWidgets.QLabel(self.FrameTestereDurum)
        self.labelTestereDurum.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelTestereDurum.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTestereDurum.setObjectName("labelTestereDurum")
        self.labelTestereDurumValue = QtWidgets.QLabel(self.FrameTestereDurum)
        self.labelTestereDurumValue.setGeometry(QtCore.QRect(0, 43, 260, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelTestereDurumValue.setFont(font)
        self.labelTestereDurumValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelTestereDurumValue.setObjectName("labelTestereDurumValue")
        self.labelTestereDurumValue.setAlignment(QtCore.Qt.AlignCenter)
        self.FrameAlarm = QtWidgets.QFrame(self.Container_5)
        self.FrameAlarm.setGeometry(QtCore.QRect(580, 27, 260, 105))
        self.FrameAlarm.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameAlarm.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameAlarm.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameAlarm.setObjectName("FrameAlarm")
        self.labelAlarm = QtWidgets.QLabel(self.FrameAlarm)
        self.labelAlarm.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelAlarm.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelAlarm.setObjectName("labelAlarm")
        self.labelAlarmValue = QtWidgets.QLabel(self.FrameAlarm)
        self.labelAlarmValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelAlarmValue.setFont(font)
        self.labelAlarmValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelAlarmValue.setObjectName("labelAlarmValue")
        self.Container_2 = QtWidgets.QFrame(self.centralwidget)
        self.Container_2.setGeometry(QtCore.QRect(425, 577, 582, 435))
        self.Container_2.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.Container_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Container_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Container_2.setObjectName("Container_2")
        self.FrameSeritMotorHiz = QtWidgets.QFrame(self.Container_2)
        self.FrameSeritMotorHiz.setGeometry(QtCore.QRect(20, 27, 260, 105))
        self.FrameSeritMotorHiz.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorHiz.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritMotorHiz.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritMotorHiz.setObjectName("FrameSeritMotorHiz")
        self.labelSeritMotorHiz = QtWidgets.QLabel(self.FrameSeritMotorHiz)
        self.labelSeritMotorHiz.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritMotorHiz.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritMotorHiz.setObjectName("labelSeritMotorHiz")
        self.labelSeritMotorHizValue = QtWidgets.QLabel(self.FrameSeritMotorHiz)
        self.labelSeritMotorHizValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritMotorHizValue.setFont(font)
        self.labelSeritMotorHizValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritMotorHizValue.setObjectName("labelSeritMotorHizValue")
        self.FrameInmeMotorHiz = QtWidgets.QFrame(self.Container_2)
        self.FrameInmeMotorHiz.setGeometry(QtCore.QRect(297, 27, 260, 105))
        self.FrameInmeMotorHiz.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorHiz.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameInmeMotorHiz.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameInmeMotorHiz.setObjectName("FrameInmeMotorHiz")
        self.labelInmeMotorHiz = QtWidgets.QLabel(self.FrameInmeMotorHiz)
        self.labelInmeMotorHiz.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelInmeMotorHiz.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelInmeMotorHiz.setObjectName("labelInmeMotorHiz")
        self.labelInmeMotorHizValue = QtWidgets.QLabel(self.FrameInmeMotorHiz)
        self.labelInmeMotorHizValue.setGeometry(QtCore.QRect(91, 43, 201, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelInmeMotorHizValue.setFont(font)
        self.labelInmeMotorHizValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelInmeMotorHizValue.setObjectName("labelInmeMotorHizValue")
        self.FrameSeritMotorAkim = QtWidgets.QFrame(self.Container_2)
        self.FrameSeritMotorAkim.setGeometry(QtCore.QRect(20, 166, 260, 105))
        self.FrameSeritMotorAkim.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorAkim.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritMotorAkim.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritMotorAkim.setObjectName("FrameSeritMotorAkim")
        self.labelSeritMotorAkim = QtWidgets.QLabel(self.FrameSeritMotorAkim)
        self.labelSeritMotorAkim.setGeometry(QtCore.QRect(33, 20, 171, 20))
        self.labelSeritMotorAkim.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritMotorAkim.setObjectName("labelSeritMotorAkim")
        self.labelSeritMotorAkimValue = QtWidgets.QLabel(self.FrameSeritMotorAkim)
        self.labelSeritMotorAkimValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritMotorAkimValue.setFont(font)
        self.labelSeritMotorAkimValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritMotorAkimValue.setObjectName("labelSeritMotorAkimValue")
        self.FrameInmeMotorAkim = QtWidgets.QFrame(self.Container_2)
        self.FrameInmeMotorAkim.setGeometry(QtCore.QRect(297, 166, 260, 105))
        self.FrameInmeMotorAkim.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorAkim.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameInmeMotorAkim.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameInmeMotorAkim.setObjectName("FrameInmeMotorAkim")
        self.labelInmeMotorAkim = QtWidgets.QLabel(self.FrameInmeMotorAkim)
        self.labelInmeMotorAkim.setGeometry(QtCore.QRect(33, 20, 181, 20))
        self.labelInmeMotorAkim.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelInmeMotorAkim.setObjectName("labelInmeMotorAkim")
        self.labelInmeMotorAkimValue = QtWidgets.QLabel(self.FrameInmeMotorAkim)
        self.labelInmeMotorAkimValue.setGeometry(QtCore.QRect(91, 43, 101, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelInmeMotorAkimValue.setFont(font)
        self.labelInmeMotorAkimValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelInmeMotorAkimValue.setObjectName("labelInmeMotorAkimValue")
        self.FrameSeritMotorTork = QtWidgets.QFrame(self.Container_2)
        self.FrameSeritMotorTork.setGeometry(QtCore.QRect(20, 306, 260, 105))
        self.FrameSeritMotorTork.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameSeritMotorTork.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameSeritMotorTork.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameSeritMotorTork.setObjectName("FrameSeritMotorTork")
        self.labelSeritMotorTork = QtWidgets.QLabel(self.FrameSeritMotorTork)
        self.labelSeritMotorTork.setGeometry(QtCore.QRect(33, 20, 151, 20))
        self.labelSeritMotorTork.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritMotorTork.setObjectName("labelSeritMotorTork")
        self.labelSeritMotorTorkValue = QtWidgets.QLabel(self.FrameSeritMotorTork)
        self.labelSeritMotorTorkValue.setGeometry(QtCore.QRect(91, 43, 200, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelSeritMotorTorkValue.setFont(font)
        self.labelSeritMotorTorkValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelSeritMotorTorkValue.setObjectName("labelSeritMotorTorkValue")
        self.FrameInmeMotorTork = QtWidgets.QFrame(self.Container_2)
        self.FrameInmeMotorTork.setGeometry(QtCore.QRect(297, 306, 260, 105))
        self.FrameInmeMotorTork.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.FrameInmeMotorTork.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.FrameInmeMotorTork.setFrameShadow(QtWidgets.QFrame.Raised)
        self.FrameInmeMotorTork.setObjectName("FrameInmeMotorTork")
        self.labelInmeMotorTork = QtWidgets.QLabel(self.FrameInmeMotorTork)
        self.labelInmeMotorTork.setGeometry(QtCore.QRect(33, 20, 171, 20))
        self.labelInmeMotorTork.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelInmeMotorTork.setObjectName("labelInmeMotorTork")
        self.labelInmeMotorTorkValue = QtWidgets.QLabel(self.FrameInmeMotorTork)
        self.labelInmeMotorTorkValue.setGeometry(QtCore.QRect(91, 43, 200, 50))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelInmeMotorTorkValue.setFont(font)
        self.labelInmeMotorTorkValue.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 36px;\n"
"}")
        self.labelInmeMotorTorkValue.setObjectName("labelInmeMotorTorkValue")
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
        self.labelMakineID.setText(_translate("MainWindow", "Makine ID"))
        self.labelMakineIDValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritID.setText(_translate("MainWindow", "Şerit ID"))
        self.labelSeritIDValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritDisOlcusu.setText(_translate("MainWindow", "Şerit Diş Ölçüsü"))
        self.labelSeritDisOlcusuValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritTipi.setText(_translate("MainWindow", "Şerit Tipi"))
        self.labelSeritTipiValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritMarkasi.setText(_translate("MainWindow", "Şerit Markası"))
        self.labelSeritMarkasiValue.setText(_translate("MainWindow", "16.35"))
        self.labelBandSeritMalzemesi.setText(_translate("MainWindow", "Şerit Malzemesi"))
        self.labelBandSeritMalzemesiValue.setText(_translate("MainWindow", "16.35"))
        self.labelMalzemeCinsi.setText(_translate("MainWindow", "Malzeme Cinsi"))
        self.labelMalzemeCinsiValue.setText(_translate("MainWindow", "16.35"))
        self.labelMalzemeSertligi.setText(_translate("MainWindow", "Malzeme Sertliği"))
        self.labelMalzemeSertligiValue.setText(_translate("MainWindow", "16.35"))
        self.labelKesitYapisi.setText(_translate("MainWindow", "Kesit Yapısı"))
        self.labelKesitYapisiValue.setText(_translate("MainWindow", "16.35"))
        self.labelA.setText(_translate("MainWindow", "A (mm)"))
        self.labelAValue.setText(_translate("MainWindow", "16.35"))
        self.labelB.setText(_translate("MainWindow", "B (mm)"))
        self.labelC.setText(_translate("MainWindow", "C (mm)"))
        self.labelD.setText(_translate("MainWindow", "D (mm)"))
        self.labelBValue.setText(_translate("MainWindow", "16.35"))
        self.labelCValue.setText(_translate("MainWindow", "16.35"))
        self.labelDValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritSapmasi.setText(_translate("MainWindow", "Şerit Sapması"))
        self.labelSeritSapmasiValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritGerginligi.setText(_translate("MainWindow", "Şerit Gerginliği"))
        self.labelSeritGerginligiValue.setText(_translate("MainWindow", "16.35"))
        self.labelKafaYuksekligi.setText(_translate("MainWindow", "Kafa Yüksekliği"))
        self.labelKafaYuksekligiValue.setText(_translate("MainWindow", "16.35"))
        self.labelTitresimX.setText(_translate("MainWindow", "Titreşim (X)"))
        self.labelTitresimXValue.setText(_translate("MainWindow", "16.35"))
        self.labelTitresimY.setText(_translate("MainWindow", "Titreşim (Y)"))
        self.labelTitresimYValue.setText(_translate("MainWindow", "16.35"))
        self.labelTitresimZ.setText(_translate("MainWindow", "Titreşim (Z)"))
        self.labelTitresimZValue.setText(_translate("MainWindow", "16.35"))
        self.labelMengeneBasinc.setText(_translate("MainWindow", "Mengene Basınç"))
        self.labelMengeneBasincValue.setText(_translate("MainWindow", "16.35"))
        self.labelOrtamSicakligi.setText(_translate("MainWindow", "Ortam Sıcaklığı"))
        self.labelOrtamSicakligiValue.setText(_translate("MainWindow", "16.35"))
        self.labelOrtamNem.setText(_translate("MainWindow", "Ortam Nem"))
        self.labelOrtamNemValue.setText(_translate("MainWindow", "16.35"))
        self.labelKesilenParcaAdeti.setText(_translate("MainWindow", "Kesilen Parça Adeti"))
        self.labelKesilenParcaAdetiValue.setText(_translate("MainWindow", "16.35"))
        self.labelTestereDurum.setText(_translate("MainWindow", "Testere Durum"))
        self.labelTestereDurumValue.setText(_translate("MainWindow", "16.35"))
        self.labelAlarm.setText(_translate("MainWindow", "Alarm"))
        self.labelAlarmValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritMotorHiz.setText(_translate("MainWindow", "Şerit Motor Hız"))
        self.labelSeritMotorHizValue.setText(_translate("MainWindow", "16.35"))
        self.labelInmeMotorHiz.setText(_translate("MainWindow", "İnme Motor Hız"))
        self.labelInmeMotorHizValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritMotorAkim.setText(_translate("MainWindow", "Şerit Motor Akım"))
        self.labelSeritMotorAkimValue.setText(_translate("MainWindow", "16.35"))
        self.labelInmeMotorAkim.setText(_translate("MainWindow", "İnme Motor Akım"))
        self.labelInmeMotorAkimValue.setText(_translate("MainWindow", "16.35"))
        self.labelSeritMotorTork.setText(_translate("MainWindow", "Şerit Motor Tork"))
        self.labelSeritMotorTorkValue.setText(_translate("MainWindow", "16.35"))
        self.labelInmeMotorTork.setText(_translate("MainWindow", "İnme Motor Tork"))
        self.labelInmeMotorTorkValue.setText(_translate("MainWindow", "16.35"))
