from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget, QProgressBar)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setStyleSheet(u"")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"QWidget#centralwidget {\n"
"    background-image: url(\"src/gui/images/background.png\");\n"
"    background-repeat: no-repeat;\n"
"    background-position: center;\n"
"    background-attachment: fixed;\n"
"}\n"
"")
        self.sidebarFrame = QFrame(self.centralwidget)
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
        font = QFont()
        font.setFamilies([u"Plus Jakarta Sans"])
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        self.btnControlPanel.setFont(font)
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
        icon.addFile(u"src/gui/images/control-panel-icon2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.On)
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
        self.notificationFrame = QFrame(self.centralwidget)
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
        self.cuttingFrame = QFrame(self.centralwidget)
        self.cuttingFrame.setObjectName(u"cuttingFrame")
        self.cuttingFrame.setGeometry(QRect(425, 127, 440, 344))
        self.cuttingFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.cuttingFrame.setFrameShape(QFrame.StyledPanel)
        self.cuttingFrame.setFrameShadow(QFrame.Raised)
        self.labelCuttingMode = QLabel(self.cuttingFrame)
        self.labelCuttingMode.setObjectName(u"labelCuttingMode")
        self.labelCuttingMode.setGeometry(QRect(27, 26, 381, 34))
        self.labelCuttingMode.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.btnManualMode = QPushButton(self.cuttingFrame)
        self.btnManualMode.setObjectName(u"btnManualMode")
        self.btnManualMode.setGeometry(QRect(18, 87, 180, 45))
        self.btnManualMode.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 52px;\n"
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
        self.btnAiMode = QPushButton(self.cuttingFrame)
        self.btnAiMode.setObjectName(u"btnAiMode")
        self.btnAiMode.setGeometry(QRect(241, 87, 180, 45))
        self.btnAiMode.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 32px;\n"
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
        self.btnFuzzyMode = QPushButton(self.cuttingFrame)
        self.btnFuzzyMode.setObjectName(u"btnFuzzyMode")
        self.btnFuzzyMode.setGeometry(QRect(18, 150, 180, 45))
        self.btnFuzzyMode.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 60px;\n"
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
        self.btnExpertSystemMode = QPushButton(self.cuttingFrame)
        self.btnExpertSystemMode.setObjectName(u"btnExpertSystemMode")
        self.btnExpertSystemMode.setGeometry(QRect(241, 150, 180, 45))
        self.btnExpertSystemMode.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 22px;\n"
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
        self.labelCuttingSpeed = QLabel(self.cuttingFrame)
        self.labelCuttingSpeed.setObjectName(u"labelCuttingSpeed")
        self.labelCuttingSpeed.setGeometry(QRect(27, 222, 371, 34))
        self.labelCuttingSpeed.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.btnSlowSpeed = QPushButton(self.cuttingFrame)
        self.btnSlowSpeed.setObjectName(u"btnSlowSpeed")
        self.btnSlowSpeed.setGeometry(QRect(19, 274, 120, 45))
        self.btnSlowSpeed.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 30px;\n"
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
        self.btnNormalSpeed = QPushButton(self.cuttingFrame)
        self.btnNormalSpeed.setObjectName(u"btnNormalSpeed")
        self.btnNormalSpeed.setGeometry(QRect(160, 274, 120, 45))
        self.btnNormalSpeed.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 16px;\n"
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
        self.btnFastSpeed = QPushButton(self.cuttingFrame)
        self.btnFastSpeed.setObjectName(u"btnFastSpeed")
        self.btnFastSpeed.setGeometry(QRect(300, 274, 120, 45))
        self.btnFastSpeed.setStyleSheet(u"QPushButton {\n"
"    background-color:  rgba(26, 31, 55, 200);\n"
"    color: #F4F6FC;\n"
"	font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"    font-size: 20px;\n"
"    text-align: left;\n"
"    border-radius: 20px;\n"
"	border: 2px solid #F4F6FC;\n"
"	padding-left: 38px;\n"
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
        self.headHeightFrame = QFrame(self.centralwidget)
        self.headHeightFrame.setObjectName(u"headHeightFrame")
        self.headHeightFrame.setGeometry(QRect(880, 127, 251, 344))
        self.headHeightFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.headHeightFrame.setFrameShape(QFrame.StyledPanel)
        self.headHeightFrame.setFrameShadow(QFrame.Raised)
        self.labelHeadHeight = QLabel(self.headHeightFrame)
        self.labelHeadHeight.setObjectName(u"labelHeadHeight")
        self.labelHeadHeight.setGeometry(QRect(25, 26, 211, 34))
        self.labelHeadHeight.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.labelValue = QLabel(self.headHeightFrame)
        self.labelValue.setObjectName(u"labelValue")
        self.labelValue.setGeometry(QRect(140, 140, 101, 101))
        self.labelValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.labelValue.setAlignment(Qt.AlignCenter)
        
        # Dikey progress bar ekle
        self.progressBarHeight = QProgressBar(self.headHeightFrame)
        self.progressBarHeight.setObjectName(u"progressBarHeight")
        self.progressBarHeight.setGeometry(QRect(27, 78, 50, 250))
        self.progressBarHeight.setOrientation(Qt.Vertical)
        self.progressBarHeight.setMinimum(0)
        self.progressBarHeight.setMaximum(350)  # Maksimum 350mm yükseklik
        self.progressBarHeight.setValue(0)
        self.progressBarHeight.setTextVisible(False)
        self.progressBarHeight.setStyleSheet(u"""
            QProgressBar {
                border: none;
                border-radius: 25px;
                background-color: rgba(149, 9, 82, 0.2);
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 25px;
                background-color: #950952;
                min-height: 10px;
                border-top-left-radius: 25px;
                border-top-right-radius: 25px;
                border-bottom-left-radius: 25px;
                border-bottom-right-radius: 25px;
            }
        """)
        
        # Uzunluk labelları (en üst, orta, en alt)
        self.labelHeightTop = QLabel(self.headHeightFrame)
        self.labelHeightTop.setGeometry(QRect(75, 78, 50, 32))
        self.labelHeightTop.setStyleSheet(u"QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: 500;\n"
"    font-size: 17px;\n"
"}")
        self.labelHeightTop.setText("350\nmm")
        self.labelHeightTop.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.labelHeightTop.setObjectName(u"labelHeightTop")

        self.labelHeightMid = QLabel(self.headHeightFrame)
        self.labelHeightMid.setGeometry(QRect(75, 187, 50, 32))
        self.labelHeightMid.setStyleSheet(u"QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: 500;\n"
"    font-size: 17px;\n"
"}")
        self.labelHeightMid.setText("150\nmm")
        self.labelHeightMid.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.labelHeightMid.setObjectName(u"labelHeightMid")

        self.labelHeightBottom = QLabel(self.headHeightFrame)
        self.labelHeightBottom.setGeometry(QRect(75, 296, 50, 32))
        self.labelHeightBottom.setStyleSheet(u"QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: 500;\n"
"    font-size: 17px;\n"
"}")
        self.labelHeightBottom.setText("0\nmm")
        self.labelHeightBottom.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.labelHeightBottom.setObjectName(u"labelHeightBottom")
        
        # MM label'ı ekle
        self.labelmm = QLabel(self.headHeightFrame)
        self.labelmm.setGeometry(QRect(170, 210, 41, 34))
        self.labelmm.setStyleSheet(u"QLabel{\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus-Jakarta-Sans';\n"
"    font-weight: light;\n"
"    font-size: 24px;\n"
"}")
        self.labelmm.setObjectName(u"labelmm")
        
        # LabelValue'nun konumunu progress bar'ın yanına taşı ve boyutunu genişlet
        self.labelValue.setGeometry(QRect(135, 160, 110, 60))
        self.bandDeviationFrame = QFrame(self.centralwidget)
        self.bandDeviationFrame.setObjectName(u"bandDeviationFrame")
        self.bandDeviationFrame.setGeometry(QRect(1148, 127, 401, 344))
        self.bandDeviationFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandDeviationFrame.setFrameShape(QFrame.StyledPanel)
        self.bandDeviationFrame.setFrameShadow(QFrame.Raised)
        self.labelBandDeviation = QLabel(self.bandDeviationFrame)
        self.labelBandDeviation.setObjectName(u"labelBandDeviation")
        self.labelBandDeviation.setGeometry(QRect(27, 26, 271, 34))
        self.labelBandDeviation.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.labelBandDeviation.setAlignment(Qt.AlignCenter)
        
        # Şerit sapması değer label'ı - direkt ana frame içinde
        self.labelBandDeviationValue = QLabel(self.bandDeviationFrame)
        self.labelBandDeviationValue.setObjectName(u"labelBandDeviationValue")
        self.labelBandDeviationValue.setGeometry(QRect(26, 244, 347, 80))
        font1 = QFont()
        font1.setFamilies([u"Plus-Jakarta-Sans"])
        font1.setBold(True)
        self.labelBandDeviationValue.setFont(font1)
        self.labelBandDeviationValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 48px;\n"
"}")
        self.labelBandDeviationValue.setAlignment(Qt.AlignCenter)
        
        # Şerit sapması grafik alanı
        self.bandDeviationGraphFrame = QFrame(self.bandDeviationFrame)
        self.bandDeviationGraphFrame.setObjectName(u"bandDeviationGraphFrame")
        self.bandDeviationGraphFrame.setGeometry(QRect(27, 78, 278, 144))
        self.bandDeviationGraphFrame.setStyleSheet(u"QFrame {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}")
        self.bandDeviationGraphFrame.setFrameShape(QFrame.StyledPanel)
        self.bandDeviationGraphFrame.setFrameShadow(QFrame.Raised)
        
        # Üst değer label'ı (maksimum pozitif değer)
        self.ustdegerlabel = QLabel(self.bandDeviationFrame)
        self.ustdegerlabel.setObjectName(u"ustdegerlabel")
        self.ustdegerlabel.setGeometry(QRect(325, 93, 60, 22))
        self.ustdegerlabel.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 400;\n"
"	font-size: 16px;\n"
"}")
        self.ustdegerlabel.setAlignment(Qt.AlignLeft)
        
        # Alt değer label'ı (minimum değer)
        self.altdegerlabel = QLabel(self.bandDeviationFrame)
        self.altdegerlabel.setObjectName(u"altdegerlabel")
        self.altdegerlabel.setGeometry(QRect(325, 185, 60, 22))
        self.altdegerlabel.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 400;\n"
