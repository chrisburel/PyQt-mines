from PyQt4 import QtCore, QtGui
import random

class MinesweeperItem(object):
    def __init__(self, row, column):
        self.row = row
        self.column = column
        self._isBomb = False
        self._bombNeighborCount = 0

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

class MinesweeperModel(QtCore.QAbstractItemModel):
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
        if role != QtCore.Qt.DisplayRole:
            return None
        if not index.isValid():
            return None
        item = index.internalPointer()
        if item.isBomb:
            return 'B'
        if item.bombNeighborCount:
            return str(item.bombNeighborCount)
        return ''

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

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    model = MinesweeperModel(5, 10, 10)
    view = QtGui.QTableView()
    view.setModel(model)
    view.verticalHeader().hide()
    view.horizontalHeader().hide()
    view.horizontalHeader().setDefaultSectionSize(view.verticalHeader().defaultSectionSize())
    view.show()
    app.exec_()
