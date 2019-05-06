_REVISION = 'v2019-04-25'

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
    # Remove existing handlers, Python creates a
    # default handler that goes to the console
    # and will ignore further basicConfig calls
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    # create logger
    logging.basicConfig(level=logging.INFO, style='{', format='{message:>20s} > {funcName}')
    main()
