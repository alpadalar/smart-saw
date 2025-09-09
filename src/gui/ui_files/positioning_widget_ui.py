
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
        self.labelSmart_2 = QLabel(self.sidebarFrame)
        self.labelSmart_2.setObjectName(u"labelSmart_2")
        self.labelSmart_2.setGeometry(QRect(31, 32, 330, 73))
        self.labelSmart_2.setStyleSheet(u"QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-weight: bold;\n"
"}\n"
"")
        self.labelSaw_2 = QLabel(self.sidebarFrame)
        self.labelSaw_2.setObjectName(u"labelSaw_2")
        self.labelSaw_2.setGeometry(QRect(230, 32, 150, 73))
        self.labelSaw_2.setStyleSheet(u"QLabel {\n"
"    background-color: transparent;\n"
"    color: #F4F6FC;\n"
"    font-size: 58px;\n"
"    font-family: 'Plus Jakarta Sans';\n"
"    font-weight: 100\n"
";\n"
"}\n"
"")
        self.lineSmartSaw_2 = QFrame(self.sidebarFrame)
        self.lineSmartSaw_2.setObjectName(u"lineSmartSaw_2")
        self.lineSmartSaw_2.setGeometry(QRect(30, 110, 332, 3))
        self.lineSmartSaw_2.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1: 0, y1: 0, x2: 1, y2: 0,\n"
