#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
import json
import os
import traceback
import importlib
from pathlib import Path

from ..common.utility import load_json
from ..common.constant import EventType, MSG_TYPE
from ..common.datastruct import Event
from ..strategy.strategy_base import StrategyBase
CtaTemplate = StrategyBase


class CtaManager(QtWidgets.QWidget):
    """"""

    signal_log = QtCore.pyqtSignal(Event)
    signal_strategy_in = QtCore.pyqtSignal(Event)
    signal_strategy_out = QtCore.pyqtSignal(Event)
    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"

    def __init__(self):
        super().__init__()

        # self.main_engine = main_engine
        # self.event_engine = event_engine
        # self.cta_engine = main_engine.get_engine(APP_NAME)
        self.strategy_setting = {}  # strategy_name: dict
        self.strategy_data = {}     # strategy_name: dict
        self.classes = {}           # class_name: stategy_class
        self.engines = []
        self.strategy_engine_map = {}  # strategy_name -> engine_id map
        self.managers = {}
        self.load_strategy_class()
        self.load_strategy_setting()
        self.load_strategy_data()
        self.init_ui()
        self.register_event()
        # self.cta_engine.init_engine()
        self.update_class_combo()
        self.refresh_strategies()

    def load_strategy_class(self, reload: bool = False):
        """
        Load strategy class from source code.
        """
        # app_path = Path(__file__).parent.parent
        # path1 = app_path.joinpath("cta_strategy", "strategies")
        # self.load_strategy_class_from_folder(
        #     path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("mystrategy")
        self.load_strategy_class_from_folder(path2, "", reload)

    def load_strategy_class_from_folder(self, path: Path, module_name: str = "", reload: bool = False):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = "mystrategy.".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(
                        strategy_module_name, reload)

    def load_strategy_class_from_module(self, module_name: str, reload: bool = False):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)
        # if reload delete old attribute
            if reload:
                for attr in dir(module):
                    if attr not in ('__name__', '__file__'):
                        delattr(module, attr)
                importlib.reload(module)
            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            print(msg)
            # self.write_log(msg)

    def get_all_strategy_class_names(self):
        """
        Return names of strategy classes loaded.
        """
        return list(self.classes.keys())

    def get_strategy_class_parameters(self, class_name: str):
        """
        Get default parameters of a strategy class.
        """
        strategy_class = self.classes[class_name]

        parameters = {}
        for name in strategy_class.parameters:
            parameters[name] = getattr(strategy_class, name)

        return parameters

    def load_strategy_setting(self):
        """
        Load setting file.
        """
        self.strategy_setting = load_json(self.setting_filename)

    def load_strategy_data(self):
        """
        Load strategy data from json file.
        """
        self.strategy_data = load_json(self.data_filename)

    def init_ui(self):
        """"""
        self.setWindowTitle("CTA Strategy")

        # Create widgets
        self.class_combo = QtWidgets.QComboBox()
        self.engine_combo = QtWidgets.QComboBox()

        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_strategy)

        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_strategies)

        init_button = QtWidgets.QPushButton("Init All")
        init_button.clicked.connect(self.init_all_strategies)

        start_button = QtWidgets.QPushButton("Start ALL")
        start_button.clicked.connect(self.start_all_strategies)

        stop_button = QtWidgets.QPushButton("Stop ALL")
        stop_button.clicked.connect(self.stop_all_strategies)

        reset_button = QtWidgets.QPushButton("Reset ALL")
        reset_button.clicked.connect(self.reset_all_strategies)

        self.scroll_layout = QtWidgets.QVBoxLayout()
        self.scroll_layout.addStretch()

        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setLayout(self.scroll_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        # self.log_monitor = LogMonitor(self.main_engine, self.event_engine)

        # self.stop_order_monitor = StopOrderMonitor(
        #     self.main_engine, self.event_engine
        # )

        # Set layout
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(refresh_button)
        hbox1.addWidget(QtWidgets.QLabel('Strategy'))
        hbox1.addWidget(self.class_combo)
        hbox1.addWidget(add_button)
        hbox1.addWidget(QtWidgets.QLabel('Engine PID'))
        hbox1.addWidget(self.engine_combo)
        hbox1.addStretch()
        hbox1.addWidget(init_button)
        hbox1.addWidget(start_button)
        hbox1.addWidget(stop_button)
        hbox1.addWidget(reset_button)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(scroll_area, 0, 0, 2, 1)
        # grid.addWidget(self.stop_order_monitor, 0, 1)
        # grid.addWidget(self.log_monitor, 1, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(grid)

        self.setLayout(vbox)
        self.setMinimumHeight(600)

    def update_class_combo(self):
        """"""
        self.class_combo.addItems(
            self.get_all_strategy_class_names()
        )

    def register_event(self):
        """"""
        self.signal_strategy_in.connect(self.process_strategy_event)

        # self.event_engine.register(
        #     EVENT_CTA_STRATEGY, self.signal_strategy.emit
        # )

    def process_strategy_event(self, event):
        """
        Update strategy status onto its monitor.
        """
        if event.msg_type == MSG_TYPE.MSG_TYPE_STRATEGY_RTN_DATA:
            strmsg = event.data
            data = json.loads(strmsg)
            # print(type(data),data)
            # first remove not active strategy
            # for sname in self.managers.keys():
            #     if sname not in data.keys():
            #         self.remove_strategy(sname)
            # second update data in managers
            for strategy_name, strategy_config in data.items():
                if strategy_name in self.managers:
                    # if this strategy already exist in other engine, remove it
                    if self.strategy_engine_map[strategy_name] != strategy_config["engine_id"]:
                        self.send_remove_strategy_msg(
                            strategy_name, str(strategy_config["engine_id"]), True)
                        continue
                    manager = self.managers[strategy_name]
                    manager.update_data(strategy_config)
                else:
                    manager = StrategyManager(self, strategy_config)
                    self.scroll_layout.insertWidget(0, manager)
                    self.managers[strategy_name] = manager
                    self.strategy_engine_map[strategy_name] = strategy_config["engine_id"]
        elif event.msg_type == MSG_TYPE.MSG_TYPE_STRATEGY_RTN_REMOVE:
            if str(self.strategy_engine_map[event.data]) == event.source:
                self.remove_strategy(event.data)
        elif event.msg_type == MSG_TYPE.MSG_TYPE_STRATEGY_STATUS:
            if (event.source != '0') and (event.source not in self.engines):
                self.engines.append(event.source)
                self.engine_combo.addItem(event.source)

    def refresh_strategies(self):
        # reload all the strategy class
        self.reload_strategies()
        # reload all the managers, delete first, send qry msg, then add manager according to reply
        while self.managers:
            name, manager = self.managers.popitem()
            manager.deleteLater()
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*', src='0',
                  msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_GET_DATA)
        self.signal_strategy_out.emit(m)
        # reload all the engine, delele first , send qry msg, then add according to reply
        self.engine_combo.clear()
        self.engines.clear()
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*',
                  src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STATUS)
        self.signal_strategy_out.emit(m)

    def init_all_strategies(self):
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*', src='0',
                  msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_INIT_ALL)
        self.signal_strategy_out.emit(m)

    def start_all_strategies(self):
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*', src='0',
                  msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_START_ALL)
        self.signal_strategy_out.emit(m)

    def stop_all_strategies(self):
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*', src='0',
                  msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STOP_ALL)
        self.signal_strategy_out.emit(m)

    def reset_all_strategies(self):
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*', src='0',
                  msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RESET_ALL)
        self.signal_strategy_out.emit(m)

    def reload_strategies(self):
        self.class_combo.clear()
        self.classes.clear()
        self.load_strategy_class(True)
        self.update_class_combo()
        m = Event(type=EventType.STRATEGY_CONTROL, des='@*',
                  src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RELOAD)
        self.signal_strategy_out.emit(m)

    def init_strategy(self, strategy_name: str, id: str):
        m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name,
                  des='@' + id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_INIT)
        self.signal_strategy_out.emit(m)

    def start_strategy(self, strategy_name: str, id: str):
        m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name,
                  des='@' + id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_START)
        self.signal_strategy_out.emit(m)

    def stop_strategy(self, strategy_name: str, id: str):
        m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name,
                  des='@' + id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STOP)
        self.signal_strategy_out.emit(m)

    def reset_strategy(self, strategy_name: str, id: str):
        m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name,
                  des='@' + id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RESET)
        self.signal_strategy_out.emit(m)

    def edit_strategy(self, strategy_name: str, setting: dict, id: str):
        msg = strategy_name + '|' + json.dumps(setting)
        m = Event(type=EventType.STRATEGY_CONTROL, data=msg, des='@' +
                  id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_EDIT)
        self.signal_strategy_out.emit(m)

    def send_remove_strategy_msg(self, strategy_name: str, id: str, duplicate: bool = False):
        if duplicate:
            m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name, des='@' +
                      id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE_DUPLICATE)
        else:
            m = Event(type=EventType.STRATEGY_CONTROL, data=strategy_name,
                      des='@' + id, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE)
        self.signal_strategy_out.emit(m)

    def remove_strategy(self, strategy_name):
        """"""
        manager = self.managers.pop(strategy_name)
        self.strategy_engine_map.pop(strategy_name)
        manager.deleteLater()

    def add_strategy(self):
        """"""
        class_name = str(self.class_combo.currentText())
        if not class_name:
            return
        engine_id = str(self.engine_combo.currentText())
        if not engine_id:
            return
        desid = '@' + engine_id
        parameters = self.get_strategy_class_parameters(class_name)
        editor = SettingEditor(parameters, class_name=class_name)
        n = editor.exec_()

        if n == editor.Accepted:
            setting = editor.get_setting()
            full_symbol = setting.pop("full_symbol")
            strategy_name = setting.pop("strategy_name")
            if strategy_name in self.managers.keys():
                QtWidgets.QMessageBox().information(
                    None, 'Error', 'strategy name already exist!', QtWidgets.QMessageBox.Ok)
                return
            strsetting = json.dumps(setting)
            msg = class_name + '|' + strategy_name + '|' + full_symbol + '|' + strsetting
            m = Event(type=EventType.STRATEGY_CONTROL, data=msg,
                      des=desid, src='0', msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_ADD)
            self.signal_strategy_out.emit(m)

    def show(self):
        """"""
        self.showMaximized()


