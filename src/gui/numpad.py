from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(763, 800)
        Dialog.setStyleSheet("background-color: rgb(6, 15, 42);")
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setGeometry(QtCore.QRect(31, 37, 701, 184))
        self.frame.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(4, 0, 691, 184))
        self.label.setStyleSheet("background-color: transparent;\n"
"color: rgb(244, 246, 252);\n"
"font:125pt \"Plus Jakarta Sans\";\n"
"font-weight:bold;\n"
"padding-bottom: 22px;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(31, 249, 217, 109))
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
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(273, 249, 217, 109))
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
        self.pushButton_3 = QtWidgets.QPushButton(Dialog)
        self.pushButton_3.setGeometry(QtCore.QRect(515, 249, 217, 109))
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
        self.pushButton_4 = QtWidgets.QPushButton(Dialog)
        self.pushButton_4.setGeometry(QtCore.QRect(31, 387, 217, 109))
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
        self.pushButton_5 = QtWidgets.QPushButton(Dialog)
        self.pushButton_5.setGeometry(QtCore.QRect(273, 387, 217, 109))
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
        self.pushButton_6 = QtWidgets.QPushButton(Dialog)
        self.pushButton_6.setGeometry(QtCore.QRect(515, 387, 217, 109))
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
        self.pushButton_7 = QtWidgets.QPushButton(Dialog)
        self.pushButton_7.setGeometry(QtCore.QRect(31, 524, 217, 109))
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
        self.pushButton_8 = QtWidgets.QPushButton(Dialog)
        self.pushButton_8.setGeometry(QtCore.QRect(273, 524, 217, 109))
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
        self.pushButton_9 = QtWidgets.QPushButton(Dialog)
        self.pushButton_9.setGeometry(QtCore.QRect(515, 524, 217, 109))
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
        self.pushButton_11 = QtWidgets.QPushButton(Dialog)
        self.pushButton_11.setGeometry(QtCore.QRect(273, 661, 217, 109))
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
        self.toolButton = QtWidgets.QToolButton(Dialog)
        self.toolButton.setGeometry(QtCore.QRect(31, 661, 217, 109))
        self.toolButton.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.toolButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("src\\gui\\images/backspace.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setIconSize(QtCore.QSize(88, 70))
        self.toolButton.setObjectName("toolButton")
        self.toolButton_2 = QtWidgets.QToolButton(Dialog)
        self.toolButton_2.setGeometry(QtCore.QRect(515, 661, 217, 109))
        self.toolButton_2.setStyleSheet("background-color: qlineargradient(\n"
"    x1: 0, y1: 1,\n"
"    x2: 0.5, y2: 0,\n"
"    stop: 0 #040c30,\n"
"    stop: 1 #226afc\n"
");\n"
"border-radius: 20px;\n"
"")
        self.toolButton_2.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("src\\gui\\images/enter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_2.setIcon(icon1)
        self.toolButton_2.setIconSize(QtCore.QSize(75, 85))
        self.toolButton_2.setObjectName("toolButton_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "777.77"))
        self.pushButton.setText(_translate("Dialog", "1"))
        self.pushButton_2.setText(_translate("Dialog", "2"))
        self.pushButton_3.setText(_translate("Dialog", "3"))
        self.pushButton_4.setText(_translate("Dialog", "4"))
        self.pushButton_5.setText(_translate("Dialog", "5"))
        self.pushButton_6.setText(_translate("Dialog", "6"))
        self.pushButton_7.setText(_translate("Dialog", "7"))
        self.pushButton_8.setText(_translate("Dialog", "8"))
        self.pushButton_9.setText(_translate("Dialog", "9"))
        self.pushButton_11.setText(_translate("Dialog", "0"))


class NumpadDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.value = ""
        self.setup_connections()
        self.update_label()

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
    app = QtWidgets.QApplication(sys.argv)
    dialog = NumpadDialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print("Girilen değer:", dialog.get_value())
