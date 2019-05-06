#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Pilatus3-FC.py converts Pilatus-1M .tif images to Bruker .sfrm format
#   and writes mask files to be used with the integration software SAINT.
#   It is currently designed to convert data collected at either APS/15ID-D
#   or SPring-8/BL02B1.
#   Copyright (C) 2018, L.Krause <lkrause@chem.au.dk>, Aarhus University, DK.
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the Free
#   Software Foundation, either version 3 of the license, or (at your option)
#   any later version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#   more details. <http://www.gnu.org/licenses/>
#
#IMPORTANT:
#   Bruker is not associated with this software and will not support this.
#   Please direct any queries to L.Krause <lkrause@chem.au.dk>
#
_REVISION = 'v2019-04-25'

import sys, os, logging
from PyQt5 import QtWidgets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from _classes_GUI import Main_GUI

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