"	font-size: 16px;\n"
"}")
        self.altdegerlabel.setAlignment(Qt.AlignLeft)
        self.systemStatusFrame = QFrame(self.centralwidget)
        self.systemStatusFrame.setObjectName(u"systemStatusFrame")
        self.systemStatusFrame.setGeometry(QRect(1568, 127, 321, 344))
        self.systemStatusFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.systemStatusFrame.setFrameShape(QFrame.StyledPanel)
        self.systemStatusFrame.setFrameShadow(QFrame.Raised)
        self.labelSystemStatus = QLabel(self.systemStatusFrame)
        self.labelSystemStatus.setObjectName(u"labelSystemStatus")
        self.labelSystemStatus.setGeometry(QRect(27, 26, 271, 34))
        self.labelSystemStatus.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.labelSystemStatusInfo = QLabel(self.systemStatusFrame)
        self.labelSystemStatusInfo.setObjectName(u"labelSystemStatusInfo")
        self.labelSystemStatusInfo.setGeometry(QRect(41, 72, 241, 141))
        self.labelSystemStatusInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 400;\n"
"	font-size: 26px;\n"
"}")
        self.labelSystemStatusInfo.setAlignment(Qt.AlignCenter)
        self.labelSystemStatusInfo.setWordWrap(True)
        self.iconStatus = QLabel(self.systemStatusFrame)
        self.iconStatus.setObjectName(u"iconStatus")
        self.iconStatus.setGeometry(QRect(121, 230, 71, 71))
        self.iconStatus.setStyleSheet(u"QLabel {\n"
"    border: none;\n"
"    background: transparent;\n"
"}\n"
"")
        self.iconStatus.setPixmap(QPixmap(u"src/gui/images/okey-icon.svg"))
        self.bandCuttingSpeedFrame = QFrame(self.centralwidget)
        self.bandCuttingSpeedFrame.setObjectName(u"bandCuttingSpeedFrame")
        self.bandCuttingSpeedFrame.setGeometry(QRect(425, 486, 551, 344))
        self.bandCuttingSpeedFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandCuttingSpeedFrame.setFrameShape(QFrame.StyledPanel)
        self.bandCuttingSpeedFrame.setFrameShadow(QFrame.Raised)
        self.labelBandCuttingSpeed = QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingSpeed.setObjectName(u"labelBandCuttingSpeed")
        self.labelBandCuttingSpeed.setGeometry(QRect(31, 27, 491, 45))
        self.labelBandCuttingSpeed.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.labelBandCuttingInfo = QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingInfo.setObjectName(u"labelBandCuttingInfo")
        self.labelBandCuttingInfo.setGeometry(QRect(31, 106, 255, 51))
        self.labelBandCuttingInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 22px;\n"
