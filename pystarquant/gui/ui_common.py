"""
common widgets, which is not cpu-consuming
"""

from enum import Enum
import psutil
from PyQt5 import QtCore, QtGui, QtWidgets #, QtWebEngineWidgets
import yaml
from datetime import datetime, date,timedelta
from pathlib import Path
import json
from copy import copy
import webbrowser
from threading import Thread


from pystarquant.common.constant import (
    Exchange, 
    Product, 
    PRODUCT_CTP2VT, 
    OPTIONTYPE_CTP2VT,
    PRODUCT_SQ2VT,
    PRODUCT_VT2SQ    
)
from pystarquant.common.datastruct import  ContractData
from pystarquant.common.utility import (
    load_json, save_json
)
from pystarquant.common.config import SETTING_FILENAME, SETTINGS
from pystarquant.api.ctp_constant import THOST_FTDC_PT_Net
from pystarquant.gui.ui_basic import EnumCell, BaseCell


# class WebWindow(QtWidgets.QWidget):

#     def __init__(self):
#         super().__init__()

#         # member variables
#         self.init_gui()

#     def init_gui(self):
#         # self.setFrameShape(QtWidgets.QFrame.StyledPanel)
#         weblayout = QtWidgets.QFormLayout()

#         self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
#         self.web = QtWebEngineWidgets.QWebEngineView()
#         self.web.setSizePolicy(
#             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
#         # self.web.setMinimumHeight(1000)
#         # self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
#         # self.web.setMinimumWidth(1000)

#         self.web.loadFinished.connect(lambda : self.web.resize(self.size()))
#         self.web.load(QtCore.QUrl("http://localhost:8888"))

#         self.web_addr = QtWidgets.QLineEdit()
#         self.web_btn_jn = QtWidgets.QPushButton('Jupyter Notebook')
#         self.web_btn_jn.clicked.connect(
#             lambda: self.web.load(QtCore.QUrl("http://localhost:8888")))
#         self.web_btn_go = QtWidgets.QPushButton('Go')
#         self.web_btn_go.clicked.connect(
#             lambda: self.web.load(QtCore.QUrl(self.web_addr.text())))

#         webhboxlayout1 = QtWidgets.QHBoxLayout()
#         webhboxlayout1.addWidget(self.web_btn_jn)
#         webhboxlayout1.addWidget(QtWidgets.QLabel('URL'))
#         webhboxlayout1.addWidget(self.web_addr)
#         webhboxlayout1.addWidget(self.web_btn_go)

#         weblayout.addRow(webhboxlayout1)
#         weblayout.addRow(self.web)
#         self.setLayout(weblayout)

class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
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
        "net_position": "是否净持仓",
        "long_margin_ratio": "多仓保证金率",
        "short_margin_ratio": "空仓保证金率"
    }

    def __init__(self):
        super().__init__()

        self.contracts = {}

        self.init_ui()

    def load_contract(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入数据", "", "YAML(*.yaml)")
        if not path:
            return
        with open(path, encoding='utf8') as fc:
            contracts = yaml.load(fc, Loader=yaml.SafeLoader)
        if not contracts:
            return
        try:
            print('loading contracts, total number:', len(contracts))
            for sym, data in contracts.items():
                contract = ContractData(
                    symbol=data["symbol"],
                    exchange=Exchange(data["exchange"]),
                    name=data["name"],
                    product=PRODUCT_CTP2VT[str(data["product"])],
                    size=data["size"],
                    pricetick=data["pricetick"],
                    net_position=True if str(
                        data["positiontype"]) == THOST_FTDC_PT_Net else False,
                    long_margin_ratio=data["long_margin_ratio"],
                    short_margin_ratio=data["short_margin_ratio"],
                    full_symbol=data["full_symbol"]
                )
                # For option only
                if contract.product == Product.OPTION:
                    contract.option_underlying = data["option_underlying"],
                    contract.option_type = OPTIONTYPE_CTP2VT.get(
                        str(data["option_type"]), None),
                    contract.option_strike = data["option_strike"],
                    contract.option_expiry = datetime.strptime(
                        str(data["option_expiry"]), "%Y%m%d"),
                self.contracts[contract.full_symbol] = contract
            QtWidgets.QMessageBox().information(
            None, 'Info', '导入合约完成', QtWidgets.QMessageBox.Ok)


        except Exception as e:
            msg = "Load contracts error: {0}".format(str(e.args[0]))
            QtWidgets.QMessageBox().information(
            None, 'Error', msg, QtWidgets.QMessageBox.Ok)


    def init_ui(self):
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText(
            "输入全称字段（交易所,类别，产品代码，合约编号），留空则查询所有合约")
        self.filter_line.returnPressed.connect(self.show_contracts)
        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)
        self.button_load = QtWidgets.QPushButton("导入")
        self.button_load.clicked.connect(self.load_contract)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)
        hbox.addWidget(self.button_load)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

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
            contracts = self.contracts

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

    def on_contract(self, contract):
        self.contracts[contract.full_symbol] = contract


