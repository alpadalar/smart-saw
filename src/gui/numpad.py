from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QPushButton, QToolButton
from PySide6.QtGui import QIcon


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(763, 800)
        Dialog.setStyleSheet("background-color: rgb(6, 15, 42);")
        self.frame = QFrame(Dialog)
        self.frame.setGeometry(31, 37, 701, 184)
        self.frame.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setObjectName("frame")
        self.label = QLabel(self.frame)
        self.label.setGeometry(4, 0, 691, 184)
        self.label.setStyleSheet("background-color: transparent;\n"
"color: rgb(244, 246, 252);\n"
"font:125pt \"Plus Jakarta Sans\";\n"
"font-weight:bold;\n"
"padding-bottom: 22px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("label")
        self.pushButton = QPushButton(Dialog)
        self.pushButton.setGeometry(31, 249, 217, 109)
        self.pushButton.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QPushButton(Dialog)
        self.pushButton_2.setGeometry(273, 249, 217, 109)
        self.pushButton_2.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QPushButton(Dialog)
        self.pushButton_3.setGeometry(515, 249, 217, 109)
        self.pushButton_3.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_4 = QPushButton(Dialog)
        self.pushButton_4.setGeometry(31, 387, 217, 109)
        self.pushButton_4.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QPushButton(Dialog)
        self.pushButton_5.setGeometry(273, 387, 217, 109)
        self.pushButton_5.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_6 = QPushButton(Dialog)
        self.pushButton_6.setGeometry(515, 387, 217, 109)
        self.pushButton_6.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_7 = QPushButton(Dialog)
        self.pushButton_7.setGeometry(31, 524, 217, 109)
        self.pushButton_7.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_8 = QPushButton(Dialog)
        self.pushButton_8.setGeometry(273, 524, 217, 109)
        self.pushButton_8.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_9 = QPushButton(Dialog)
        self.pushButton_9.setGeometry(515, 524, 217, 109)
        self.pushButton_9.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_9.setObjectName("pushButton_9")
        self.pushButton_11 = QPushButton(Dialog)
        self.pushButton_11.setGeometry(273, 661, 217, 109)
        self.pushButton_11.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"font: 75pt \"Plus Jakarta Sans\";\n"
"font-weight: bold;\n"
"color: rgb(244, 246, 252);\n"
"padding-bottom:13px;")
        self.pushButton_11.setObjectName("pushButton_11")
        self.toolButton = QToolButton(Dialog)
        self.toolButton.setGeometry(31, 661, 217, 109)
        self.toolButton.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.toolButton.setText("")
        icon = QIcon()
        icon.addPixmap("src/gui/images/backspace.png")
        self.toolButton.setIcon(icon)
        self.toolButton.setIconSize(QSize(88, 70))
        self.toolButton.setObjectName("toolButton")
        self.toolButton_2 = QToolButton(Dialog)
        self.toolButton_2.setGeometry(515, 661, 217, 109)
        self.toolButton_2.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.toolButton_2.setText("")
        icon1 = QIcon()
        icon1.addPixmap("src/gui/images/enter.png")
        self.toolButton_2.setIcon(icon1)
        self.toolButton_2.setIconSize(QSize(75, 85))
        self.toolButton_2.setObjectName("toolButton_2")

        self.retranslateUi(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle("Numpad Dialog")
        self.label.setText("0")
        self.pushButton.setText("1")
        self.pushButton_2.setText("2")
        self.pushButton_3.setText("3")
        self.pushButton_4.setText("4")
        self.pushButton_5.setText("5")
        self.pushButton_6.setText("6")
        self.pushButton_7.setText("7")
        self.pushButton_8.setText("8")
        self.pushButton_9.setText("9")
        self.pushButton_11.setText("0")


class NumpadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.value = ""
        self.Accepted = QDialog.Accepted  # Accepted attribute'unu ekle
        self.setup_connections()
        self.update_label()
        
        # Dialog'u modal yap
        self.setModal(True)
        # Dialog'u kendi boyutunda göster
        self.show()
        # Dialog'u ekranın ortasında konumlandır
        self.center_on_screen()

    def center_on_screen(self):
        """Dialog'u ekranın ortasında konumlandırır"""
        # Ekran geometrisini al
        screen = self.screen()
        screen_geometry = screen.geometry()
        
        # Dialog boyutunu al
        dialog_geometry = self.geometry()
        
        # Merkez koordinatlarını hesapla
        x = (screen_geometry.width() - dialog_geometry.width()) // 2
        y = (screen_geometry.height() - dialog_geometry.height()) // 2
        
        # Dialog'u konumlandır
        self.move(x, y)

    def setup_connections(self):
        self.ui.pushButton.clicked.connect(lambda: self.add_digit('1'))
        self.ui.pushButton_2.clicked.connect(lambda: self.add_digit('2'))
        self.ui.pushButton_3.clicked.connect(lambda: self.add_digit('3'))
        self.ui.pushButton_4.clicked.connect(lambda: self.add_digit('4'))
        self.ui.pushButton_5.clicked.connect(lambda: self.add_digit('5'))
        self.ui.pushButton_6.clicked.connect(lambda: self.add_digit('6'))
        self.ui.pushButton_7.clicked.connect(lambda: self.add_digit('7'))
        self.ui.pushButton_8.clicked.connect(lambda: self.add_digit('8'))
        self.ui.pushButton_9.clicked.connect(lambda: self.add_digit('9'))
        self.ui.pushButton_11.clicked.connect(lambda: self.add_digit('0'))
        self.ui.toolButton.clicked.connect(self.backspace)
        self.ui.toolButton_2.clicked.connect(self.accept)

    def add_digit(self, digit):
        if len(self.value) < 10:
            self.value += digit
            self.update_label()

    def backspace(self):
        if self.value:
            self.value = self.value[:-1]
            self.update_label()

    def update_label(self):
        self.ui.label.setText(self.value if self.value else "0")

    def get_value(self):
        return self.value

    def accept(self):
        super().accept()

    def showEvent(self, event):
        self.value = ""
        self.update_label()
        super().showEvent(event)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = NumpadDialog()
    if dialog.exec() == QDialog.Accepted:
        print("Girilen değer:", dialog.get_value())
