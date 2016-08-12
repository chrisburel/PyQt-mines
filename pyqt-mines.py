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
        self._isMarked = False
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
    def isMarked(self):
        return self._isMarked

    @isMarked.setter
    def isMarked(self, newVal):
        self._isMarked = newVal

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
    IsMarkedRole = QtCore.Qt.UserRole + 3

    gameWon = QtCore.Signal()
    gameOver = QtCore.Signal()

    def __init__(self, rowCount, columnCount, bombCount, parent=None):
        super(MinesweeperModel, self).__init__(parent)
        self._rowCount = rowCount
        self._columnCount = columnCount
        self._bombCount = bombCount
        self._revealedCount = 0
        self._countToWin = rowCount * columnCount - bombCount

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
            MinesweeperModel.IsMarkedRole,
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
        elif role == MinesweeperModel.IsMarkedRole:
            return item.isMarked
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
        if not index.isValid():
            return False

        item = index.internalPointer()
        if role == MinesweeperModel.IsRevealedRole:
            if item.isRevealed == value:
                return
            item.isRevealed = value

            if item.isBomb and item.isRevealed:
                self.gameOver.emit()

            self._revealedCount += 1
            self.dataChanged.emit(index, index)

            if self._revealedCount == self._countToWin:
                self.gameWon.emit()
                return True

            if item.bombNeighborCount == 0:
                for neighbor in self.bombNeighbors(index):
                    self.setData(neighbor, value, role)
            return True
        elif role == MinesweeperModel.IsMarkedRole:
            if item.isMarked == value:
                return
            item.isMarked = value
            self.dataChanged.emit(index, index)
            return True
        return False

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
        index = self.index.sibling(self.index.row(), self.index.column())
        marked = index.data(MinesweeperModel.IsMarkedRole)
        if event.button() == QtCore.Qt.LeftButton and not marked:
            index.model().setData(
                index,
                True,
                MinesweeperModel.IsRevealedRole
            )
        elif event.button() == QtCore.Qt.RightButton:
            index.model().setData(
                index,
                not marked,
                MinesweeperModel.IsMarkedRole
            )
        elif event.button() == QtCore.Qt.MiddleButton:
            neighbors = index.model().bombNeighbors(index)
            bombNeighborCount = index.data(MinesweeperModel.BombNeighborRole)
            unmarkedNeighbors = [n for n in neighbors if not n.data(MinesweeperModel.IsMarkedRole)]
            if len(neighbors) - len(unmarkedNeighbors) == bombNeighborCount:
                for neighbor in unmarkedNeighbors:
                    index.model().setData(
                        neighbor,
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

            isMarked = self.index.data(MinesweeperModel.IsMarkedRole)
            if isMarked:
                painter.setBrush(QtCore.Qt.red)
                trianglePoints = [
                    event.rect().bottomLeft(),
                    event.rect().topLeft(),
                    event.rect().bottomRight(),
                ]
                painter.drawPolygon(trianglePoints)
            return

        isBomb = self.index.data(MinesweeperModel.IsBombRole)
        if isBomb:
            painter.setBrush(QtCore.Qt.red)
        else:
            painter.setBrush(QtCore.Qt.black)
        painter.drawRect(event.rect())

        bombNeighborCount = self.index.data(MinesweeperModel.BombNeighborRole)
        if bombNeighborCount:
            painter.setPen(QtCore.Qt.red)
            painter.drawText(event.rect(), QtCore.Qt.AlignCenter, str(bombNeighborCount))

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    model = MinesweeperModel(16, 30, 99)
    view = QtGui.QTableView()
    view.setModel(model)
    view.verticalHeader().hide()
    view.horizontalHeader().hide()
    view.horizontalHeader().setDefaultSectionSize(view.verticalHeader().defaultSectionSize())
    view.resize(
        view.horizontalHeader().length() + 6,
        view.verticalHeader().length() + 6,
    )

    delegate = MinesweeperDelegate()
    view.setItemDelegate(delegate)

    for row in range(model.rowCount()):
        for column in range(model.columnCount()):
            index = model.index(row, column)
            view.openPersistentEditor(index)

    model.gameOver.connect(lambda: QtGui.QMessageBox.information(
        view,
        'Game Over',
        'Game Over!'
    ))
    model.gameWon.connect(lambda: QtGui.QMessageBox.information(
        view,
        'You Win',
        'You Win!'
    ))

    view.show()
    app.exec_()
