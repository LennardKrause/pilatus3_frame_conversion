_REVISION = 'v2019-07-02'

import sys, os, logging
from PyQt5 import QtWidgets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from _Classes_GUI import Main_GUI

def main():
    logging.debug(__name__)
    app = QtWidgets.QApplication(sys.argv)
    w = Main_GUI()
    w.setWindowTitle('Convert Pilatus3 Data to Bruker Format, {} | lkrause@chem.au.dk'.format(_REVISION))
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    # create logger
    logging.basicConfig(level=logging.INFO, style='{', format='{message:>20s} > {funcName}')
    main()
