#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import traceback
import yaml

import PyQt5
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPalette,QColor

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
# or set env variable: QT_AUTO_SCREEN_SCALE_FACTOR=2 

import pystarquant.common.sqglobal as SQGlobal

from pystarquant.gui.ui_main_window import MainWindow
from signal import signal, SIGINT, SIG_DFL
# print(PyQt5.QtWidgets.QStyleFactory.keys())

# https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
signal(SIGINT, SIG_DFL)


def excepthook(exctype, value, tb):
    """
    Raise exception under debug mode, otherwise 
    show exception detail with QMessageBox.
    """
    sys.__excepthook__(exctype, value, tb)

    msg = "".join(traceback.format_exception(exctype, value, tb))
    QtWidgets.QMessageBox.critical(
        None, "Exception", msg, QtWidgets.QMessageBox.Ok
    )


def main():

    sys.excepthook = excepthook

    qapp = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
  
    if SQGlobal.config_server['theme'] == 'dark':
        import qdarkstyle
        qapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
    # #   for mac retina
        qapp.setStyle("Fusion") 
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QtCore.Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QtCore.Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QtCore.Qt.darkGray)
        dark_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
        qapp.setPalette(dark_palette) 


    # mainWindow.showMaximized()
    # mainWindow.showFullScreen()
    mainWindow.showNormal()
    # mainWindow.resize(2560,1440)
    
    sys.exit(qapp.exec_())




       

if __name__ == "__main__":

    main()
