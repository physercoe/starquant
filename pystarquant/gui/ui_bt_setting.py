#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
import sys
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui, Qt

import csv
from datetime import datetime

from collections import defaultdict


from pystarquant.common.constant import (
    CPU_NUMS,
    Interval,
    EventType,
    Direction,
    Offset,
    Product,
    Exchange, 
    PRODUCT_CTP2VT, 
    OPTIONTYPE_CTP2VT,
    PRODUCT_SQ2VT,
    PRODUCT_VT2SQ
)
from pystarquant.common.datastruct import Event,BacktestTradeData,ContractData
from pystarquant.engine.iengine import EventEngine
from pystarquant.engine.backtest_engine import BacktestingEngine, BacktestingProEngine, OptimizationSetting
from pystarquant.strategy.strategy_base import StrategyBase,IndicatorBase,FactorBase,ModelBase
from pystarquant.gui.ui_basic import VerticalTabBar,SettingEditorWidget,QHLine,QVLine,EnumCell, BaseCell
import pystarquant.common.sqglobal as SQGlobal
from pystarquant.data import database_manager


CtaTemplate = StrategyBase

sys.path.insert(0, "../..")

class BacktestingSettingEditorWidget(QtWidgets.QWidget):
    """
    For creating new strategy and editing strategy parameters.
    """

    def __init__(
        self, class_name: str = '', parameters: dict = {}
    ):
        """"""
        super().__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.file_name = ''
        self.mode = 'new'  # new, append, compare

        self.init_ui()
        self.savesetting = False

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()


        self.startbutton = QtWidgets.QPushButton("开始回测")
        self.savebtn = QtWidgets.QPushButton('保存设置')
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.startbutton)
        hbox1.addWidget(self.savebtn)

        file_button = QtWidgets.QPushButton("选择文件")
        file_button.clicked.connect(self.select_file)
        file_button.setToolTip('读取已有回测结果')
        self.file_edit = QtWidgets.QLineEdit()
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItem('new')
        self.mode_combo.addItem('append')
        # self.mode_combo.addItem('compare')
        # btsetbtn = QtWidgets.QPushButton('相关合约参数请在pro模式下设置')        
        # btsetbtn.setEnabled(False)

        self.load_button = QtWidgets.QPushButton("加载结果")
        # self.load_button.clicked.connect(self.load_setting)
        self.load_button.setToolTip('相关合约参数请在pro模式下设置')

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(file_button)
        hbox2.addWidget(self.file_edit)
        hbox2.addWidget(self.mode_combo)
        hbox2.addWidget(self.load_button)

        form.addRow(hbox1)
        form.addRow(hbox2)

        self.parawidget = SettingEditorWidget()
        form.addWidget(self.parawidget)

        self.setLayout(form)

    def set_paras(self,class_name: str,parameters:dict):
        self.parawidget.set_paras(class_name,parameters)

    
    def save_setting(self):
        self.savesetting = True


    def get_setting(self):

        """"""

        return self.parawidget.get_setting()


    def load_setting(self):
        self.mode = self.mode_combo.currentText()
        self.file_name = self.file_edit.text()


    def select_file(self):
        """"""
        result: str = QtWidgets.QFileDialog.getOpenFileName(
            self, filter="CSV (*.csv);;CSV GZ(*.csv.gz)")
        filename = result[0]
        if filename:
            self.file_edit.setText(filename)