"}")
        self.BandCuttingCurrentFrame = QFrame(self.bandCuttingSpeedFrame)
        self.BandCuttingCurrentFrame.setObjectName(u"BandCuttingCurrentFrame")
        self.BandCuttingCurrentFrame.setGeometry(QRect(31, 200, 217, 109))
        self.BandCuttingCurrentFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandCuttingCurrentFrame.setFrameShape(QFrame.StyledPanel)
        self.BandCuttingCurrentFrame.setFrameShadow(QFrame.Raised)
        self.labelBandCuttingCurrent = QLabel(self.BandCuttingCurrentFrame)
        self.labelBandCuttingCurrent.setObjectName(u"labelBandCuttingCurrent")
        self.labelBandCuttingCurrent.setGeometry(QRect(23, 20, 181, 20))
        self.labelBandCuttingCurrent.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBandCuttingCurrentValue = QLabel(self.BandCuttingCurrentFrame)
        self.labelBandCuttingCurrentValue.setObjectName(u"labelBandCuttingCurrentValue")
        self.labelBandCuttingCurrentValue.setGeometry(QRect(21, 43, 171, 50))
        self.labelBandCuttingCurrentValue.setFont(font1)
        self.labelBandCuttingCurrentValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBandCuttingCurrentValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.BandCuttingTorqueFrame = QFrame(self.bandCuttingSpeedFrame)
        self.BandCuttingTorqueFrame.setObjectName(u"BandCuttingTorqueFrame")
        self.BandCuttingTorqueFrame.setGeometry(QRect(294, 200, 217, 109))
        self.BandCuttingTorqueFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandCuttingTorqueFrame.setFrameShape(QFrame.StyledPanel)
        self.BandCuttingTorqueFrame.setFrameShadow(QFrame.Raised)
        self.labelBandCuttingTorque = QLabel(self.BandCuttingTorqueFrame)
        self.labelBandCuttingTorque.setObjectName(u"labelBandCuttingTorque")
        self.labelBandCuttingTorque.setGeometry(QRect(23, 20, 181, 20))
        self.labelBandCuttingTorque.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBandCuttingTorqueValue = QLabel(self.BandCuttingTorqueFrame)
        self.labelBandCuttingTorqueValue.setObjectName(u"labelBandCuttingTorqueValue")
        self.labelBandCuttingTorqueValue.setGeometry(QRect(21, 43, 171, 50))
        self.labelBandCuttingTorqueValue.setFont(font1)
        self.labelBandCuttingTorqueValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBandCuttingTorqueValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelBandCuttingSpeedValue = QLabel(self.bandCuttingSpeedFrame)
        self.labelBandCuttingSpeedValue.setObjectName(u"labelBandCuttingSpeedValue")
        self.labelBandCuttingSpeedValue.setGeometry(QRect(300, 70, 241, 111))
        self.labelBandCuttingSpeedValue.setFont(font1)
        self.labelBandCuttingSpeedValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 80px;\n"
