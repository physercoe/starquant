#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import traceback
import yaml
from PyQt5 import QtCore, QtWidgets, QtGui
from source.gui.ui_main_window import MainWindow
import atexit
from signal import signal, SIGINT, SIG_DFL
from os import kill
from multiprocessing import Process

import itchat
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

    config_server = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, 'etc/config_server.yaml')
        with open(os.path.expanduser(config_file), encoding='utf8') as fd:
            config_server = yaml.load(fd)
    except IOError:
        print("config_server.yaml is missing")

    config_client = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, 'etc/config_client.yaml')
        with open(os.path.expanduser(config_file), encoding='utf8') as fd:
            config_client = yaml.load(fd)
    except IOError:
        print("config_client.yaml is missing")

    lang_dict = None
    font = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, 'source/gui/language/en/live_text.yaml')
        font = QtGui.QFont('Microsoft Sans Serif', 12)
        if config_client['language'] == 'cn':
            config_file = os.path.join(path, 'source/gui/language/cn/live_text.yaml')
            font = QtGui.QFont(u'微软雅黑', 10)
        with open(os.path.expanduser(config_file), encoding='utf8') as fd:
            lang_dict = yaml.load(fd)
        lang_dict['font'] = font
    except IOError:
        print("live_text.yaml is missing")

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow(config_server, config_client, lang_dict)

    if config_client['theme'] == 'dark':
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    mainWindow.showMaximized()

    sys.exit(app.exec_())




       

if __name__ == "__main__":

    main()
