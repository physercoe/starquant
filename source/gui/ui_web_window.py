#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
import sys
import os
import webbrowser



from queue import Queue, Empty
from PyQt5 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets
from datetime import datetime

sys.path.insert(0,"../..")


from source.common import sqglobal

class WebWindow(QtWidgets.QFrame):


    def __init__(self):
        super(WebWindow, self).__init__()

        ## member variables
        self.init_gui()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel) 
        weblayout = QtWidgets.QFormLayout()

        self.web =  QtWebEngineWidgets.QWebEngineView()
        self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.web.setMinimumHeight(1000)
        # self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        # self.web.setMinimumWidth(1000)
        self.web.load(QtCore.QUrl("http://localhost:8888"))

        self.web_addr = QtWidgets.QLineEdit()
        self.web_btn_jn = QtWidgets.QPushButton('Jupyter Notebook') 
        self.web_btn_jn.clicked.connect(lambda:self.web.load(QtCore.QUrl("http://localhost:8888")))
        self.web_btn_go = QtWidgets.QPushButton('Go') 
        self.web_btn_go.clicked.connect(lambda:self.web.load(QtCore.QUrl(self.web_addr.text())))
        
        webhboxlayout1 = QtWidgets.QHBoxLayout()
        webhboxlayout1.addWidget(self.web_btn_jn)
        webhboxlayout1.addWidget(QtWidgets.QLabel('Web'))
        webhboxlayout1.addWidget(self.web_addr)
        webhboxlayout1.addWidget(self.web_btn_go)

        weblayout.addRow(webhboxlayout1)
        weblayout.addRow(self.web)
        self.setLayout(weblayout)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    ui = WebWindow()
    ui.show()
    app.exec_()