"}")
        self.labelBandCuttingSpeedValue.setAlignment(Qt.AlignCenter)
        self.bandDescentSpeedFrame = QFrame(self.centralwidget)
        self.bandDescentSpeedFrame.setObjectName(u"bandDescentSpeedFrame")
        self.bandDescentSpeedFrame.setGeometry(QRect(998, 486, 551, 344))
        self.bandDescentSpeedFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.bandDescentSpeedFrame.setFrameShape(QFrame.StyledPanel)
        self.bandDescentSpeedFrame.setFrameShadow(QFrame.Raised)
        self.labelBandDescentSpeed = QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentSpeed.setObjectName(u"labelBandDescentSpeed")
        self.labelBandDescentSpeed.setGeometry(QRect(31, 27, 491, 45))
        self.labelBandDescentSpeed.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 32px;\n"
"}")
        self.labelBandDescentInfo = QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentInfo.setObjectName(u"labelBandDescentInfo")
        self.labelBandDescentInfo.setGeometry(QRect(31, 106, 255, 51))
        self.labelBandDescentInfo.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 22px;\n"
"}")
        self.BandDescentCurrentFrame = QFrame(self.bandDescentSpeedFrame)
        self.BandDescentCurrentFrame.setObjectName(u"BandDescentCurrentFrame")
        self.BandDescentCurrentFrame.setGeometry(QRect(31, 200, 217, 109))
        self.BandDescentCurrentFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandDescentCurrentFrame.setFrameShape(QFrame.StyledPanel)
        self.BandDescentCurrentFrame.setFrameShadow(QFrame.Raised)
        self.labelBandDescentCurrent = QLabel(self.BandDescentCurrentFrame)
        self.labelBandDescentCurrent.setObjectName(u"labelBandDescentCurrent")
        self.labelBandDescentCurrent.setGeometry(QRect(23, 20, 181, 20))
        self.labelBandDescentCurrent.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBandDescentCurrentValue = QLabel(self.BandDescentCurrentFrame)
        self.labelBandDescentCurrentValue.setObjectName(u"labelBandDescentCurrentValue")
        self.labelBandDescentCurrentValue.setGeometry(QRect(21, 43, 171, 50))
        self.labelBandDescentCurrentValue.setFont(font1)
        self.labelBandDescentCurrentValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBandDescentCurrentValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.BandDescentTorqueFrame = QFrame(self.bandDescentSpeedFrame)
        self.BandDescentTorqueFrame.setObjectName(u"BandDescentTorqueFrame")
        self.BandDescentTorqueFrame.setGeometry(QRect(294, 200, 217, 109))
        self.BandDescentTorqueFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.BandDescentTorqueFrame.setFrameShape(QFrame.StyledPanel)
        self.BandDescentTorqueFrame.setFrameShadow(QFrame.Raised)
        self.labelBandDescentTorque = QLabel(self.BandDescentTorqueFrame)
        self.labelBandDescentTorque.setObjectName(u"labelBandDescentTorque")
        self.labelBandDescentTorque.setGeometry(QRect(23, 20, 181, 20))
        self.labelBandDescentTorque.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: medium;\n"
