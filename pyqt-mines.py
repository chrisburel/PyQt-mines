import sip
sip.setapi('QVariant', 2)
from PyQt4 import QtCore, QtGui
import random

class MinesweeperItem(object):
    def __init__(self, row, column):
        self.row = row
        self.column = column
        self._isBomb = False
        self._bombNeighborCount = 0
        self._isRevealed = False

    @property
    def bombNeighborCount(self):
        return self._bombNeighborCount

    @bombNeighborCount.setter
    def bombNeighborCount(self, newCount):
        self._bombNeighborCount = newCount

    @property
    def isBomb(self):
        return self._isBomb

    @isBomb.setter
    def isBomb(self, newVal):
        self._isBomb = newVal

    @property
    def isRevealed(self):
        return self._isRevealed

    @isRevealed.setter
    def isRevealed(self, newVal):
        self._isRevealed = newVal

class MinesweeperModel(QtCore.QAbstractItemModel):
    BombNeighborRole = QtCore.Qt.UserRole
    IsBombRole = QtCore.Qt.UserRole + 1
    IsRevealedRole = QtCore.Qt.UserRole + 2

    def __init__(self, rowCount, columnCount, bombCount, parent=None):
        super(MinesweeperModel, self).__init__(parent)
        self._rowCount = rowCount
        self._columnCount = columnCount
        self._bombCount = bombCount

        nonBombItems = set()

        self._items = [list() for _ in range(rowCount)]
        for row in range(rowCount):
            for column in range(columnCount):
                item = MinesweeperItem(row, column)
                self._items[row].append(item)
                nonBombItems.add(item)
        self._bombItems = set()
        for _ in range(bombCount):
            item = random.sample(nonBombItems, 1)[0]
            item.isBomb = True
            nonBombItems.remove(item)
            self._bombItems.add(item)
            for neighbor in self.bombNeighbors(self.index(item.row, item.column)):
                neighbor.internalPointer().bombNeighborCount += 1

    def bombNeighbors(self, index):
        neighbors = []
        for row in range(index.row() - 1, index.row() + 2):
            for column in range(index.column() - 1, index.column() + 2):
                neighbor = index.sibling(row, column)
                if neighbor.isValid() and neighbor != self:
                    neighbors.append(neighbor)
        return neighbors

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._columnCount

    def data(self, index, role=QtCore.Qt.DisplayRole):
        supportedRoles = (
            MinesweeperModel.BombNeighborRole,
            MinesweeperModel.IsBombRole,
            MinesweeperModel.IsRevealedRole,
        )

        if role not in supportedRoles:
            return None
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == MinesweeperModel.BombNeighborRole:
            return item.bombNeighborCount
        elif role == MinesweeperModel.IsBombRole:
            return item.isBomb
        elif role == MinesweeperModel.IsRevealedRole:
            return item.isRevealed
        return None

    def flags(self, index):
        return super(MinesweeperModel, self).flags(index) | QtCore.Qt.ItemIsEditable

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return QtCore.QModelIndex()
        if row < 0 or column < 0 or row >= self._rowCount or column >= self._columnCount:
            return QtCore.QModelIndex()
        return self.createIndex(row, column, self._items[row][column])

    def parent(self, index=None):
        if index is None:
            return super(MinesweeperModel, self).parent()
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._rowCount

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != MinesweeperModel.IsRevealedRole:
            return False
        item = index.internalPointer()
        item.isRevealed = value
        self.dataChanged.emit(index, index)
        return True

class MinesweeperDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return MinesweeperItemEditor(QtCore.QPersistentModelIndex(index), parent)

    def paint(self, painter, option, index):
        return

class MinesweeperItemEditor(QtGui.QWidget):
    def __init__(self, index, parent=None):
        super(MinesweeperItemEditor, self).__init__(parent)
        self.index = index

    def mouseReleaseEvent(self, event):
        self.index.model().setData(
            self.index.sibling(self.index.row(), self.index.column()),
            True,
            MinesweeperModel.IsRevealedRole
        )

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        isRevealed = self.index.data(MinesweeperModel.IsRevealedRole)
        painter.setPen(QtCore.Qt.NoPen)
        if not isRevealed:
            painter.setBrush(QtCore.Qt.white)
            painter.drawRect(event.rect())
            return

        painter.setBrush(QtCore.Qt.black)
        painter.drawRect(event.rect())

        bombNeighborCount = self.index.data(MinesweeperModel.BombNeighborRole)
        if bombNeighborCount:
            painter.setPen(QtCore.Qt.red)
            painter.drawText(event.rect(), QtCore.Qt.AlignCenter, str(bombNeighborCount))

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    model = MinesweeperModel(5, 10, 10)
    view = QtGui.QTableView()
    view.setModel(model)
    view.verticalHeader().hide()
    view.horizontalHeader().hide()
    view.horizontalHeader().setDefaultSectionSize(view.verticalHeader().defaultSectionSize())

    delegate = MinesweeperDelegate()
    view.setItemDelegate(delegate)

    for row in range(model.rowCount()):
        for column in range(model.columnCount()):
            index = model.index(row, column)
            view.openPersistentEditor(index)

    view.show()
    app.exec_()
