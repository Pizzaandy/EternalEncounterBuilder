import resources
from PyQt5 import QtCore, QtGui, QtWidgets
import ebl_compiler as compiler
from ebl_compiler import CACHE_FILE
from pathlib import Path

import sys
import os
import json

import multiprocessing


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    log_data = QtCore.pyqtSignal(str)

    def worker_log(self, s):
        self.log_data.emit(s)

    def run(self):
        compiler.worker_object = self
        ebl_file = ui.ebl_file_box.toPlainText().strip()
        entities_file = ui.base_entities_box.toPlainText().strip()
        output_folder = ui.output_file_box.toPlainText().strip()
        show_checkpoints = ui.checkpoints_box.isChecked()
        compress = ui.compress_box.isChecked()
        show_targets = ui.show_targets_box.isChecked()
        do_check = ui.punctuation_box.isChecked()

        do_compile = True

        if not ebl_file:
            self.worker_log("No EBL file provided, skipped")
            ebl_file = None
        elif not Path(ebl_file).exists():
            self.worker_log("EBL file does not exist!")
            do_compile = False

        if not entities_file or not Path(entities_file).exists():
            self.worker_log("Entities file does not exist!")
            do_compile = False

        if not output_folder or not Path(output_folder).exists():
            self.worker_log("Output folder does not exist!")
            do_compile = False

        if compress:
            oodle_name = (
                "liblinoodle.so" if "linux" in sys.platform else "oo2core_8_win64.dll"
            )
            if not Path(oodle_name).exists():
                self.worker_log(f"{oodle_name} is not in the folder!")
                self.worker_log("Cannot compress file!")
                do_compile = False

        for file in [
            "idAI2_base.txt",
            "idAI2_dlc1.txt",
            "idAI2_dlc2.txt",
            "anim_offsets.txt",
        ]:
            if not os.path.exists(file):
                self.worker_log(f"{file} not found in folder!")
                do_compile = False

        if not do_compile:
            self.worker_log("Failed to build!")
            self.finished.emit()
            return

        try:
            compiler.apply_ebl(
                ebl_file=ebl_file,
                base_file=entities_file,
                output_folder=output_folder,
                show_checkpoints=show_checkpoints,
                compress_file=compress,
                show_spawn_targets=show_targets,
                do_punctuation_check=do_check,
            )
        except Exception as e:
            print(e)
            self.worker_log(e)
            self.worker_log("Failed to build!")

        self.finished.emit()