class StatusThread(QtCore.QThread):
    status_update = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            cpuPercent = psutil.cpu_percent()
            memoryPercent = psutil.virtual_memory().percent
            self.status_update.emit(
                'CPU Usage: ' + str(cpuPercent) + '% Memory Usage: ' + str(memoryPercent) + '%')
            self.sleep(2)

class EmbTerminal(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QtCore.QProcess(self)
        self.terminal = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.terminal)
        # Works also with urxvt:
        self.process.start('urxvt',['-embed', str(int(self.winId()))])

class FileTreeWidget(QtWidgets.QWidget):
    signal_filepath = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # self.left = 10
        # self.top = 10
        # self.width = 640
        # self.height = 480
        self.initUI()
 
    def initUI(self):
        # self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height)
        dir = str(Path.cwd())
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(dir)
        
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(dir))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.doubleClicked.connect(self.show_filepath)
        # self.tree.setWindowTitle("Dir View")
        # self.tree.resize(640, 400)
        windowLayout = QtWidgets.QVBoxLayout()
        windowLayout.addWidget(self.tree)
        self.setLayout(windowLayout)

    def show_filepath(self,qmodelindex):
        fpath = self.model.filePath(qmodelindex)
        self.signal_filepath.emit(fpath)
        
class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("Python进程相关配置")
        self.setMinimumWidth(800)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        settings = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type = type(field_value)
            widget = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("确定")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        self.setLayout(form)

    def update_setting(self):
        """
        Get setting value from line edits and update global setting file.
        """
        settings = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text = widget.text()

            if field_type == bool:
                if value_text == "True":
                    field_value = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()


class TextEditDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self, filename: str):
        """"""
        super().__init__()
        self.filename = filename
        self.setWindowTitle("配置编辑文件")
        self.setMinimumWidth(800)
        self.setMinimumHeight(800)
        self.textedit = QtWidgets.QTextEdit()
        self.textedit.setFont(QtGui.QFont('Microsoft Sans Serif', 12))
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        form = QtWidgets.QVBoxLayout()
        savebutton = QtWidgets.QPushButton("save")
        savebutton.clicked.connect(self.update_file)
        form.addWidget(self.textedit)
        form.addWidget(savebutton)
        self.setLayout(form)
        with open(self.filename, 'r') as f:
            my_txt = f.read()
            self.textedit.setText(my_txt)

    def update_file(self):
        """
        .
        """

        my_text = self.textedit.toPlainText()
        with open(self.filename, 'w+') as f:
            f.write(my_text)
        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )
        self.accept()





from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
}


class PythonHighlighter (QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
























class TextEditWidget(QtWidgets.QWidget):
    """
    Start connection of a certain gateway.
    """

    def __init__(self, filename: str=''):
        """"""
        super().__init__()
        self.filename = filename
        self.textedit = QtWidgets.QTextEdit()
        self.highlight = PythonHighlighter(self.textedit.document())
        self.textedit.setFont(QtGui.QFont('Microsoft Sans Serif', 12))
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        form = QtWidgets.QVBoxLayout()
        savebutton = QtWidgets.QPushButton("save")
        savebutton.clicked.connect(self.update_file)
        form.addWidget(savebutton)
        form.addWidget(self.textedit)

        self.setLayout(form)

    def open_file(self,fpath:str):
        self.filename = fpath
        with open(self.filename, 'r') as f:
            my_txt = f.read()
            self.textedit.setText(my_txt)


    def update_file(self):
        """
        .
        """
        mbox = QtWidgets.QMessageBox().question(None, '确认', '是否覆盖源文件？',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if mbox == QtWidgets.QMessageBox.No:
            return

        if self.filename:
            my_text = self.textedit.toPlainText()
            with open(self.filename, 'w+') as f:
                f.write(my_text)









class AboutWidget(QtWidgets.QDialog):
    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super().__init__(parent)

        self.initUi()
    # ----------------------------------------------------------------------

    def initUi(self):
        """"""
        self.setWindowTitle('About StarQuant')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        text = u"""
            StarQuant(易数交易系统)           
            Integrated Algo-Trade/Backtest System
            Language: C++,Python
            Version: 1.0rc3 
            Build: 20221022
            License：MIT

            Contact: whereilive@gmail.com


            莫道交易如浪深，莫言策略似沙沉。
            千回万测虽辛苦，实盘验后始得金。
     
            """
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(300)

        self.gif = QtGui.QMovie('pystarquant/gui/image/star.gif')
        labelgif = QtWidgets.QLabel()
        labelgif.setMovie(self.gif)
        self.gif.start()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(labelgif)
        vbox.addWidget(label)
        button = QtWidgets.QPushButton("开源版源代码网址")
        button.clicked.connect(self.open_code)
        vbox.addWidget(button)
        self.setLayout(vbox)

    def open_code(self):

        webbrowser.open("https://www.github.com/physercoe/starquant")