class OptimizationSettingEditorWidget(QtWidgets.QWidget):
    """
    For setting up parameters for optimization.
    """

    opt_mode = QtCore.pyqtSignal(str)

    DISPLAY_NAME_MAP = {
        "总收益率": "total_return",
        "夏普比率": "sharpe_ratio",
        "收益回撤比": "return_drawdown_ratio",
        "成交额收益率":"return_turnover",

    }

    def __init__(
        self, class_name: str='', parameters: dict={}
    ):
        """"""
        super().__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.optimization_setting = None
        self.use_ga = False
        self.use_roll = False

        self.init_ui()

    def init_ui(self):
        """"""

        QLabel = QtWidgets.QLabel        
        grid = QtWidgets.QGridLayout()

        self.parallel_button = QtWidgets.QPushButton("网格寻优")
        self.parallel_button.clicked.connect(self.generate_parallel_setting)
        self.roll_button = QtWidgets.QPushButton("滚动优化")
        self.roll_button.clicked.connect(self.generate_roll_setting)
        self.ga_button = QtWidgets.QPushButton("遗传寻优")
        self.ga_button.clicked.connect(self.generate_ga_setting)
        grid.addWidget(self.parallel_button, 0, 0, 1, 2)
        grid.addWidget(self.roll_button, 0, 2, 1, 1)
        grid.addWidget(self.ga_button, 0, 3, 1, 1)

        self.parellelnums = QtWidgets.QSpinBox()
        self.parellelnums.setSingleStep(1)
        self.parellelnums.setRange(1, CPU_NUMS)
        self.parellelnums.setValue(CPU_NUMS)
        grid.addWidget(QtWidgets.QLabel('进程数'), 1, 0, 1, 1)
        grid.addWidget(self.parellelnums,1, 1, 1, 1)

        self.rollperiods = QtWidgets.QSpinBox()
        self.rollperiods.setSingleStep(1)
        self.rollperiods.setRange(1, 365)
        self.rollperiods.setValue(7)
        grid.addWidget(QtWidgets.QLabel('滚动周期/天'), 1, 2, 1, 1)
        grid.addWidget(self.rollperiods,1, 3, 1, 1)


        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItems(list(self.DISPLAY_NAME_MAP.keys()))


        grid.addWidget(QLabel("目标"), 2, 0)
        grid.addWidget(self.target_combo, 2, 1, 1, 3)
        grid.addWidget(QLabel("参数"), 3, 0)
        grid.addWidget(QLabel("开始"), 3, 1)
        grid.addWidget(QLabel("步进"), 3, 2)
        grid.addWidget(QLabel("结束"), 3, 3)

        # # Add vt_symbol and name edit if add new strategy
        # self.setWindowTitle(f"参数寻优配置：{self.class_name}")


        self.parawidget = QtWidgets.QWidget()
        self.parawidget.setLayout(QtWidgets.QFormLayout())

        form = QtWidgets.QFormLayout()
        form.addRow(grid)
        form.addWidget(self.parawidget)

        self.setLayout(form)        

    def set_paras(self,class_name: str, parameters: dict):
        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.optimization_setting = None
        self.use_ga = False
        self.use_roll = False        
        validator = QtGui.QDoubleValidator()

        QtWidgets.QWidget().setLayout(self.parawidget.layout())
        grid = QtWidgets.QGridLayout(self.parawidget)
        row = 0

        QLabel = QtWidgets.QLabel 
        for name, value in self.parameters.items():
            type_ = type(value)
            if type_ not in [int, float]:
                continue

            start_edit = QtWidgets.QLineEdit(str(value))
            step_edit = QtWidgets.QLineEdit(str(1))
            end_edit = QtWidgets.QLineEdit(str(value))

            for edit in [start_edit, step_edit, end_edit]:
                edit.setValidator(validator)

            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(start_edit, row, 1)
            grid.addWidget(step_edit, row, 2)
            grid.addWidget(end_edit, row, 3)

            self.edits[name] = {
                "type": type_,
                "start": start_edit,
                "step": step_edit,
                "end": end_edit
            }

            row += 1

    def generate_ga_setting(self):
        """"""
        self.use_ga = True
        self.generate_setting()
        self.opt_mode.emit('ga')

    def generate_parallel_setting(self):
        """"""
        self.use_ga = False
        self.generate_setting()
        self.opt_mode.emit('grid')

    def generate_roll_setting(self):
        self.use_ga = False
        self.use_roll = True
        self.generate_setting()
        self.opt_mode.emit('roll')

    def generate_setting(self):
        """"""
        self.optimization_setting = OptimizationSetting()

        self.target_display = self.target_combo.currentText()
        target_name = self.DISPLAY_NAME_MAP[self.target_display]
        self.optimization_setting.set_target(target_name)

        num_cpus = self.parellelnums.value()
        self.optimization_setting.set_num_cpus(num_cpus)

        rollperiod = self.rollperiods.value()
        self.optimization_setting.set_roll_period(rollperiod)
        self.optimization_setting.set_use_roll(self.use_roll)

        for name, d in self.edits.items():
            type_ = d["type"]
            start_value = type_(d["start"].text())
            step_value = type_(d["step"].text())
            end_value = type_(d["end"].text())

            if start_value == end_value:
                self.optimization_setting.add_parameter(name, start_value)
            else:
                self.optimization_setting.add_parameter(
                    name,
                    start_value,
                    end_value,
                    step_value
                )


    def get_setting(self):
        """"""
        return self.optimization_setting, self.use_ga



