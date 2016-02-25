import os
import sys
import signal
from PyQt4 import QtGui, QtCore, uic
from state import ZkState
from kazoo.exceptions import KazooException
from kazoo.handlers.threading import TimeoutError


class MainWindow(QtGui.QMainWindow):

  def __init__(self):
    super(MainWindow, self).__init__()
    self.state = ZkState()
    self.tree_model = QtGui.QStandardItemModel()
    self.tree_model.setHorizontalHeaderLabels(['Items'])
    self.ui = uic.loadUi('main.ui', self)
    self.ui.actionQuit.triggered.connect(self.quit)
    self.ui.connectButton.clicked.connect(self.connect)
    self.ui.znodesTree.setModel(self.tree_model)
    self.ui.znodesTree.clicked.connect(self.tree_clicked)
    self.ui.znodesTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.ui.znodesTree.customContextMenuRequested.connect(self.tree_menu)
    self.update_widgets()

  @QtCore.pyqtSlot()
  def quit(self):
    sys.exit(0)

  @QtCore.pyqtSlot()
  def connect(self):
    if self.state.connected:
      self.state.disconnect()
      self.tree_model.clear()
    else:
      try:
        host, port = self.ui.hostBox.text().trimmed().split(':')
        port = int(port)
      except (ValueError, TypeError):
        QtGui.QMessageBox.critical(None, 'Failed connecting to ZK', 'Format is host:port')
        self.update_widgets()
        return
        
      try:
        self.state.connect(host, port)
      except (TimeoutError, KazooException) as e:  
        QtGui.QMessageBox.critical(None, 'Failed connecting to ZK', str(e))

    self.update_widgets()
    if self.state.connected:
      self.populate_tree()

  def update_widgets(self):
    if self.state.connected:
      self.ui.saveButton.setEnabled(True)
      self.ui.connectButton.setText('Disconnect')
      self.ui.statusbar.showMessage('Connected to {0}:{1}'.format(self.state.host, self.state.port))
    else:
      self.ui.saveButton.setEnabled(False)
      self.ui.historyButton.setEnabled(False)
      self.ui.connectButton.setText('Connect')
      self.ui.statusbar.showMessage('Disconnected')

  def recurse_tree(self, path, parent):
    item = QtGui.QStandardItem(os.path.basename(path) or '/')
    item.setEditable(False)
    item._path = path
    
    kids = self.state.get_kids(path)
    
    for kid in kids:
      self.recurse_tree(os.path.join(path, kid), item)

    if len(kids):
      icon_file = '/usr/share/icons/gnome/16x16/mimetypes/package-x-generic.png'
    else:
      icon_file = '/usr/share/icons/gnome/16x16/mimetypes/text-x-generic.png'

    item.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_file)))

    parent.appendRow(item)

  def populate_tree(self):
    if not self.state.connected:
      print 'not connected'
      return
    self.recurse_tree('/', self.tree_model)

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_clicked(self, index):
    item = self.tree_model.itemFromIndex(index)
    path = item._path
    contents = self.state.get_contents(path)
    self.ui.textBox.setText(contents)

    if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:
      print 'would spawn context for ' + path

  @QtCore.pyqtSlot(QtCore.QModelIndex)
  def tree_menu(self, position):
    indexes = self.znodesTree.selectedIndexes()
    if not len(indexes):
      return
    item = self.tree_model.itemFromIndex(indexes[0])
    path = item._path

    menu = QtGui.QMenu()
    menu.addAction('Create child of ' + path, lambda: self.create_child(path))
    menu.addAction('Delete ' + path, lambda: self.delete_path(path))

    menu.exec_(self.znodesTree.viewport().mapToGlobal(position))

  def delete_path(self, path):
    print 'would delete ' + path

  def create_child(self, path):
    print 'would create child of ' + path

def main():
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.show()
  if len(sys.argv) > 1:
    window._load_map(sys.argv[1])
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()