"""
Basic widgets for SQ main window.
"""

import csv
from enum import Enum
from typing import Any

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from ..common.datastruct import Event
from ..engine.iengine import EventEngine
from ..common.constant import Direction

from ..common.constant import EventType, OT2STR




COLOR_LONG = QtGui.QColor("red")
COLOR_SHORT = QtGui.QColor("green")
COLOR_BID = QtGui.QColor(255, 174, 201)
COLOR_ASK = QtGui.QColor(160, 255, 160)
COLOR_BLACK = QtGui.QColor("black")




class VerticalTabBar(QtWidgets.QTabBar):
    # def tabSizeHint(self,index):
    #     s = QtWidgets.QTabBar.tabSizeHint(self,index)
    #     s.transpose()
    #     return s

    def paintEvent(self,event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            # s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(180)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()




class QFloatTableWidgetItem (QtWidgets.QTableWidgetItem):
    def __init__ (self, value):
        super(QFloatTableWidgetItem, self).__init__(value)

    def __lt__ (self, other):
        if (isinstance(other, QFloatTableWidgetItem)):
            selfDataValue  = float(self.text())
            otherDataValue = float(other.text())
            return selfDataValue < otherDataValue
        else:
            return QtWidgets.QTableWidgetItem.__lt__(self, other)





class BaseCell(QtWidgets.QTableWidgetItem):
    """
    General cell used in tablewidgets.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(BaseCell, self).__init__()
        self.setTextAlignment(QtCore.Qt.AlignCenter)
        self.set_content(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Set text content.
        """
        self.setText(str(content))
        self._data = data

    def get_data(self):
        """
        Get data object.
        """
        return self._data


class EnumCell(BaseCell):
    """
    Cell used for showing enum data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(EnumCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Set text using enum.constant.value.
        """
        if content:
            super(EnumCell, self).set_content(content.value, data)

class OTCell(BaseCell):
    """
    Cell used for showing ordertype data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(OTCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Set text using ot2str.
        """
        if content:
            text = OT2STR.get(content,'未知')
            self.setText(text)
            self._data = data


class DirectionCell(EnumCell):
    """
    Cell used for showing direction data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(DirectionCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Cell color is set according to direction.
        """
        super(DirectionCell, self).set_content(content, data)

        if content is Direction.SHORT:
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class BidCell(BaseCell):
    """
    Cell used for showing bid price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(BidCell, self).__init__(content, data)

        self.setForeground(COLOR_BLACK)
        self.setForeground(COLOR_BID)


class AskCell(BaseCell):
    """
    Cell used for showing ask price and volume.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(AskCell, self).__init__(content, data)

        self.setForeground(COLOR_BLACK)
        self.setForeground(COLOR_ASK)


class PnlCell(BaseCell):
    """
    Cell used for showing pnl data.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(PnlCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Cell color is set based on whether pnl is 
        positive or negative.
        """
        super(PnlCell, self).set_content(content, data)

        if str(content).startswith("-"):
            self.setForeground(COLOR_SHORT)
        else:
            self.setForeground(COLOR_LONG)


class TimeCell(BaseCell):
    """
    Cell used for showing time string from datetime object.
    """

    def __init__(self, content: Any, data: Any):
        """"""
        super(TimeCell, self).__init__(content, data)

    def set_content(self, content: Any, data: Any):
        """
        Time format is 12:12:12.5
        """
        timestamp = content.strftime("%H:%M:%S")

        millisecond = int(content.microsecond / 1000)
        if millisecond:
            timestamp = f"{timestamp}.{millisecond}"

        self.setText(timestamp)
        self._data = data


class MsgCell(BaseCell):
    """
    Cell used for showing msg data.
    """

    def __init__(self, content: str, data: Any):
        """"""
        super(MsgCell, self).__init__(content, data)
        self.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)