class BacktestingDataViewSettingEditorWidget(QtWidgets.QWidget):
    """
    for data view setting
    """
    sig_indicator = QtCore.pyqtSignal(IndicatorBase)
    sig_reload_indicator = QtCore.pyqtSignal(bool)
    def __init__(self):
        """"""
        super().__init__()
        self.num_combos = 1
        self.edits = []

        self.indicator_classes = {}    # name->indictor
        self.indicator = None
        self.settings = {}

        self.init_ui()

        self.load_indicator()

    def change_indicator_setting(self,cn):
        cs = self.settings.get(cn,{})
        self.iswidget.set_paras(cn,cs)
    
    def get_setting(self):
        """"""
        setting = []
        op = self.opcombo.currentText()
        if len(self.edits) < 2:
            symbol = self.symbol_line.text()
            weight = 0
            setting.append((symbol, weight))
        else:
            for name, num in self.edits:
                symbol = name.text()
                weight = int(num.text())
                setting.append((symbol, weight))
        return setting, op


    def set_combo(self,num):
        self.num_combos = int(num)
        self.edits = []
        QtWidgets.QWidget().setLayout(self.comsetting.layout())
        form = QtWidgets.QFormLayout(self.comsetting)
        if self.num_combos  < 2:
            return
            
        for i in range(self.num_combos):

            symbol = QtWidgets.QLineEdit()
            symbol.setToolTip(f'组合中第{i+1}个合约全称')
            symbol.setFixedWidth(250)
            weight = QtWidgets.QLineEdit('0')
            weight.setFixedWidth(50)
            weight.setToolTip(f'第{i+1}个合约权重')
            validator = QtGui.QIntValidator()
            weight.setValidator(validator)

            form.addRow(symbol, weight)

            self.edits.append((symbol, weight))


    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        self.showdatabtn = QtWidgets.QPushButton("显示行情")

        
        self.symbol_line = QtWidgets.QLineEdit("SHFE F RB 88")



        self.num_combination = QtWidgets.QSpinBox()

        self.num_combination.setToolTip('标的数目')
        self.num_combination.setSingleStep(1)
        self.num_combination.setRange(1, 4)
        self.num_combination.setValue(1)
        self.num_combination.valueChanged.connect(self.set_combo)

        self.opcombo = QtWidgets.QComboBox()
        self.opcombo.addItems(['+','*'])       



        self.data_source = QtWidgets.QComboBox()
        self.data_source.addItems(['DataBase','Memory'])
        self.dbusingcursor = QtWidgets.QCheckBox()
        self.dbusingcursor.setChecked(True)
        self.dbusingcursor.setToolTip("数据库是否采用游标回放数据")

 
        self.db_collection_edit = QtWidgets.QLineEdit('db_bar_data') # 表名
        self.db_type_combo = QtWidgets.QComboBox()    # 字段类型
        self.db_type_combo.addItems(['Bar','Tick','TbtBar'])
        self.db_interval_combo =  QtWidgets.QComboBox()  #字段参数
        for interval in Interval:
            self.db_interval_combo.addItem(interval.value)

        self.start_date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.end_date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')

        self.comsetting = QtWidgets.QWidget()
        self.comsetting.setLayout(QtWidgets.QFormLayout())



        self.indicator_combo = QtWidgets.QComboBox()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))
        self.indicator_combo.currentTextChanged.connect(self.change_indicator_setting)
        showindicator_button = QtWidgets.QPushButton("显示指标")
        showindicator_button.clicked.connect(self.show_indicator)
        refresh_button = QtWidgets.QPushButton("重新加载")
        refresh_button.clicked.connect(lambda:self.load_indicator(True))
        self.iswidget = SettingEditorWidget()


        hbox0 = QtWidgets.QHBoxLayout()
        hbox0.addWidget(self.showdatabtn)
        hbox0.addWidget(showindicator_button)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(QtWidgets.QLabel('标的全称'))
        hbox1.addWidget(self.symbol_line)


        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(QtWidgets.QLabel('开始'))
        hbox3.addWidget(self.start_date_edit)
        hbox3.addWidget(QtWidgets.QLabel('结束'))
        hbox3.addWidget(self.end_date_edit)


        hbox11 = QtWidgets.QHBoxLayout()
        hbox11.addWidget(QtWidgets.QLabel('数据来源'))
        hbox11.addWidget(self.data_source)
        hbox11.addWidget(QtWidgets.QLabel('游标'))
        hbox11.addWidget(self.dbusingcursor)


        hbox12 = QtWidgets.QHBoxLayout()
        hbox12.addWidget(QtWidgets.QLabel('DB表名') )
        hbox12.addWidget(self.db_collection_edit)


        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(QtWidgets.QLabel('字段类型'))
        hbox2.addWidget(self.db_type_combo)
        hbox2.addWidget(QtWidgets.QLabel('时间尺度'))
        hbox2.addWidget(self.db_interval_combo)


        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(QtWidgets.QLabel('组合数目'))
        hbox4.addWidget(self.num_combination)
        hbox4.addWidget(QtWidgets.QLabel('运算符'))
        hbox4.addWidget(self.opcombo)

        hbox5 = QtWidgets.QHBoxLayout()
        hbox5.addWidget(QtWidgets.QLabel('指标名称'))        
        hbox5.addWidget(self.indicator_combo)
        hbox5.addWidget(refresh_button)


        form.addRow(hbox0)
        form.addRow(hbox1)
        form.addRow(hbox3)
        form.addRow(hbox11)
        form.addRow(hbox12)
        form.addRow(hbox2)
        form.addRow(hbox4)
        form.addWidget(self.comsetting)
        form.addRow(hbox5)

        form.addWidget(self.iswidget)



        self.setLayout(form)

    def show_indicator(self):

        class_name = self.indicator_combo.currentText()
        old_setting = self.settings[class_name]
        new_setting = None
        if old_setting:
            new_setting = self.iswidget.get_setting()
            self.settings[class_name] = new_setting

        indicator_class = self.indicator_classes.get(class_name, None)
        if indicator_class:
            myindicator = indicator_class()
            if new_setting:
                myindicator.update_setting(new_setting)
            self.sig_indicator.emit(myindicator)



    def load_indicator(self, reload: bool = False):
        if reload:
            SQGlobal.indicatorloader.load_class(True)
            self.sig_reload_indicator.emit(True)

        self.indicator_classes =  SQGlobal.indicatorloader.classes
        self.settings = SQGlobal.indicatorloader.settings

        self.indicator_combo.clear()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))