"	font-size: 20px;\n"
"}")
        self.labelBandDescentTorqueValue = QLabel(self.BandDescentTorqueFrame)
        self.labelBandDescentTorqueValue.setObjectName(u"labelBandDescentTorqueValue")
        self.labelBandDescentTorqueValue.setGeometry(QRect(21, 43, 171, 50))
        self.labelBandDescentTorqueValue.setFont(font1)
        self.labelBandDescentTorqueValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 36px;\n"
"}")
        self.labelBandDescentTorqueValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelBandDescentSpeedValue = QLabel(self.bandDescentSpeedFrame)
        self.labelBandDescentSpeedValue.setObjectName(u"labelBandDescentSpeedValue")
        self.labelBandDescentSpeedValue.setGeometry(QRect(300, 70, 241, 111))
        self.labelBandDescentSpeedValue.setFont(font1)
        self.labelBandDescentSpeedValue.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 80px;\n"
"}")
        self.labelBandDescentSpeedValue.setAlignment(Qt.AlignCenter)
        self.logViewerFrame = QFrame(self.centralwidget)
        self.logViewerFrame.setObjectName(u"logViewerFrame")
        self.logViewerFrame.setGeometry(QRect(1568, 486, 321, 580))
        self.logViewerFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.logViewerFrame.setFrameShape(QFrame.StyledPanel)
        self.logViewerFrame.setFrameShadow(QFrame.Raised)
        self.labelLogViewer = QLabel(self.logViewerFrame)
        self.labelLogViewer.setObjectName(u"labelLogViewer")
        self.labelLogViewer.setGeometry(QRect(27, 26, 271, 34))
        self.labelLogViewer.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: bold;\n"
