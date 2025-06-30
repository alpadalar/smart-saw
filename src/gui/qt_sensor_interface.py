from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setStyleSheet("")
        MainWindow.showFullScreen()
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("""
QWidget#centralwidget {
    background-image: url('src/gui/images/background.png');
    background-repeat: no-repeat;
    background-position: center;
    background-attachment: fixed;
}
""")
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setContentsMargins(0, 0, 0, 0)
        self.centralwidget.setFixedSize(MainWindow.size())
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
        icon.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/control-panel-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/control-panel-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon1.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/positioning-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/positioning-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon2.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/camera-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/camera-icon-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon3.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/sensor-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/sensor-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        icon4.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/tracking-icon2.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap("src\\gui\\../../../../../icons/tracking-icon2-active.svg"), QtGui.QIcon.Active, QtGui.QIcon.On)
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
        self.XEkseniFrame = QtWidgets.QFrame(self.centralwidget)
        self.XEkseniFrame.setGeometry(QtCore.QRect(425, 724, 578, 342))
        self.XEkseniFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.XEkseniFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.XEkseniFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.XEkseniFrame.setObjectName("XEkseniFrame")
        self.labelXEkseni = QtWidgets.QLabel(self.XEkseniFrame)
        self.labelXEkseni.setGeometry(QtCore.QRect(34, 19, 295, 39))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelXEkseni.setFont(font)
        self.labelXEkseni.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 28px;\n"
"}")
        self.labelXEkseni.setObjectName("labelXEkseni")
        self.btnKesmeHizi = QtWidgets.QPushButton(self.XEkseniFrame)
        self.btnKesmeHizi.setGeometry(QtCore.QRect(41, 82, 223, 90))
        self.btnKesmeHizi.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    padding: 5px 10px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
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
        self.btnKesmeHizi.setObjectName("btnKesmeHizi")
        self.btnIlerlemeHizi = QtWidgets.QPushButton(self.XEkseniFrame)
        self.btnIlerlemeHizi.setGeometry(QtCore.QRect(315, 82, 223, 90))
        self.btnIlerlemeHizi.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    padding: 5px 10px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnIlerlemeHizi.setCheckable(True)
        self.btnIlerlemeHizi.setObjectName("btnIlerlemeHizi")
        self.btnSeritAkim = QtWidgets.QPushButton(self.XEkseniFrame)
        self.btnSeritAkim.setGeometry(QtCore.QRect(41, 218, 223, 90))
        self.btnSeritAkim.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    padding: 5px 10px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnSeritAkim.setCheckable(True)
        self.btnSeritAkim.setObjectName("btnSeritAkim")
        self.btnSeritSapmasi = QtWidgets.QPushButton(self.XEkseniFrame)
        self.btnSeritSapmasi.setGeometry(QtCore.QRect(315, 218, 223, 90))
        self.btnSeritSapmasi.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 25px;\n"
"    padding: 5px 10px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.1);\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #950952;\n"
"}")
        self.btnSeritSapmasi.setCheckable(True)
        self.btnSeritSapmasi.setObjectName("btnSeritSapmasi")
        self.kesimGrafigiFrame = QtWidgets.QFrame(self.centralwidget)
        self.kesimGrafigiFrame.setGeometry(QtCore.QRect(425, 127, 934, 568))
        self.kesimGrafigiFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.kesimGrafigiFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.kesimGrafigiFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.kesimGrafigiFrame.setObjectName("kesimGrafigiFrame")
        self.labelKesimGrafigi = QtWidgets.QLabel(self.kesimGrafigiFrame)
        self.labelKesimGrafigi.setGeometry(QtCore.QRect(34, 19, 461, 45))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelKesimGrafigi.setFont(font)
        self.labelKesimGrafigi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelKesimGrafigi.setObjectName("labelKesimGrafigi")
        self.labelKesimGrafigiInfo = QtWidgets.QLabel(self.kesimGrafigiFrame)
        self.labelKesimGrafigiInfo.setGeometry(QtCore.QRect(306, 33, 602, 31))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(False)
        font.setWeight(12)
        self.labelKesimGrafigiInfo.setFont(font)
        self.labelKesimGrafigiInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: 100;\n"
"    font-size: 22px;\n"
"}")
        self.labelKesimGrafigiInfo.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.labelKesimGrafigiInfo.setObjectName("labelKesimGrafigiInfo")
        self.AnomaliDurumuFrame = QtWidgets.QFrame(self.centralwidget)
        self.AnomaliDurumuFrame.setGeometry(QtCore.QRect(1385, 127, 505, 941))
        self.AnomaliDurumuFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.AnomaliDurumuFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.AnomaliDurumuFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.AnomaliDurumuFrame.setObjectName("AnomaliDurumuFrame")
        self.labelAnomaliDurumu = QtWidgets.QLabel(self.AnomaliDurumuFrame)
        self.labelAnomaliDurumu.setGeometry(QtCore.QRect(34, 19, 295, 39))
        self.labelAnomaliDurumu.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 32px;\n"