class StrategyManager(QtWidgets.QFrame):
    """
    Manager for a strategy
    """

    def __init__(
        self, cta_manager: CtaManager, data: dict
    ):
        """"""
        super().__init__()

        self.cta_manager = cta_manager
        # self.cta_engine = cta_engine

        self.strategy_name = data["strategy_name"]
        self.engine_id = str(data["engine_id"])
        self._data = data

        self.init_ui()

    def init_ui(self):
        """"""
        self.setMaximumHeight(180)
        self.setFrameShape(self.Box)
        self.setLineWidth(1)

        init_button = QtWidgets.QPushButton("  Init  ")
        init_button.clicked.connect(self.init_strategy)

        start_button = QtWidgets.QPushButton(" Start ")
        start_button.clicked.connect(self.start_strategy)

        stop_button = QtWidgets.QPushButton(" Stop ")
        stop_button.clicked.connect(self.stop_strategy)

        reset_button = QtWidgets.QPushButton(" Reset ")
        reset_button.clicked.connect(self.reset_strategy)

        edit_button = QtWidgets.QPushButton(" Edit ")
        edit_button.clicked.connect(self.edit_strategy)

        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(self.remove_strategy)

        engine_id = self._data["engine_id"]
        strategy_name = self._data["strategy_name"]
        full_symbol = self._data["full_symbol"]
        class_name = self._data["class_name"]
        author = self._data["author"]
        account = self._data["parameters"].get("account", "")
        api = self._data["parameters"].get("api", "")

        label_text = (
            f"{api}|{account}: {strategy_name}@{engine_id}  -  {full_symbol}  ({class_name} by {author})"
        )
        label = QtWidgets.QLabel(label_text)
        label.setAlignment(QtCore.Qt.AlignLeft)

        self.parameters_monitor = DataMonitor(self._data["parameters"])
        self.variables_monitor = DataMonitor(self._data["variables"])

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(label)
        hbox.addStretch()
        hbox.addWidget(init_button)
        hbox.addWidget(start_button)
        hbox.addWidget(stop_button)
        hbox.addWidget(reset_button)
        hbox.addWidget(edit_button)
        hbox.addWidget(remove_button)

        vbox = QtWidgets.QVBoxLayout()
        # vbox.addWidget(label)
        vbox.addLayout(hbox)
        vbox.addWidget(self.parameters_monitor)
        vbox.addWidget(self.variables_monitor)
        self.setLayout(vbox)

    def update_data(self, data: dict):
        """"""
        self._data = data

        self.parameters_monitor.update_data(data["parameters"])
        self.variables_monitor.update_data(data["variables"])

    def init_strategy(self):
        """"""
        self.cta_manager.init_strategy(self.strategy_name, self.engine_id)

    def start_strategy(self):
        """"""
        self.cta_manager.start_strategy(self.strategy_name, self.engine_id)

    def stop_strategy(self):
        """"""
        self.cta_manager.stop_strategy(self.strategy_name, self.engine_id)

    def reset_strategy(self):
        self.cta_manager.reset_strategy(self.strategy_name, self.engine_id)

    def edit_strategy(self):
        """"""
        strategy_name = self._data["strategy_name"]

        parameters = self.parameters_monitor._data
        editor = SettingEditor(parameters, strategy_name=strategy_name)
        n = editor.exec_()

        if n == editor.Accepted:
            setting = editor.get_setting()
            self.cta_manager.edit_strategy(
                strategy_name, setting, self.engine_id)

    def remove_strategy(self):
        """"""
        # result = self.cta_engine.remove_strategy(self.strategy_name)

        # # Only remove strategy gui manager if it has been removed from engine
        # if result:
        #     self.cta_manager.remove_strategy(self.strategy_name)
        mbox = QtWidgets.QMessageBox().question(None, 'confirm', 'are you sure',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
        if mbox == QtWidgets.QMessageBox.Yes:
            self.cta_manager.send_remove_strategy_msg(
                self.strategy_name, self.engine_id)


class DataMonitor(QtWidgets.QTableWidget):
    """
    Table monitor for parameters and variables.
    """

    def __init__(self, data: dict):
        """"""
        super().__init__()

        self._data = data
        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        labels = list(self._data.keys())
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)

        self.setRowCount(1)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)

        for column, name in enumerate(self._data.keys()):
            value = self._data[name]

            cell = QtWidgets.QTableWidgetItem(str(value))
            cell.setTextAlignment(QtCore.Qt.AlignCenter)

            self.setItem(0, column, cell)
            self.cells[name] = cell

    def update_data(self, data: dict):
        """"""
        for name, value in data.items():
            cell = self.cells[name]
            cell.setText(str(value))