class BaseMonitor(QtWidgets.QTableWidget):
    """
    Monitor data update in VN Trader.
    """

    event_type : EventType = EventType.HEADER
    data_key = ""
    sorting = False
    headers = {}

    signal = QtCore.pyqtSignal(Event)

    def __init__(self, event_engine: EventEngine):
        """"""
        super(BaseMonitor, self).__init__()

 
        self.event_engine = event_engine
        self.cells = {}

        self.init_ui()
        self.register_event()

    def init_ui(self):
        """"""
        self.init_table()
        self.init_menu()

    def init_table(self):
        """
        Initialize table.
        """
        self.setColumnCount(len(self.headers))

        labels = [d["display"] for d in self.headers.values()]
        self.setHorizontalHeaderLabels(labels)

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(self.sorting)

    def init_menu(self):
        """
        Create right click menu.
        """
        self.menu = QtWidgets.QMenu(self)

        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.menu.addAction(resize_action)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

        del_action = QtWidgets.QAction("删除数据", self)
        del_action.triggered.connect(self.deleterows)           
        self.menu.addAction(del_action)

    def register_event(self):
        """
        Register event handler into event engine.
        """
        self.signal.connect(self.process_event)
        self.event_engine.register(self.event_type, self.signal.emit)

    def process_event(self, event):
        """
        Process new data from event and update into table.
        """
        # Disable sorting to prevent unwanted error.
        if self.sorting:
            self.setSortingEnabled(False)

        # Update data into table.
        data = event.data

        if not self.data_key:
            self.insert_new_row(data)
        else:
            key = data.__getattribute__(self.data_key)

            if key in self.cells:
                self.update_old_row(data)
            else:
                self.insert_new_row(data)

        # Enable sorting
        if self.sorting:
            self.setSortingEnabled(True)

    def insert_new_row(self, data):
        """
        Insert a new row at the top of table.
        """
        self.insertRow(0)

        row_cells = {}
        for column, header in enumerate(self.headers.keys()):
            setting = self.headers[header]

            content = data.__getattribute__(header)
            cell = setting["cell"](content, data)
            self.setItem(0, column, cell)

            if setting["update"]:
                row_cells[header] = cell

        if self.data_key:
            key = data.__getattribute__(self.data_key)
            self.cells[key] = row_cells

    def update_old_row(self, data):
        """
        Update an old row in table.
        """
        key = data.__getattribute__(self.data_key)
        row_cells = self.cells[key]

        for header, cell in row_cells.items():
            content = data.__getattribute__(header)
            cell.set_content(content, data)

    def resize_columns(self):
        """
        Resize all columns according to contents.
        """
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def save_csv(self):
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")

        if not path:
            return

        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")

            writer.writerow(self.headers.keys())

            for row in range(self.rowCount()):
                row_data = []
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)

    def deleterows(self):
        rr = QtWidgets.QMessageBox.warning(self, "注意", "删除无法恢复！",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
            QtWidgets.QMessageBox.No)
        if rr == QtWidgets.QMessageBox.Yes:
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
                cell = self.item(i,0)
                data = cell.get_data()
                key = data.__getattribute__(self.data_key)
                self.removeRow(i)
                del self.cells[key]        
    
    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())





class CandlestickItem(pg.GraphicsObject):
    w = 0.35
    bull_pen = pg.mkPen('r')
    bear_pen = pg.mkPen('g')
    bull_brush = pg.mkBrush('r') #pg.mkBrush('#00cc00')
    bear_brush = pg.mkBrush('g')#   pg.mkBrush('#fa0000')

    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data        
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()        
        p = QtGui.QPainter(self.picture)
        for t, bar in enumerate(self.data):
            # t = 60*(bar.datetime.hour - 9) + bar.datetime.minute
            if bar.open_price < bar.close_price:
                p.setPen(self.bull_pen)
                p.setBrush(self.bull_brush)
            else:
                p.setPen(self.bear_pen)
                p.setBrush(self.bear_brush)
            p.drawLine(QtCore.QPointF(t, bar.low_price), QtCore.QPointF(t, bar.high_price))
            p.drawRect(QtCore.QRectF(t - self.w, bar.open_price, self.w * 2, bar.close_price - bar.open_price))
        p.end()
        self.update()


    def on_bar(self,bar):
        # self.data.append(bar)
        self.generatePicture()
        # p = self.p
        # t = 60*(bar.datetime.hour - 9) + bar.datetime.minute
        # if bar.open_price < bar.close_price:
        #     p.setPen(self.bull_pen)
        #     p.setBrush(self.bull_brush)
        # else:
        #     p.setPen(self.bear_pen)
        #     p.setBrush(self.bear_brush)
        # p.drawLine(QtCore.QPointF(t, bar.low_price), QtCore.QPointF(t, bar.high_price))
        # p.drawRect(QtCore.QRectF(t - self.w, bar.open_price, self.w * 2, bar.close_price - bar.open_price))
        # p.end()
        # self.update()       

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class VolumeItem(pg.GraphicsObject):
    w = 0.35
    bull_pen = pg.mkPen('r')
    bear_pen = pg.mkPen('g')
    bull_brush = pg.mkBrush('r') #pg.mkBrush('#00cc00')
    bear_brush = pg.mkBrush('g')#   pg.mkBrush('#fa0000')

    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        for t, bar in enumerate(self.data):
            # t = 60*(bar.datetime.hour - 9) + bar.datetime.minute
            sign = 1
            if bar.open_price < bar.close_price:
                p.setPen(self.bull_pen)
                p.setBrush(self.bull_brush)
            else:
                p.setPen(self.bear_pen)
                p.setBrush(self.bear_brush) 
                sign = -1           
            p.drawRect(QtCore.QRectF(t - self.w, 0, self.w * 2, sign*bar.volume))
        p.end()
        self.update()

    def on_bar(self,bar):
        # self.data.append(bar)
        self.generatePicture()    

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())