class BatchSettingTable(QtWidgets.QTableWidget):
    cols = np.array(
        [
            ('策略名称', 'strategy'),
            ('策略参数', 'parameter'),
            ('合约全称', 'full_symbol'),
            ('时间尺度', 'interval'),
            ('起始日期', 'start'),
            ('结束日期', 'end'),
            ('保证金率','margin'),
            ('手续费率','rate'),
            ('交易滑点','slippage'),
            ('合约乘数','size'),
            ('价格跳动','pricetick')
        ]
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("批量回测设置")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setSortingEnabled(True)
        self.setColumnCount(len(self.cols))
        self.setHorizontalHeaderLabels(self.cols[:, 0])
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.init_menu()
        self.setMinimumHeight(450)
        self.setMinimumWidth(900)
        self.setEditTriggers(self.DoubleClicked)
        self.setToolTip('pro模式下合约参数在合约列表中设定，这里的合约参数无效')

    def init_menu(self):
        self.menu = QtWidgets.QMenu(self)
        insert_action = QtWidgets.QAction("增加一行",self)
        insert_action.triggered.connect(lambda:self.insertRow(0))
        self.menu.addAction(insert_action)
        delete_action = QtWidgets.QAction("删除选定行", self)
        delete_action.triggered.connect(self.deleterows)
        self.menu.addAction(delete_action)
        clear_action = QtWidgets.QAction("清空", self)
        clear_action.triggered.connect(self.cleardata)        
        self.menu.addAction(clear_action)
        import_action = QtWidgets.QAction("导入", self)
        import_action.triggered.connect(self.importdata)
        self.menu.addAction(import_action)
        export_action  = QtWidgets.QAction("导出",self)
        export_action.triggered.connect(self.exportdata)
        self.menu.addAction(export_action)
        

    def cleardata(self):
        self.setRowCount(0)

    def exportdata(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")
        if not path:
            return
        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            # writer.writerow(self.headers.keys())

            for row in range(self.rowCount()):
                row_data = []
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)

    def importdata(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入数据", "", "CSV(*.csv)")
        if not path:
            return
        self.setSortingEnabled(False)

        with open(path, "r") as f:
            reader = csv.reader(f, lineterminator="\n")
            for line in reader:
                self.insertRow(0)
                for icol, col in enumerate(self.cols[:, 1]):
                    item = QtWidgets.QTableWidgetItem(line[icol])
                    align = QtCore.Qt.AlignVCenter
                    item.setTextAlignment(align)
                    self.setItem(0, icol, item)

        self.sortItems(1, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)

    def deleterows(self):
        """
        delete 
        """
        curow = self.currentRow()
        selections = self.selectionModel()
        selectedsList = selections.selectedRows()
        rows = []
        for r in selectedsList:
            rows.append(r.row())
        if len(rows) == 0 and curow >= 0:
            rows.append(curow)
        rows.reverse()
        for i in rows:
            self.removeRow(i)

    def show_data(self, item):
        row = item.row()
        pass

    def add_data(self, set: dict):
        if not set:
            return
        self.setSortingEnabled(False)
        self.insertRow(0)
        for icol, col in enumerate(self.cols[:, 1]):
            if col == 'start' or col == 'end':
                val = set[col].strftime('%Y-%m-%d')
            else:
                val = str(set[col])
            item = QtWidgets.QTableWidgetItem(val)
            align = QtCore.Qt.AlignVCenter
            item.setTextAlignment(align)
            self.setItem(0, icol, item)
        self.setSortingEnabled(True)
        self.sortItems(3, QtCore.Qt.AscendingOrder)

    def get_data(self):
        settinglist = defaultdict(list)
        self.setSortingEnabled(False)
        for row in range(self.rowCount()):
            for icol, col in enumerate(self.cols[:, 1]):
                item = self.item(row, icol)
                if item:
                    if col == 'start' or col == 'end':
                        timestr = str(item.text())
                        dt = datetime.strptime(timestr, "%Y-%m-%d")
                        settinglist[col].append(dt.date())
                    else:
                        settinglist[col].append(str(item.text()))
        self.setSortingEnabled(True)
        return settinglist

    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())


class BtContractManager(QtWidgets.QWidget):
    """
    Query/edit contract data available to bactest in system.
    """

    headers = {
        "full_symbol": "全称",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "rate": "手续费率",
        "slippage": "交易滑点",
        "net_position": "是否净持仓",
    }

    def __init__(self):
        super().__init__()

        self.contracts = {}
        # self.load_contract()

        self.init_ui()
        self.init_menu()


    def init_menu(self):

        self.menu = QtWidgets.QMenu(self)
        insert_action = QtWidgets.QAction("增加合约",self)
        insert_action.triggered.connect(self.add_contract)
        self.menu.addAction(insert_action)

    def init_ui(self):
        """"""
        self.setWindowTitle("回测合约参数设置")
        self.resize(1000, 600)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText(
            "输入全称字段（交易所,类别，产品代码，合约编号），留空则查询所有合约")
        self.filter_line.returnPressed.connect(self.show_contracts)
        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)
        self.button_import = QtWidgets.QPushButton("导入")
        self.button_import.clicked.connect(self.importdata)
        self.button_export = QtWidgets.QPushButton("导出")
        self.button_export.clicked.connect(self.exportdata)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.DoubleClicked)
        self.contract_table.setAlternatingRowColors(True)
        self.contract_table.itemChanged.connect(self.edit_contract)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)
        hbox.addWidget(self.button_import)
        hbox.addWidget(self.button_export)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def add_contract(self):
        dialog = ContractSettingEditor()
        i = dialog.exec()
        if i != dialog.Accepted:
            return
        contract = dialog.get_contract()
        self.contracts[contract.full_symbol] = contract

        self.contract_table.insertRow(0)
        for column, name in enumerate(self.headers.keys()):
            value = getattr(contract, name)
            if isinstance(value, Enum):
                cell = EnumCell(value, contract)
            else:
                cell = BaseCell(value, contract)
            self.contract_table.setItem(0, column, cell)



    def show_contracts(self):
        """
        Show contracts by symbol
        """
        flt = str(self.filter_line.text()).upper()

        if flt:
            contracts = [
                contract for contract in self.contracts.values() if flt in contract.full_symbol
            ]
        else:
            contracts = list(self.contracts.values())

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()

    def edit_contract(self, item):
        itemcontract = item.get_data()
        field = list(self.headers.keys())[item.column()]
        data = getattr(itemcontract,field)
        if type(data) == int:
            setattr(self.contracts[itemcontract.full_symbol], field, int(item.text()))
        elif type(data) == float:
            setattr(self.contracts[itemcontract.full_symbol], field, float(item.text()))

    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())


    def exportdata(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")
        if not path:
            return
        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(self.headers.keys())

            for contract in self.contracts.values():
                row_data = []
                for name in self.headers.keys():                
                    attri = getattr(contract, name)
                    if isinstance(attri, Product):
                        data = PRODUCT_VT2SQ[attri]
                    elif isinstance(attri, Exchange):
                        data = attri.value
                    elif isinstance(attri,bool):
                        data = int(attri)
                    else:
                        data = str(attri)
                    row_data.append(data)
                writer.writerow(row_data)

    def importdata(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入数据", "", "CSV(*.csv)")
        if not path:
            return
        with open(path, "r") as f:
            reader = csv.DictReader(f, lineterminator="\n")
            try:
                for item in reader:
                    contract = ContractData(
                        symbol=str(item["symbol"]),
                        exchange=Exchange(item["exchange"]),
                        name=str(item["name"]),
                        product=PRODUCT_SQ2VT[str(item["product"])],
                        size=float(item["size"]),
                        pricetick=float(item["pricetick"]),
                        min_volume=float(item["min_volume"]),
                        net_position=bool(int(item["net_position"])),
                        full_symbol=str(item["full_symbol"]),
                        slippage=float(item["slippage"]), 
                        rate=float(item["rate"])                 
                    )
                    self.contracts[contract.full_symbol] = contract
            except Exception as e:
                msg = "Load btcontracts error: {0}".format(str(e.args[0]))
                QtWidgets.QMessageBox().information(
                None, 'Error', msg, QtWidgets.QMessageBox.Ok)

class ContractSettingEditor(QtWidgets.QDialog):
    """
    For creating new contract and editing strategy parameters.
    """
    headers = {
        "full_symbol": "全称",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "rate": "手续费率",
        "isratio":"是否按金额",
        "slippage": "交易滑点",
        "net_position": "是否净持仓",
    }
    def __init__(self):
        """"""
        super().__init__()

        self.contract = ContractData(
                symbol='XX99',
                exchange=Exchange.SHFE,
                name='未知',
                product=Product.FUTURES,
                size=1,
                pricetick=1.0,
                min_volume=1,
                net_position=False,
                full_symbol='SHFE F XX 99',
                slippage=0.0, 
                rate=0.0001                 
            )
        self.edits = {}
        self.init_ui()


    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle("合约设置")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        for name in self.headers.keys():
            value = getattr(self.contract, name)
            type_ = type(value)
            if isinstance(value,Enum):
                edit = QtWidgets.QComboBox()
                enumlist = list(type_.__members__.values())
                enumstrlist = [a.value for a in enumlist]
                edit.addItems(enumstrlist)
            else:
                edit = QtWidgets.QLineEdit(str(value))
                if type_ is int:
                    validator = QtGui.QIntValidator()
                    edit.setValidator(validator)
                elif type_ is float:
                    validator = QtGui.QDoubleValidator()
                    edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)
            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton('确定')
        button.clicked.connect(self.accept)
        form.addRow(button)

        self.setLayout(form)
    

    def get_contract(self):
        """"""
        for name, tp in self.edits.items():
            edit, type_ = tp
            if issubclass(type_, Enum):
                value_text = edit.currentText()
            else:
                value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            else:
                value = type_(value_text)
            setattr(self.contract, name, value)

        return self.contract