class SettingEditor(QtWidgets.QDialog):
    """
    For creating new strategy and editing strategy parameters.
    """

    def __init__(
        self, parameters: dict, strategy_name: str = "", class_name: str = ""
    ):
        """"""
        super().__init__()

        self.parameters = parameters
        self.strategy_name = strategy_name
        self.class_name = class_name

        self.edits = {}

        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add full_symbol and name edit if add new strategy
        if self.class_name:
            self.setWindowTitle(f"添加策略：{self.class_name}")
            button_text = "添加"
            parameters = {"strategy_name": "", "full_symbol": ""}
            parameters.update(self.parameters)
        else:
            self.setWindowTitle(f"参数编辑：{self.strategy_name}")
            button_text = "确定"
            parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)

            edit = QtWidgets.QLineEdit(str(value))
            if type_ is int:
                validator = QtGui.QIntValidator()
                edit.setValidator(validator)
            elif type_ is float:
                validator = QtGui.QDoubleValidator()
                edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)

            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow(button)

        self.setLayout(form)

    def get_setting(self):
        """"""
        setting = {}

        if self.class_name:
            setting["class_name"] = self.class_name

        for name, tp in self.edits.items():
            edit, type_ = tp
            value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            else:
                value = type_(value_text)

            setting[name] = value

        return setting