"}")
        self.labelAnomaliDurumu.setObjectName("labelAnomaliDurumu")
        
        # toolButton eklemesi
        self.toolButton = QtWidgets.QToolButton(self.AnomaliDurumuFrame)
        self.toolButton.setGeometry(QtCore.QRect(420, 10, 60, 60))
        self.toolButton.setStyleSheet("    background: qlineargradient(\n"
"    spread:pad, \n"
"    x1:0, y1:0, \n"
"    x2:0.5, y2:0.5, \n"
"    stop:0 rgba(0, 0, 0, 255), \n"
"    stop:1 rgba(124, 4, 66, 255));\n"
"    border-radius: 20px;")
        self.toolButton.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("src\\gui\\images/icons8-cross-30.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon5)
        self.toolButton.setIconSize(QtCore.QSize(30, 30))
        self.toolButton.setObjectName("toolButton")
        self.MotorVerileriFrame = QtWidgets.QFrame(self.AnomaliDurumuFrame)
        self.MotorVerileriFrame.setGeometry(QtCore.QRect(23, 77, 459, 297))
        self.MotorVerileriFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.MotorVerileriFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.MotorVerileriFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.MotorVerileriFrame.setObjectName("MotorVerileriFrame")
        self.labelMotorVerileri = QtWidgets.QLabel(self.MotorVerileriFrame)
        self.labelMotorVerileri.setGeometry(QtCore.QRect(8, 8, 443, 45))
        self.labelMotorVerileri.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 26px;\n"
"}")
        self.labelMotorVerileri.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMotorVerileri.setObjectName("labelMotorVerileri")
        self.KesmeHiziFrame = QtWidgets.QFrame(self.MotorVerileriFrame)
        self.KesmeHiziFrame.setGeometry(QtCore.QRect(8, 73, 443, 60))
        self.KesmeHiziFrame.setStyleSheet("QFrame {\n"
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
        self.KesmeHiziFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.KesmeHiziFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.KesmeHiziFrame.setObjectName("KesmeHiziFrame")
        self.labelKesmeHizi = QtWidgets.QLabel(self.KesmeHiziFrame)
        self.labelKesmeHizi.setGeometry(QtCore.QRect(28, 8, 393, 20))
        self.labelKesmeHizi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelKesmeHizi.setObjectName("labelKesmeHizi")
        self.labelKesmeHiziInfo = QtWidgets.QLabel(self.KesmeHiziFrame)
        self.labelKesmeHiziInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelKesmeHiziInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelKesmeHiziInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelKesmeHiziInfo.setObjectName("labelKesmeHiziInfo")
        self.IlerlemeHiziFrame = QtWidgets.QFrame(self.MotorVerileriFrame)
        self.IlerlemeHiziFrame.setGeometry(QtCore.QRect(8, 153, 443, 60))
        self.IlerlemeHiziFrame.setStyleSheet("QFrame {\n"
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
        self.IlerlemeHiziFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.IlerlemeHiziFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.IlerlemeHiziFrame.setObjectName("IlerlemeHiziFrame")
        self.labelIlerlemeHiziInfo = QtWidgets.QLabel(self.IlerlemeHiziFrame)
        self.labelIlerlemeHiziInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelIlerlemeHiziInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelIlerlemeHiziInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelIlerlemeHiziInfo.setObjectName("labelIlerlemeHiziInfo")
        self.labelIlerlemeHizi = QtWidgets.QLabel(self.IlerlemeHiziFrame)
        self.labelIlerlemeHizi.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelIlerlemeHizi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelIlerlemeHizi.setObjectName("labelIlerlemeHizi")
        self.SeritAkimFrame = QtWidgets.QFrame(self.MotorVerileriFrame)
        self.SeritAkimFrame.setGeometry(QtCore.QRect(8, 233, 443, 60))
        self.SeritAkimFrame.setStyleSheet("QFrame {\n"
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
        self.SeritAkimFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.SeritAkimFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.SeritAkimFrame.setObjectName("SeritAkimFrame")
        self.labelSeritAkimInfo = QtWidgets.QLabel(self.SeritAkimFrame)
        self.labelSeritAkimInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelSeritAkimInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritAkimInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelSeritAkimInfo.setObjectName("labelSeritAkimInfo")
        self.labelSeritAkim = QtWidgets.QLabel(self.SeritAkimFrame)
        self.labelSeritAkim.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelSeritAkim.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritAkim.setObjectName("labelSeritAkim")
        self.SensorVerileriFrame = QtWidgets.QFrame(self.AnomaliDurumuFrame)
        self.SensorVerileriFrame.setGeometry(QtCore.QRect(23, 387, 459, 529))
        self.SensorVerileriFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.SensorVerileriFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.SensorVerileriFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.SensorVerileriFrame.setObjectName("SensorVerileriFrame")
        self.labelSensorVerileri = QtWidgets.QLabel(self.SensorVerileriFrame)
        self.labelSensorVerileri.setGeometry(QtCore.QRect(8, 8, 443, 45))
        self.labelSensorVerileri.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 26px;\n"
"}")
        self.labelSensorVerileri.setAlignment(QtCore.Qt.AlignCenter)
        self.labelSensorVerileri.setObjectName("labelSensorVerileri")
        self.SicaklikFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.SicaklikFrame.setGeometry(QtCore.QRect(8, 58, 443, 60))
        self.SicaklikFrame.setStyleSheet("QFrame {\n"
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
        self.SicaklikFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.SicaklikFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.SicaklikFrame.setObjectName("SicaklikFrame")
        self.labelSicaklikInfo = QtWidgets.QLabel(self.SicaklikFrame)
        self.labelSicaklikInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelSicaklikInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSicaklikInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelSicaklikInfo.setObjectName("labelSicaklikInfo")
        self.labelSicaklik = QtWidgets.QLabel(self.SicaklikFrame)
        self.labelSicaklik.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelSicaklik.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelSicaklik.setObjectName("labelSicaklik")
        self.NemFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.NemFrame.setGeometry(QtCore.QRect(8, 138, 443, 60))
        self.NemFrame.setStyleSheet("QFrame {\n"
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
        self.NemFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.NemFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.NemFrame.setObjectName("NemFrame")
        self.labelNemInfo = QtWidgets.QLabel(self.NemFrame)
        self.labelNemInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelNemInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelNemInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelNemInfo.setObjectName("labelNemInfo")
        self.labelNem = QtWidgets.QLabel(self.NemFrame)
        self.labelNem.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelNem.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelNem.setObjectName("labelNem")
        self.SeritSapmasiFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.SeritSapmasiFrame.setGeometry(QtCore.QRect(8, 218, 443, 60))
        self.SeritSapmasiFrame.setStyleSheet("QFrame {\n"
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
        self.SeritSapmasiFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.SeritSapmasiFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.SeritSapmasiFrame.setObjectName("SeritSapmasiFrame")
        self.labelSeritSapmasiInfo = QtWidgets.QLabel(self.SeritSapmasiFrame)
        self.labelSeritSapmasiInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelSeritSapmasiInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritSapmasiInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelSeritSapmasiInfo.setObjectName("labelSeritSapmasiInfo")
        self.labelSeritSapmasi = QtWidgets.QLabel(self.SeritSapmasiFrame)
        self.labelSeritSapmasi.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelSeritSapmasi.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelSeritSapmasi.setObjectName("labelSeritSapmasi")
        self.TitresimXFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.TitresimXFrame.setGeometry(QtCore.QRect(8, 298, 443, 60))
        self.TitresimXFrame.setStyleSheet("QFrame {\n"
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
        self.TitresimXFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.TitresimXFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.TitresimXFrame.setObjectName("TitresimXFrame")
        self.labelTitresimXInfo = QtWidgets.QLabel(self.TitresimXFrame)
        self.labelTitresimXInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelTitresimXInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimXInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelTitresimXInfo.setObjectName("labelTitresimXInfo")
        self.labelTitresimX = QtWidgets.QLabel(self.TitresimXFrame)
        self.labelTitresimX.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelTitresimX.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimX.setObjectName("labelTitresimX")
        self.TitresimYFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.TitresimYFrame.setGeometry(QtCore.QRect(8, 378, 443, 60))
        self.TitresimYFrame.setStyleSheet("QFrame {\n"
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
        self.TitresimYFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.TitresimYFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.TitresimYFrame.setObjectName("TitresimYFrame")
        self.labelTitresimYInfo = QtWidgets.QLabel(self.TitresimYFrame)
        self.labelTitresimYInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelTitresimYInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimYInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelTitresimYInfo.setObjectName("labelTitresimYInfo")
        self.labelTitresimY = QtWidgets.QLabel(self.TitresimYFrame)
        self.labelTitresimY.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelTitresimY.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimY.setObjectName("labelTitresimY")
        self.TitresimZFrame = QtWidgets.QFrame(self.SensorVerileriFrame)
        self.TitresimZFrame.setGeometry(QtCore.QRect(8, 458, 443, 60))
        self.TitresimZFrame.setStyleSheet("QFrame {\n"
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
        self.TitresimZFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.TitresimZFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.TitresimZFrame.setObjectName("TitresimZFrame")
        self.labelTitresimZInfo = QtWidgets.QLabel(self.TitresimZFrame)
        self.labelTitresimZInfo.setGeometry(QtCore.QRect(25, 33, 393, 20))
        self.labelTitresimZInfo.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: medium;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimZInfo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.labelTitresimZInfo.setObjectName("labelTitresimZInfo")
        self.labelTitresimZ = QtWidgets.QLabel(self.TitresimZFrame)
        self.labelTitresimZ.setGeometry(QtCore.QRect(25, 8, 393, 20))
        self.labelTitresimZ.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color:    #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"}")
        self.labelTitresimZ.setObjectName("labelTitresimZ")
        self.YEkseniFrame = QtWidgets.QFrame(self.centralwidget)
        self.YEkseniFrame.setGeometry(QtCore.QRect(1030, 724, 329, 342))
        self.YEkseniFrame.setStyleSheet("QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.YEkseniFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.YEkseniFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.YEkseniFrame.setObjectName("YEkseniFrame")
        self.labelYEkseni = QtWidgets.QLabel(self.YEkseniFrame)
        self.labelYEkseni.setGeometry(QtCore.QRect(34, 19, 295, 39))
        font = QtGui.QFont()
        font.setFamily("Plus-Jakarta-Sans")
        font.setPointSize(-1)
        font.setBold(True)
        font.setWeight(75)
        self.labelYEkseni.setFont(font)
        self.labelYEkseni.setStyleSheet("QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus-Jakarta-Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 28px;\n"
"}")
        self.labelYEkseni.setObjectName("labelYEkseni")
        self.btnZaman = QtWidgets.QPushButton(self.YEkseniFrame)
        self.btnZaman.setGeometry(QtCore.QRect(53, 82, 223, 90))
        self.btnZaman.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 30px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
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
        self.btnZaman.setObjectName("btnZaman")
        self.btnYukseklik = QtWidgets.QPushButton(self.YEkseniFrame)
        self.btnYukseklik.setGeometry(QtCore.QRect(53, 218, 223, 90))
        self.btnYukseklik.setStyleSheet("QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"    font-family: \'Plus Jakarta Sans\';\n"
"    font-weight: bold;\n"
"    font-size: 30px;\n"
"    border-radius: 45px;\n"
"    border: 2px solid #F4F6FC;\n"
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
        self.btnYukseklik.setObjectName("btnYukseklik")
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
        self.labelXEkseni.setText(_translate("MainWindow", "X Ekseni"))
        self.btnKesmeHizi.setText(_translate("MainWindow", "Kesme\n"
"Hızı"))
        self.btnIlerlemeHizi.setText(_translate("MainWindow", "İlerleme\n"
"Hızı"))
        self.btnSeritAkim.setText(_translate("MainWindow", "Şerit\n"
"Akım"))
        self.btnSeritSapmasi.setText(_translate("MainWindow", "Şerit\n"
"Sapması"))
        self.labelKesimGrafigi.setText(_translate("MainWindow", "Kesim Grafiği"))
        self.labelKesimGrafigiInfo.setText(_translate("MainWindow", "Görüntülemek istediğiniz grafiğin X ve Y eksenini seçin."))
        self.labelAnomaliDurumu.setText(_translate("MainWindow", "Anomali Durumu"))
        self.labelMotorVerileri.setText(_translate("MainWindow", "Motor Verileri"))
        self.labelKesmeHizi.setText(_translate("MainWindow", "Kesme Hızı"))
        self.labelKesmeHiziInfo.setText(_translate("MainWindow", "14.12.2025 tarihinde anomali tespit edildi."))
        self.labelIlerlemeHiziInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelIlerlemeHizi.setText(_translate("MainWindow", "İlerleme Hızı"))
        self.labelSeritAkimInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelSeritAkim.setText(_translate("MainWindow", "Şerit Akım"))
        self.labelSensorVerileri.setText(_translate("MainWindow", "Sensör Verileri"))
        self.labelSicaklikInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelSicaklik.setText(_translate("MainWindow", "Sıcaklık"))
        self.labelNemInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelNem.setText(_translate("MainWindow", "Nem"))
        self.labelSeritSapmasiInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelSeritSapmasi.setText(_translate("MainWindow", "Şerit Sapması"))
        self.labelTitresimXInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelTitresimX.setText(_translate("MainWindow", "Titreşim X Ekseni"))
        self.labelTitresimYInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelTitresimY.setText(_translate("MainWindow", "Titreşim Y Ekseni"))
        self.labelTitresimZInfo.setText(_translate("MainWindow", "Her şey yolunda."))
        self.labelTitresimZ.setText(_translate("MainWindow", "Titreşim Z Ekseni"))
        self.labelYEkseni.setText(_translate("MainWindow", "Y Ekseni"))
        self.btnZaman.setText(_translate("MainWindow", "Zaman"))
        self.btnYukseklik.setText(_translate("MainWindow", "Yükseklik"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