"	font-size: 24px;\n"
"}")
        self.logViewerScroll = QScrollArea(self.logViewerFrame)
        self.logViewerScroll.setObjectName(u"logViewerScroll")
        self.logViewerScroll.setGeometry(QRect(30, 90, 261, 461))
        self.logViewerScroll.setStyleSheet(u"QScrollArea {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}\n"
"\n"
"QWidget#scrollAreaWidgetContents {\n"
"    background-color: transparent;\n"
"}\n"
"")
        self.logViewerScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logViewerScroll.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 261, 461))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.logViewerScroll.setWidget(self.scrollAreaWidgetContents)
        self.cuttingControlFrame = QFrame(self.centralwidget)
        self.cuttingControlFrame.setObjectName(u"cuttingControlFrame")
        self.cuttingControlFrame.setGeometry(QRect(425, 845, 1127, 221))
        self.cuttingControlFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.cuttingControlFrame.setFrameShape(QFrame.StyledPanel)
        self.cuttingControlFrame.setFrameShadow(QFrame.Raised)
        self.toolBtnCuttingStart = QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStart.setObjectName(u"toolBtnCuttingStart")
        self.toolBtnCuttingStart.setEnabled(True)
        self.toolBtnCuttingStart.setGeometry(QRect(27, 27, 220, 170))
        self.toolBtnCuttingStart.setStyleSheet(u"QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"	border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 20pt;\n"
"    font-weight: 500;\n"
"    icon-size: 115px;\n"
"	padding-top: 7px;\n"
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
        icon5 = QIcon()
        icon5.addFile(u"src/gui/images/cutting-start-icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolBtnCuttingStart.setIcon(icon5)
        self.toolBtnCuttingStart.setIconSize(QSize(105, 105))
        self.toolBtnCuttingStart.setCheckable(True)
        self.toolBtnCuttingStart.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnCuttingStop = QToolButton(self.cuttingControlFrame)
        self.toolBtnCuttingStop.setObjectName(u"toolBtnCuttingStop")
        self.toolBtnCuttingStop.setGeometry(QRect(312, 27, 220, 170))
        self.toolBtnCuttingStop.setStyleSheet(u"QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"	border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 20pt;\n"
"    font-weight: 500;\n"
"    icon-size: 115px;\n"
"	padding-top: 7px;\n"
"    padding-bottom: 15px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    background-color: rgba(255, 255, 255, 0.05);\n"
"}\n"
"\n"
"\n"
"QToolButton:checked {\n"
"    background-color: #950952;\n"
"}\n"
"")
        icon6 = QIcon()
        icon6.addFile(u"src/gui/images/cutting-stop-icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolBtnCuttingStop.setIcon(icon6)
        self.toolBtnCuttingStop.setIconSize(QSize(105, 105))
        self.toolBtnCuttingStop.setCheckable(True)
        self.toolBtnCuttingStop.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnCoolant = QToolButton(self.cuttingControlFrame)
        self.toolBtnCoolant.setObjectName(u"toolBtnCoolant")
        self.toolBtnCoolant.setGeometry(QRect(596, 27, 220, 170))
        self.toolBtnCoolant.setStyleSheet(u"QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"	border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 20pt;\n"
"    font-weight: 500;\n"
"    icon-size: 115px;\n"
"	padding-top: 7px;\n"
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
        icon7 = QIcon()
        icon7.addFile(u"src/gui/images/coolant-liquid-icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolBtnCoolant.setIcon(icon7)
        self.toolBtnCoolant.setIconSize(QSize(105, 105))
        self.toolBtnCoolant.setCheckable(True)
        self.toolBtnCoolant.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBtnSawdustCleaning = QToolButton(self.cuttingControlFrame)
        self.toolBtnSawdustCleaning.setObjectName(u"toolBtnSawdustCleaning")
        self.toolBtnSawdustCleaning.setGeometry(QRect(881, 24, 220, 170))
        self.toolBtnSawdustCleaning.setStyleSheet(u"QToolButton {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 12, 41, 255),\n"
"        stop:1 rgba(4, 12, 48, 127)\n"
"    );\n"
"    border-radius: 50px;\n"
"	border: 2px solid #F4F6FC;\n"
"    color: #F4F6FC;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-size: 20pt;\n"
"    font-weight: 500;\n"
"    icon-size: 115px;\n"
"	padding-top: 7px;\n"
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
        icon8 = QIcon()
        icon8.addFile(u"src/gui/images/sawdust-cleaning-icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolBtnSawdustCleaning.setIcon(icon8)
        self.toolBtnSawdustCleaning.setIconSize(QSize(105, 105))
        self.toolBtnSawdustCleaning.setCheckable(True)
        self.toolBtnSawdustCleaning.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.labelSmart.setText(QCoreApplication.translate("MainWindow", u"SMART", None))
        self.labelSaw.setText(QCoreApplication.translate("MainWindow", u"SAW", None))
        self.btnControlPanel.setText(QCoreApplication.translate("MainWindow", u" Kontrol Paneli", None))
        self.btnPositioning.setText(QCoreApplication.translate("MainWindow", u"Konumland\u0131rma", None))
        self.btnCamera.setText(QCoreApplication.translate("MainWindow", u"Kamera Verileri", None))
        self.btnSensor.setText(QCoreApplication.translate("MainWindow", u"Sens\u00f6r Verileri", None))
        self.btnTracking.setText(QCoreApplication.translate("MainWindow", u"\u0130zleme", None))
        self.labelDate.setText(QCoreApplication.translate("MainWindow", u"14.12.2025 \u00c7ar\u015famba", None))
        self.labelTime.setText(QCoreApplication.translate("MainWindow", u"12.30", None))
        self.labelCuttingMode.setText(QCoreApplication.translate("MainWindow", u"Kesim Modu", None))
        self.btnManualMode.setText(QCoreApplication.translate("MainWindow", u"Manuel", None))
        self.btnAiMode.setText(QCoreApplication.translate("MainWindow", u"Yapay Zeka", None))
        self.btnFuzzyMode.setText(QCoreApplication.translate("MainWindow", u"Veri", None))
        self.btnExpertSystemMode.setText(QCoreApplication.translate("MainWindow", u"Uzman Sistem", None))
        self.labelCuttingSpeed.setText(QCoreApplication.translate("MainWindow", u"Kesim H\u0131z\u0131", None))
        self.btnSlowSpeed.setText(QCoreApplication.translate("MainWindow", u"Yava\u015f", None))
        self.btnNormalSpeed.setText(QCoreApplication.translate("MainWindow", u"Standart", None))
        self.btnFastSpeed.setText(QCoreApplication.translate("MainWindow", u"H\u0131zl\u0131", None))
        self.labelHeadHeight.setText(QCoreApplication.translate("MainWindow", u"Kafa Yüksekliği", None))
        self.labelValue.setText(QCoreApplication.translate("MainWindow", u"108", None))
        self.labelmm.setText(QCoreApplication.translate("MainWindow", u"mm", None))
        self.labelBandDeviation.setText(QCoreApplication.translate("MainWindow", u"Şerit Sapması", None))
        self.labelBandDeviationValue.setText(QCoreApplication.translate("MainWindow", u"16.35", None))
        self.labelSystemStatus.setText(QCoreApplication.translate("MainWindow", u"Sistem Durumu", None))
        self.labelSystemStatusInfo.setText(QCoreApplication.translate("MainWindow", u"Her \u015eey Yolunda !", None))
        self.iconStatus.setText("")
        self.labelBandCuttingSpeed.setText(QCoreApplication.translate("MainWindow", u"\u015eerit Kesme H\u0131z\u0131", None))
        self.labelBandCuttingInfo.setText(QCoreApplication.translate("MainWindow", u"Ba\u015flang\u0131\u00e7 h\u0131z\u0131n\u0131\n"
"belirlemek i\u00e7in t\u0131klay\u0131n.", None))
        self.labelBandCuttingCurrent.setText(QCoreApplication.translate("MainWindow", u"\u015eerit Motor Ak\u0131m", None))
        self.labelBandCuttingCurrentValue.setText(QCoreApplication.translate("MainWindow", u"16.35", None))
        self.labelBandCuttingTorque.setText(QCoreApplication.translate("MainWindow", u"\u015eerit Motor Tork", None))
        self.labelBandCuttingTorqueValue.setText(QCoreApplication.translate("MainWindow", u"16.35", None))
        self.labelBandCuttingSpeedValue.setText(QCoreApplication.translate("MainWindow", u"16", None))
        self.labelBandDescentSpeed.setText(QCoreApplication.translate("MainWindow", u"\u015eerit \u0130nme H\u0131z\u0131", None))
        self.labelBandDescentInfo.setText(QCoreApplication.translate("MainWindow", u"Ba\u015flang\u0131\u00e7 h\u0131z\u0131n\u0131\n"
"belirlemek i\u00e7in t\u0131klay\u0131n.", None))
        self.labelBandDescentCurrent.setText(QCoreApplication.translate("MainWindow", u"\u0130nme Motor Ak\u0131m", None))
        self.labelBandDescentCurrentValue.setText(QCoreApplication.translate("MainWindow", u"16.35", None))
        self.labelBandDescentTorque.setText(QCoreApplication.translate("MainWindow", u"\u0130nme Motor Tork", None))
        self.labelBandDescentTorqueValue.setText(QCoreApplication.translate("MainWindow", u"16.35", None))
        self.labelBandDescentSpeedValue.setText(QCoreApplication.translate("MainWindow", u"16", None))
        self.labelLogViewer.setText(QCoreApplication.translate("MainWindow", u"\u00c7al\u0131\u015fma G\u00fcnl\u00fc\u011f\u00fc", None))
        self.toolBtnCuttingStart.setText(QCoreApplication.translate("MainWindow", u"Kesim Ba\u015flat", None))
        self.toolBtnCuttingStop.setText(QCoreApplication.translate("MainWindow", u"Kesim Durdur", None))
        self.toolBtnCoolant.setText(QCoreApplication.translate("MainWindow", u"So\u011futma S\u0131v\u0131s\u0131", None))
        self.toolBtnSawdustCleaning.setText(QCoreApplication.translate("MainWindow", u"Tala\u015f Temizlik", None))
    # retranslateUi