class Ui_MainWindow(object):
    def __init__(self):
        self.worker = Worker()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(628, 563)
        MainWindow.setMaximumSize(QtCore.QSize(628, 563))
        MainWindow.setWindowIcon(QtGui.QIcon(":/icons/hammer_logo.ico"))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth()
        )
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QtCore.QSize(628, 522))
        self.centralwidget.setObjectName("centralwidget")
        self.base_entities_box = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.base_entities_box.setGeometry(QtCore.QRect(60, 40, 551, 31))
        self.base_entities_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.base_entities_box.setFont(font)
        self.base_entities_box.setObjectName("base_entities_box")
        self.base_entities_label = QtWidgets.QLabel(self.centralwidget)
        self.base_entities_label.setGeometry(QtCore.QRect(20, 10, 151, 21))
        self.base_entities_label.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.base_entities_label.setFont(font)
        self.base_entities_label.setObjectName("base_entities_label")
        self.ebl_file_box = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.ebl_file_box.setGeometry(QtCore.QRect(60, 110, 551, 31))
        self.ebl_file_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.ebl_file_box.setFont(font)
        self.ebl_file_box.setObjectName("ebl_file_box")

        self.punctuation_box = QtWidgets.QCheckBox(self.centralwidget)
        self.punctuation_box.setGeometry(QtCore.QRect(20, 320, 121, 17))
        self.punctuation_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.punctuation_box.setFont(font)
        self.punctuation_box.setObjectName("punctuation_box")

        self.checkpoints_box = QtWidgets.QCheckBox(self.centralwidget)
        self.checkpoints_box.setGeometry(QtCore.QRect(20, 350, 200, 17))
        self.checkpoints_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkpoints_box.setFont(font)
        self.checkpoints_box.setObjectName("checkpoints_box")

        self.compress_box = QtWidgets.QCheckBox(self.centralwidget)
        self.compress_box.setGeometry(QtCore.QRect(20, 380, 121, 17))
        self.compress_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.compress_box.setFont(font)
        self.compress_box.setObjectName("compress_box")
        self.show_targets_box = QtWidgets.QCheckBox(self.centralwidget)
        self.show_targets_box.setGeometry(QtCore.QRect(20, 410, 171, 17))
        self.show_targets_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.show_targets_box.setFont(font)
        self.show_targets_box.setObjectName("show_targets_box")
        self.ebl_fileselect = QtWidgets.QToolButton(self.centralwidget)
        self.ebl_fileselect.setGeometry(QtCore.QRect(20, 110, 31, 31))
        self.ebl_fileselect.setMaximumSize(QtCore.QSize(628, 522))
        self.ebl_fileselect.setObjectName("ebl_fileselect")
        self.base_entities_fileselect = QtWidgets.QToolButton(self.centralwidget)
        self.base_entities_fileselect.setGeometry(QtCore.QRect(20, 40, 31, 31))
        self.base_entities_fileselect.setMaximumSize(QtCore.QSize(628, 522))
        self.base_entities_fileselect.setObjectName("base_entities_fileselect")
        self.build_btn = QtWidgets.QPushButton(self.centralwidget)
        self.build_btn.setGeometry(QtCore.QRect(20, 450, 161, 71))
        self.build_btn.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.build_btn.setFont(font)
        self.build_btn.setObjectName("build_btn")
        self.build_btn.clicked.connect(self.build_process)
        self.ebl_file_label = QtWidgets.QLabel(self.centralwidget)
        self.ebl_file_label.setGeometry(QtCore.QRect(20, 80, 151, 21))
        self.ebl_file_label.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.ebl_file_label.setFont(font)
        self.ebl_file_label.setObjectName("ebl_file_label")
        self.output_file_box = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.output_file_box.setGeometry(QtCore.QRect(60, 180, 551, 31))
        self.output_file_box.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.output_file_box.setFont(font)
        self.output_file_box.setObjectName("ebl_file_box_2")
        self.output_fileselect = QtWidgets.QToolButton(self.centralwidget)
        self.output_fileselect.setGeometry(QtCore.QRect(20, 180, 31, 31))
        self.output_fileselect.setMaximumSize(QtCore.QSize(628, 522))
        self.output_fileselect.setObjectName("ebl_fileselect_2")
        self.output_file_label = QtWidgets.QLabel(self.centralwidget)
        self.output_file_label.setGeometry(QtCore.QRect(20, 150, 151, 21))
        self.output_file_label.setMaximumSize(QtCore.QSize(628, 522))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.output_file_label.setFont(font)
        self.output_file_label.setObjectName("ebl_file_label_2")
        self.log_browser = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.log_browser.setGeometry(QtCore.QRect(200, 231, 411, 291))
        self.log_browser.setMaximumSize(QtCore.QSize(628, 522))
        self.log_browser.setReadOnly(True)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(8)
        self.log_browser.setFont(font)
        self.log_browser.setObjectName("log_browser")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 628, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Encounter Builder"))
        self.base_entities_label.setText(
            _translate("MainWindow", "Vanilla .entities file")
        )
        self.punctuation_box.setText(_translate("MainWindow", "Verify File"))
        self.checkpoints_box.setText(_translate("MainWindow", "List Checkpoints"))
        self.compress_box.setText(_translate("MainWindow", "Compress"))
        self.show_targets_box.setText(
            _translate("MainWindow", "Visualize Spawn Targets")
        )
        self.ebl_fileselect.setText(_translate("MainWindow", "..."))
        self.base_entities_fileselect.setText(_translate("MainWindow", "..."))
        self.build_btn.setText(_translate("MainWindow", "Build"))
        self.ebl_file_label.setText(_translate("MainWindow", "EBL file"))
        self.output_fileselect.setText(_translate("MainWindow", "..."))
        self.output_file_label.setText(_translate("MainWindow", "Output path"))

    def build_process(self):
        try:
            clear_log()
            self.worker = Worker()
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.log_data.connect(self.log)
            self.thread.start()

            self.build_btn.setEnabled(False)
            self.thread.finished.connect(lambda: self.build_btn.setEnabled(True))
        except Exception as e:
            print(e)

    def log(self, s):
        self.log_browser.appendPlainText(str(s))


ui = Ui_MainWindow()
app = QtWidgets.QApplication(sys.argv)
Win = QtWidgets.QMainWindow()
ui.setupUi(Win)


def set_base_entities_fp():
    fp = QtWidgets.QFileDialog.getOpenFileName(
        Win, "Select an Entities File", filter="Entities file (*.entities)"
    )
    print(fp)
    if not fp[0]:
        return
    ui.base_entities_box.setPlainText(str(fp[0]))


def set_ebl_fp():
    fp = QtWidgets.QFileDialog.getOpenFileName(
        Win, "Select an EBL File", filter="EBL file (*.ebl)"
    )
    if not fp[0]:
        return
    ui.ebl_file_box.setPlainText(str(fp[0]))


def set_output_fp():
    fp = QtWidgets.QFileDialog.getExistingDirectory(
        Win,
        "Select an Output Folder",
    )
    if not fp:
        return
    ui.output_file_box.setPlainText(str(fp))


def clear_log():
    ui.log_browser.clear()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    Win.show()
    print("eeee")
    try:
        with open(CACHE_FILE, "r") as fp:
            existing_cache = json.load(fp)
        if "__PREVIOUS_FILES__" in existing_cache:
            print("Found previous filenames")
            vanilla_entities, ebl_file, output_path = existing_cache[
                "__PREVIOUS_FILES__"
            ]
            ui.base_entities_box.setPlainText(vanilla_entities)
            ui.ebl_file_box.setPlainText(ebl_file)
            ui.output_file_box.setPlainText(output_path)
    except (json.JSONDecodeError, FileNotFoundError):
        compiler.ui_log(f"{CACHE_FILE} was deleted!")
    ui.base_entities_fileselect.clicked.connect(set_base_entities_fp)
    ui.ebl_fileselect.clicked.connect(set_ebl_fp)
    ui.output_fileselect.clicked.connect(set_output_fp)
    sys.exit(app.exec_())