"        stop: 0 rgba(255, 255, 255, 0),\n"
"        stop: 0.5 rgba(255, 255, 255, 100),\n"
"        stop: 1 rgba(255, 255, 255, 0)\n"
"    );\n"
"    border: none;\n"
"}\n"
"")
        self.lineSmartSaw_2.setFrameShadow(QFrame.Plain)
        self.lineSmartSaw_2.setLineWidth(1)
        self.lineSmartSaw_2.setFrameShape(QFrame.Shape.HLine)
        self.btnControlPanel_2 = QPushButton(self.sidebarFrame)
        self.btnControlPanel_2.setObjectName(u"btnControlPanel_2")
        self.btnControlPanel_2.setGeometry(QRect(26, 165, 355, 110))
        font = QFont()
        font.setFamilies([u"Plus Jakarta Sans"])
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        self.btnControlPanel_2.setFont(font)
        self.btnControlPanel_2.setMouseTracking(True)
        self.btnControlPanel_2.setStyleSheet(u"QPushButton {\n"
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
        self.btnControlPanel_2.setIcon(icon)
        self.btnControlPanel_2.setIconSize(QSize(70, 70))
        self.btnPositioning_2 = QPushButton(self.sidebarFrame)
        self.btnPositioning_2.setObjectName(u"btnPositioning_2")
        self.btnPositioning_2.setGeometry(QRect(26, 286, 355, 110))
        self.btnPositioning_2.setStyleSheet(u"QPushButton {\n"
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
        self.btnPositioning_2.setIcon(icon1)
        self.btnPositioning_2.setIconSize(QSize(80, 80))
        self.btnCamera_2 = QPushButton(self.sidebarFrame)
        self.btnCamera_2.setObjectName(u"btnCamera_2")
        self.btnCamera_2.setGeometry(QRect(26, 407, 355, 110))
        self.btnCamera_2.setStyleSheet(u"QPushButton {\n"
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
        self.btnCamera_2.setIcon(icon2)
        self.btnCamera_2.setIconSize(QSize(80, 80))
        self.btnSensor_2 = QPushButton(self.sidebarFrame)
        self.btnSensor_2.setObjectName(u"btnSensor_2")
        self.btnSensor_2.setGeometry(QRect(26, 528, 355, 110))
        self.btnSensor_2.setStyleSheet(u"QPushButton {\n"
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
        self.btnSensor_2.setIcon(icon3)
        self.btnSensor_2.setIconSize(QSize(80, 80))
        self.btnTracking_2 = QPushButton(self.sidebarFrame)
        self.btnTracking_2.setObjectName(u"btnTracking_2")
        self.btnTracking_2.setGeometry(QRect(27, 649, 355, 110))
        self.btnTracking_2.setStyleSheet(u"QPushButton {\n"
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
        self.btnTracking_2.setIcon(icon4)
        self.btnTracking_2.setIconSize(QSize(80, 80))
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
        self.mengeneKontroluFrame = QFrame(Form)
        self.mengeneKontroluFrame.setObjectName(u"mengeneKontroluFrame")
        self.mengeneKontroluFrame.setGeometry(QRect(425, 127, 461, 939))
        self.mengeneKontroluFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.mengeneKontroluFrame.setFrameShape(QFrame.StyledPanel)
        self.mengeneKontroluFrame.setFrameShadow(QFrame.Raised)
        self.labelMengeneKontrolu = QLabel(self.mengeneKontroluFrame)
        self.labelMengeneKontrolu.setObjectName(u"labelMengeneKontrolu")
        self.labelMengeneKontrolu.setGeometry(QRect(4, 19, 451, 45))
        font1 = QFont()
        font1.setFamilies([u"Plus-Jakarta-Sans"])
        font1.setBold(True)
        self.labelMengeneKontrolu.setFont(font1)
        self.labelMengeneKontrolu.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 500;\n"
"	font-size: 31px;\n"
"}")
        self.labelMengeneKontrolu.setAlignment(Qt.AlignCenter)
        self.btnArkaMengeneAc = QPushButton(self.mengeneKontroluFrame)
        self.btnArkaMengeneAc.setObjectName(u"btnArkaMengeneAc")
        self.btnArkaMengeneAc.setGeometry(QRect(97, 104, 254, 251))
        self.btnArkaMengeneAc.setStyleSheet(u"QPushButton {\n"
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
        icon5 = QIcon()
        icon5.addFile(u"src/gui/images/arka-mengene-ac.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnArkaMengeneAc.setIcon(icon5)
        self.btnArkaMengeneAc.setIconSize(QSize(205, 205))
        self.btnArkaMengeneAc.setCheckable(True)
        self.btnMengeneKapat = QPushButton(self.mengeneKontroluFrame)
        self.btnMengeneKapat.setObjectName(u"btnMengeneKapat")
        self.btnMengeneKapat.setGeometry(QRect(97, 379, 254, 251))
        self.btnMengeneKapat.setStyleSheet(u"QPushButton {\n"
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
        icon6 = QIcon()
        icon6.addFile(u"src/gui/images/mengene-sikistir.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnMengeneKapat.setIcon(icon6)
        self.btnMengeneKapat.setIconSize(QSize(205, 205))
        self.btnMengeneKapat.setCheckable(True)
        self.btnOnMengeneAc = QPushButton(self.mengeneKontroluFrame)
        self.btnOnMengeneAc.setObjectName(u"btnOnMengeneAc")
        self.btnOnMengeneAc.setGeometry(QRect(97, 654, 254, 251))
        self.btnOnMengeneAc.setStyleSheet(u"QPushButton {\n"
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
        icon7 = QIcon()
        icon7.addFile(u"src/gui/images/on-mengene-ac.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnOnMengeneAc.setIcon(icon7)
        self.btnOnMengeneAc.setIconSize(QSize(205, 205))
        self.btnOnMengeneAc.setCheckable(True)
        self.malzemeKonumlandirmaFrame = QFrame(Form)
        self.malzemeKonumlandirmaFrame.setObjectName(u"malzemeKonumlandirmaFrame")
        self.malzemeKonumlandirmaFrame.setGeometry(QRect(918, 127, 481, 939))
        self.malzemeKonumlandirmaFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.malzemeKonumlandirmaFrame.setFrameShape(QFrame.StyledPanel)
        self.malzemeKonumlandirmaFrame.setFrameShadow(QFrame.Raised)
        self.labelMalzemeKonumlandirma_2 = QLabel(self.malzemeKonumlandirmaFrame)
        self.labelMalzemeKonumlandirma_2.setObjectName(u"labelMalzemeKonumlandirma_2")
        self.labelMalzemeKonumlandirma_2.setGeometry(QRect(4, 19, 471, 45))
        self.labelMalzemeKonumlandirma_2.setFont(font1)
        self.labelMalzemeKonumlandirma_2.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 500;\n"
"	font-size: 31px;\n"
"}")
        self.labelMalzemeKonumlandirma_2.setAlignment(Qt.AlignCenter)
        self.btnMalzemeGeri = QPushButton(self.malzemeKonumlandirmaFrame)
        self.btnMalzemeGeri.setObjectName(u"btnMalzemeGeri")
        self.btnMalzemeGeri.setGeometry(QRect(50, 104, 382, 378))
        self.btnMalzemeGeri.setStyleSheet(u"QPushButton {\n"
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
        icon8 = QIcon()
        icon8.addFile(u"src/gui/images/malzeme-geri-icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnMalzemeGeri.setIcon(icon8)
        self.btnMalzemeGeri.setIconSize(QSize(265, 265))
        self.btnMalzemeGeri.setCheckable(True)
        self.btnMalzemeIleri = QPushButton(self.malzemeKonumlandirmaFrame)
        self.btnMalzemeIleri.setObjectName(u"btnMalzemeIleri")
        self.btnMalzemeIleri.setGeometry(QRect(50, 526, 382, 378))
        self.btnMalzemeIleri.setStyleSheet(u"QPushButton {\n"
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
        icon9 = QIcon()
        icon9.addFile(u"src/gui/images/malzeme-ileri-icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnMalzemeIleri.setIcon(icon9)
        self.btnMalzemeIleri.setIconSize(QSize(265, 265))
        self.btnMalzemeIleri.setCheckable(True)
        self.testereKonumlandirmaFrame = QFrame(Form)
        self.testereKonumlandirmaFrame.setObjectName(u"testereKonumlandirmaFrame")
        self.testereKonumlandirmaFrame.setGeometry(QRect(1430, 127, 461, 939))
        self.testereKonumlandirmaFrame.setStyleSheet(u"QFrame {\n"
"    background: qlineargradient(\n"
"        x1:0, y1:0, x2:0, y2:1,\n"
"        stop:0 rgba(6, 11, 38, 240),\n"
"        stop:1 rgba(26, 31, 55, 0)\n"
"    );\n"
"    border-radius: 20px;\n"
"}\n"
"")
        self.testereKonumlandirmaFrame.setFrameShape(QFrame.StyledPanel)
        self.testereKonumlandirmaFrame.setFrameShadow(QFrame.Raised)
        self.labelTestereKonumlandirma = QLabel(self.testereKonumlandirmaFrame)
        self.labelTestereKonumlandirma.setObjectName(u"labelTestereKonumlandirma")
        self.labelTestereKonumlandirma.setGeometry(QRect(4, 19, 451, 45))
        self.labelTestereKonumlandirma.setFont(font1)
        self.labelTestereKonumlandirma.setStyleSheet(u"QLabel{\n"
"	background-color: transparent;\n"
"	color: #F4F6FC;\n"
"	font-family: 'Plus-Jakarta-Sans';\n"
"	font-weight: 500;\n"
"	font-size: 31px;\n"
"}")
        self.labelTestereKonumlandirma.setAlignment(Qt.AlignCenter)
        self.btnTestereYukari = QPushButton(self.testereKonumlandirmaFrame)
        self.btnTestereYukari.setObjectName(u"btnTestereYukari")
        self.btnTestereYukari.setGeometry(QRect(41, 104, 382, 378))
        self.btnTestereYukari.setStyleSheet(u"QPushButton {\n"
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
        icon10 = QIcon()
        icon10.addFile(u"src/gui/images/saw-up-icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnTestereYukari.setIcon(icon10)
        self.btnTestereYukari.setIconSize(QSize(265, 265))
        self.btnTestereYukari.setCheckable(True)
        self.btnTestereAsagi = QPushButton(self.testereKonumlandirmaFrame)
        self.btnTestereAsagi.setObjectName(u"btnTestereAsagi")
        self.btnTestereAsagi.setGeometry(QRect(41, 526, 382, 378))
        self.btnTestereAsagi.setStyleSheet(u"QPushButton {\n"
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
        icon11 = QIcon()
        icon11.addFile(u"src/gui/images/saw-down-icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnTestereAsagi.setIcon(icon11)
        self.btnTestereAsagi.setIconSize(QSize(265, 265))
        self.btnTestereAsagi.setCheckable(True)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelSmart_2.setText(QCoreApplication.translate("Form", u"SMART", None))
        self.labelSaw_2.setText(QCoreApplication.translate("Form", u"SAW", None))
        self.btnControlPanel_2.setText(QCoreApplication.translate("Form", u" Kontrol Paneli", None))
        self.btnPositioning_2.setText(QCoreApplication.translate("Form", u"Konumland\u0131rma", None))
        self.btnCamera_2.setText(QCoreApplication.translate("Form", u"Kamera Verileri", None))
        self.btnSensor_2.setText(QCoreApplication.translate("Form", u"Sens\u00f6r Verileri", None))
        self.btnTracking_2.setText(QCoreApplication.translate("Form", u"\u0130zleme", None))
        self.labelDate.setText(QCoreApplication.translate("Form", u"14.12.2025 \u00c7ar\u015famba", None))
        self.labelTime.setText(QCoreApplication.translate("Form", u"12.30", None))
        self.labelMengeneKontrolu.setText(QCoreApplication.translate("Form", u"Mengene Kontrol\u00fc", None))
        self.btnArkaMengeneAc.setText("")
        self.btnMengeneKapat.setText("")
        self.btnOnMengeneAc.setText("")
        self.labelMalzemeKonumlandirma_2.setText(QCoreApplication.translate("Form", u"Malzeme Konumland\u0131rma", None))
        self.btnMalzemeGeri.setText("")
        self.btnMalzemeIleri.setText("")
        self.labelTestereKonumlandirma.setText(QCoreApplication.translate("Form", u"Testere Konumland\u0131rma", None))
        self.btnTestereYukari.setText("")
        self.btnTestereAsagi.setText("")
    # retranslateUi

