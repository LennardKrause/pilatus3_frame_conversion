import os, sys, logging, re, glob
import numpy as np
from PyQt5 import QtCore, uic, QtWidgets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from _Classes_FrameView import FrameView
from _Utility import read_pilatus_cbf, read_pilatus_tif, get_run_info,\
                     convert_frame_APS_Bruker, convert_frame_SP8_Bruker,\
                     convert_frame_DLS_Bruker

class Main_GUI(QtWidgets.QMainWindow, uic.loadUiType(os.path.join(os.path.dirname(__file__), '_Main_GUI.ui'))[0]):
    def __init__(self):
        logging.info(self.__class__.__name__)
        super(QtWidgets.QMainWindow, self).__init__()
        self.setupUi(self)
        
        self.status = QtWidgets.QLabel()
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.statusBar.addWidget(self.status, 1)
        
        # essentials
        self.init_icons()
        self.init_styles()
        self.init_vars()
        self.set_tooltips()
        
        # window icon
        self.setWindowIcon(self.windowIcon)
        
        # installEventFilters allow us to use the 'line_edit' widget as a button 
        # and catch the FocusIn event to switch between data-path and sfrm-path
        # to be altered by the Filesystem browser
        self.paths_active = self.le_input
        self.le_input.installEventFilter(self)
        self.le_output.installEventFilter(self)
        
        # initiate the filebrowser
        self.init_file_browser()
        
        # init FrameView class
        self.FVObj = FrameView()
        self.wi_frameContainer.insertWidget(0, self.FVObj)
        self.FVObj.mask_written.connect(self.mask_check_stored)
        self.FVObj.frame_loaded.connect(self.fix_to_frame_dimensions.setFixedSize)
        
        # link GUI to functions
        self.tb_convert.clicked.connect(self.start_conversion)
        self.cb_link.stateChanged.connect(self.check_path_link)
        self.tb_mask_save.clicked.connect(self.mask_prepare_writing)
        self.hs_mask_int.valueChanged.connect(self.mask_change_frame_max_int)
        self.tb_mask_next_img.clicked.connect(lambda: self.mask_change_image_rel(inc =  1))
        self.tb_mask_prev_img.clicked.connect(lambda: self.mask_change_image_rel(inc = -1))
        self.cb_mask_fname.currentIndexChanged.connect(self.mask_change_image_abs)
        self.tb_mask_reset.clicked.connect(self.FVObj.reset_patches)
        self.tabWidget.currentChanged.connect(self.on_tab_change)
        
        # disable the draw-mask tabWidget
        # enable if valid images are loaded
        self.tabWidget.setTabEnabled(1, False)
        
        # hide progress and status-bar on startup
        self.pb_convert.hide()
        self.statusBar.hide()
        
    def set_tooltips(self):
        logging.info(self.__class__.__name__)
        # add tooltips
        self.tb_convert.setToolTip('Start the conversion')
        self.le_output.setToolTip('Current output directory.\nIf unlinked: Select to specify the target output directory using the file-browser.\nManual editing is allowed, non-existing paths will be created recursively.')
        self.le_input.setToolTip('Current input directory.\nIf unlinked: Select to specify the target input directory using the file-browser.')
        self.cb_link.setToolTip('Link/Unlink output directory and input directory.\nIf linked: the output directory follows the input directory (plus added suffix).\nIf unlinked: Select either to specify the target directory using the filebrowser.')
        self.cb_overwrite.setToolTip('Overwrite existing files in the output directory?')
    
    def init_file_browser(self):
        logging.info(self.__class__.__name__)
        # use the QFileSystemModel
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath('')
        #self.model.setNameFilters(['*.tif', '*.sfrm'])
        self.model.setNameFilterDisables(False)
        # currently only shows directories
        # use:  | QtCore.QDir.AllEntries
        # to show files
        self.model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)# | QtCore.QDir.AllEntries)
        
        # set treeView to use the QFileSystemModel 
        self.treeView.setModel(self.model)
        self.treeView.setAnimated(False)
        self.treeView.setIndentation(20)
        #self.treeView.setSortingEnabled(True)
        # don't strech last column
        self.treeView.header().setStretchLastSection(False)
        # stretch first
        self.treeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # hide 'size' and 'type' header columns
        self.treeView.setColumnHidden(1, True)
        self.treeView.setColumnHidden(2, True)
        
        # scroll the treeview to start_dir
        # apply start_dir as current dir by calling the 'on_click' function
        start_dir = os.getcwd()
        self.treeView.scrollTo(self.model.index(start_dir))
        self.on_treeView_clicked(self.model.index(start_dir))
        
    def init_icons(self):
        logging.info(self.__class__.__name__)
        # icons
        self.windowIcon = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_BrowserReload'))
        self.ic_MessageBoxWarning = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MessageBoxWarning'))
        self.ic_MessageBoxCritical = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MessageBoxCritical'))
        self.ic_MessageBoxInformation = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MessageBoxInformation'))
        self.ic_MessageBoxQuestion = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MessageBoxQuestion'))
        
    def init_styles(self):
        logging.info(self.__class__.__name__)
        self.pb_style = ('QProgressBar        {text-align: center; border: 1px solid grey; border-radius: 2px}'
                         'QProgressBar:chunk  {background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 rgb(  0, 171, 164), stop: 1 rgb( 55, 160, 203));}')
        
        self.tb_style = ('QToolButton          {background-color: rgb(240, 240, 240); color: rgb(  0,   0,   0); border: 1px solid rgb( 75,  75,  75); border-radius: 2px}'
                         'QToolButton:hover    {background-color: rgb(255, 255, 255); color: rgb(  0,   0,   0); border: 1px solid rgb( 75,  75,  75)}'
                         'QToolButton:pressed  {background-color: rgb(255, 255, 255); color: rgb(  0,   0,   0); border: 1px solid rgb( 75,  75,  75)}'
                         'QToolButton:checked  {background-color: rgb(200, 200, 200); color: rgb(  0,   0,   0); border: 1px solid rgb( 75,  75,  75)}'
                         'QToolButton:disabled {background-color: rgb(220, 200, 200); color: rgb(  0,   0,   0); border: 1px solid rgb( 75,  75,  75)}')
                                 
        self.le_style_coupled = ('QLineEdit      {background-color: rgb(240, 240, 240)}')
        
        self.le_style_single = ('QLineEdit       {background-color: rgb(250, 250, 250); border-width: 2px; border-style: solid; border-color: rgb(100, 255, 100)}'
                                'QLineEdit:hover {background-color: rgb(250, 250, 250); border-width: 2px; border-style: solid; border-color: rgb(100, 255, 100)}'
                                'QLineEdit:focus {background-color: rgb(250, 250, 250); border-width: 2px; border-style: solid; border-color: rgb(100, 255, 100)}')
        
        self.rb_style = ('QCheckBox                      {background-color:white; color:black;}'
                         'QCheckBox::indicator           {width:10px; height:10px;border-radius:7px;}'
                         'QCheckBox::indicator:checked   {background-color:limegreen}'
                         'QCheckBox::indicator:unchecked {background-color:crimson}')
        
        # apply style sheets
        self.cb_mask_stored.setStyleSheet(self.rb_style)
        self.le_input.setStyleSheet(self.le_style_coupled)
        self.le_output.setStyleSheet(self.le_style_coupled)
        self.tb_convert.setStyleSheet(self.tb_style)
        self.tb_mask_save.setStyleSheet(self.tb_style)
        self.tb_mask_reset.setStyleSheet(self.tb_style)
        self.pb_convert.setStyleSheet(self.pb_style)
        self.tabWidget.setStyleSheet('QTabBar::tab { height: 25px; width: 200px; }')
        self.tb_mask_prev_img.setStyleSheet(self.tb_style)
        self.tb_mask_next_img.setStyleSheet(self.tb_style)
        self.tb_mask_prev_img.setArrowType(QtCore.Qt.LeftArrow)
        self.tb_mask_next_img.setArrowType(QtCore.Qt.RightArrow)
        
    def init_vars(self):
        logging.info(self.__class__.__name__)
        '''
         
        '''
        self.fRnum = None
        self.fStem = None
        self.fPath = None
        self.rList = []
        self.fList = []
        self.suffix = '_sfrm'
        
        # some hardcoded limits that might make sense
        self.hs_mask_int.setMaximum(1000)
        
        #########################################
        ##  Add new format identifiers here!   ##
        #########################################
        self.exts = ('*_*.tif', '*_*.cbf')
        self.availableFormats = [self.format_SP8,
                                 self.format_APS,
                                 self.format_DLS]
    
    ##############################################
    ##         Frame Format definitions         ##
    ##############################################
    def check_format(self, aFrame):
        logging.info(self.__class__.__name__)
        for aCheckFunc in self.availableFormats:
            if aCheckFunc(aFrame):
                return True
            else:
                continue
        return False
    
    def format_DLS(self, aFrame):
        logging.info(self.__class__.__name__)
        '''
        Check the first file if reformatting to Bruker name format is possible
        any_name_#run_#frame.tif -> any_name_rr_ffff.sfrm
        '''
        try:
            fhead, fname = os.path.split(aFrame)
            bname, ext = os.path.splitext(fname)
            if not ext == '.cbf':
                return False
            # open file and check: _diffrn.id DLS_I19-1
            with open(aFrame, 'rb') as oFrame:
                try:
                    id = re.search(b'_diffrn.id\s+(?P<id>.+)', oFrame.read(2048)).group('id').decode().strip()
                except AttributeError:
                    return False
            if not id == 'DLS_I19-1':
                return False
            fstm, rnum, fnum, flen = get_run_info(bname)
            self.fRnum = rnum                         # Run number
            self.fStem = fstm                         # Frame name up to the run number
            self.fPath = aFrame                       # Full path to frame incl. frame name
            self.fStar = '{:>0{w}}.'.format(1, w=flen)# Number indicating start of a run
            self.fInfo = (1679, 1475, 0)              # Frame info (rows, cols, offset)
            self.fSite = 'DLS'                        # Facility identifier
            self.fFunc = read_pilatus_cbf             # Frame read function (from _Utility)
            self.fRota = False                        # rotate the frame upon conversion?
            return True
        except (ValueError, IndexError):
            return False
    
    def format_APS(self, aFrame):
        logging.info(self.__class__.__name__)
        '''
        Check the first file if reformatting to Bruker name format is possible
        any_name_#run_#frame.tif -> any_name_rr_ffff.sfrm
        '''
        try:
            fhead, fname = os.path.split(aFrame)
            bname, ext = os.path.splitext(fname)
            if not ext == '.tif':
                return False
            # open file and check S/N: 10-0147
            with open(aFrame, 'rb') as oFrame:
                SN = re.search(b'S/N\s+(?P<SN>\d+\-\d+)', oFrame.read(128)).group('SN').decode()
            if not SN == '10-0147':
                return False
            fstm, rnum, fnum, flen = get_run_info(bname)
            self.fRnum = rnum                         # Run number
            self.fStem = fstm                         # Frame name up to the run number
            self.fPath = aFrame                       # Full path to frame incl. frame name
            self.fStar = '{:>0{w}}.'.format(1, w=flen)# Number indicating start of a run
            self.fInfo = (1043, 981, 4096)            # Frame info (rows, cols, offset)
            self.fSite = 'APS'                        # Facility identifier
            self.fFunc = read_pilatus_tif             # Frame read function (from _Utility)
            self.fRota = True                         # rotate the frame upon conversion?
            return True
        except (ValueError, IndexError):
            return False
    
    def format_SP8(self, aFrame):
        logging.info(self.__class__.__name__)
        '''
        Check the first file if name is compatible with SPring-8 convention
        e.g. any_name_rrfff.tif, where rr is the 2 digit run numer: 00 - 99
        fff is the 3 digit frame number: 001 - 999
        '''
        try:
            fhead, fname = os.path.split(aFrame)
            bname, ext = os.path.splitext(fname)
            if not ext == '.tif':
                return False
            # open file and check S/N: 10-0163
            with open(aFrame, 'rb') as oFrame:
                SN = re.search(b'S/N\s+(?P<SN>\d+\-\d+)', oFrame.read(128)).group('SN').decode()
            if not SN == '10-0163':
                return False
            fstm, rnum, fnum, flen = get_run_info(bname)
            ########################################
            ## USE FNUM TO DEFINE START OF RUN!!! ##
            ########################################
            self.fRnum = rnum                         # Run number
            self.fStem = fstm                         # Frame name up to the run number
            self.fPath = aFrame                       # Full path to frame incl. frame name
            self.fStar = '{:>0{w}}.'.format(1, w=flen)# Number indicating start of a run
            self.fInfo = (1043, 981, 4096)            # Frame info (rows, cols, offset)
            self.fSite = 'SP8'                        # Facility identifier
            self.fFunc = read_pilatus_tif             # Frame read function (from _Utility)
            self.fRota = True                         # rotate the frame upon conversion?
            return True
        except ValueError:
            return False
    ##############################################
    ##       END Frame Format definitions       ##
    ##############################################
    
    def mask_prepare_writing(self):
        logging.info(self.__class__.__name__)
        oPath = os.path.abspath(self.le_output.text())
        self.create_output_directory(oPath)
        aMask = os.path.join(oPath, '{}_xa_{:>02}_0001.sfrm'.format(self.fStem, int(self.fRnum)))
        self.FVObj.convert_patches_to_mask(self.fPath, aMask)
    
    def mask_check_stored(self, aFrame):
        logging.info(self.__class__.__name__)
        if aFrame in self.FVObj.masks:
            self.cb_mask_stored.setChecked(True)
        else:
            self.cb_mask_stored.setChecked(False)
    
    def mask_change_image_abs(self, idx):
        logging.info(self.__class__.__name__)
        aFrame = os.path.abspath(self.rList[idx])
        self.check_format(aFrame)
        self.mask_check_stored(aFrame)
        self.FVObj.frame_update(aFrame, self.fFunc, *self.fInfo, rotate=self.fRota)
    
    def mask_change_image_rel(self, inc):
        logging.info(self.__class__.__name__)
        idx = self.cb_mask_fname.currentIndex() + int(inc)
        if idx < 0 or idx >= self.cb_mask_fname.count():
            return
        # setCurrentIndex calls self.mask_change_image_abs
        self.cb_mask_fname.setCurrentIndex(idx)
    
    def mask_change_frame_max_int(self):
        #logging.info(self.__class__.__name__)
        self.FVObj.showFrame.set_clim(vmin=0, vmax=self.hs_mask_int.value())
        self.FVObj.cmap_max = self.hs_mask_int.value()
        self.FVObj.draw()
        
    def eventFilter(self, obj, event):
        #logging.info(self.__class__.__name__)
        '''
         
        '''
        if event.type() == QtCore.QEvent.FocusIn:
            if (obj == self.le_input or obj == self.le_output) and self.cb_link.isChecked():
                self.le_input.setStyleSheet(self.le_style_coupled)
                self.le_output.setStyleSheet(self.le_style_coupled)
                self.paths_active = self.le_input
                self.treeView.scrollTo(self.model.index(self.le_input.text()))
            elif obj == self.le_output and not self.cb_link.isChecked():
                self.le_input.setStyleSheet(self.le_style_coupled)
                self.le_output.setStyleSheet(self.le_style_single)
                self.paths_active = self.le_output
                self.treeView.scrollTo(self.model.index(self.le_output.text()))
            elif obj == self.le_input and not self.cb_link.isChecked():
                self.le_input.setStyleSheet(self.le_style_single)
                self.le_output.setStyleSheet(self.le_style_coupled)
                self.paths_active = self.le_input
                self.treeView.scrollTo(self.model.index(self.le_input.text()))
        return super(Main_GUI, self).eventFilter(obj, event)

    def popup_window(self, _title, _text, _info):
        logging.info(self.__class__.__name__)
        '''
         _icon:
            QtWidgets.QMessageBox.NoIcon      0 the message box does not have any icon.
            QtWidgets.QMessageBox.Information 1 an icon indicating that the message is nothing out of the ordinary.
            QtWidgets.QMessageBox.Warning     2 an icon indicating that the message is a warning, but can be dealt with.
            QtWidgets.QMessageBox.Critical    3 an icon indicating that the message represents a critical problem.
            QtWidgets.QMessageBox.Question    4 an icon indicating that the message is asking a question.
        '''
        if _title.upper() == 'INFORMATION':
            _wicon = self.windowIcon#self.ic_MessageBoxInformation
            _icon = QtWidgets.QMessageBox.Information
        elif _title.upper() == 'WARNING':
            _wicon = self.windowIcon#self.ic_MessageBoxWarning
            _icon = QtWidgets.QMessageBox.Warning
        elif _title.upper() == 'CRITICAL':
            _wicon = self.windowIcon#self.ic_MessageBoxCritical
            _icon = QtWidgets.QMessageBox.Critical
        elif _title.upper() == 'QUESTION':
            _wicon = self.windowIcon#self.ic_MessageBoxQuestion
            _icon = QtWidgets.QMessageBox.Question
        else:
            _wicon = self.windowIcon
            _icon = QtWidgets.QMessageBox.NoIcon
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowIcon(_wicon)
        msgBox.setIcon(_icon)
        msgBox.setWindowTitle(_title)
        msgBox.setText(_text)
        msgBox.setInformativeText(_info)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()
    
    def check_path_link(self):
        logging.info(self.__class__.__name__)
        '''
         switch between input / output path manipulation
         this function ONLY takes care about the stylesheet
         and determines which one is active after toggling
         the link checkbox 'self.cb_link.isChecked()'
          - if checked, both paths reference to 'self.le_input'
          - 'self.paths_active' links to the currently active object
          - checked: 'self.le_input' is active (always)
          - unchecked: 'self.le_output' is activated by default,
            can be switched
        '''
        self.le_input.setStyleSheet(self.le_style_coupled)
        self.le_output.setStyleSheet(self.le_style_coupled)
        if self.cb_link.isChecked():
            self.paths_active = self.le_input
            self.le_output.setText(self.le_input.text() + self.suffix)
        else:
            self.paths_active = self.le_output
            self.paths_active.setStyleSheet(self.le_style_single)
        
    def on_tab_change(self, idx):
        '''
         update frame only if Frameviewer tab is opened
        '''
        if idx == 1:
            self.mask_check_stored(self.fPath)
            self.FVObj.frame_update(self.fPath, self.fFunc, *self.fInfo, rotate=self.fRota)
        else:
            return
    
    def on_treeView_clicked(self, index):
        logging.info(self.__class__.__name__)
        '''
         Current find run_list implementation is flawed yet simple:
         - iterate over all frames found and find the 001. (SP8) or 
           0001. (APS) entries that mark the beginning of a new run
         - if the first frame is missing THIS WILL CRASH!
           hence, to be fixed later, if ever.
        '''
        indexItem = self.model.index(index.row(), 0, index.parent())
        curPath = os.path.abspath(self.model.filePath(indexItem))
        
        if self.cb_link.isChecked():
            self.le_input.setText(curPath)
            self.le_output.setText(curPath + self.suffix)
        
        elif self.paths_active == self.le_input:
            self.le_input.setText(curPath)
        
        elif self.paths_active == self.le_output:
            self.le_output.setText(curPath)
            return
        
        self.tb_convert.setText('Convert Images')
        self.tb_convert.setEnabled(False)
        
        # find files
        fDir = QtCore.QDir()
        fDir.setPath(curPath)
        fDir.setNameFilters(self.exts)
        fDir.setFilter(QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
        fDir.setSorting(QtCore.QDir.Name)
        nFrames = fDir.count()
        
        if nFrames > 0:
            self.fList = [i.absoluteFilePath() for i in fDir.entryInfoList()]
            if not self.check_format(os.path.abspath(self.fList[0])):
                return
            
            # Incorrect/Incomplete runs may end in empty self.rList
            # - e.g. if first frame is missing it's not considered a run!
            # - self.fStar is updated by self.check_format()
            self.rList = sorted([os.path.abspath(f) for f in self.fList if self.fStar in f])
            # generate the mask list here would save calling check_format a lot!
            # - getting the run name however is non-trivial due to different naming conventions!
            # - here: simple counting solution - bad idea!
            #self.mList = [os.path.join(self.le_output.text(), '{}_xa_{:>02}_0001.sfrm'.format(self.fStem, i)) for i in range(len((self.rList)))]
            if len(self.rList) == 0:
                return
            
            # clearing and adding to combobox triggers it's .currentIndexChanged()
            # block signals to not call self.mask_change_image_abs
            self.cb_mask_fname.blockSignals(True)
            # clear combobox
            self.cb_mask_fname.clear()
            # add runs to combobox
            [self.cb_mask_fname.addItem(os.path.basename(i)) for i in self.rList]
            self.cb_mask_fname.blockSignals(False)
            
            # if we are here we may allow conversion
            # - the check for the .inf files (SP8 data) is done
            #   by the actual conversion function!
            self.tb_convert.setText('Convert {} Images'.format(nFrames))
            self.tabWidget.setTabEnabled(1, True)
            self.tb_convert.setEnabled(True)
        
        elif self.paths_active == self.le_input:
            self.tabWidget.setTabEnabled(1, False)
        else:
            logging.info('You should not be able to read this message!')
                    
    def create_output_directory(self, aPath):
        logging.info(self.__class__.__name__)
        # create output file path
        if not os.path.exists(aPath):
            os.makedirs(aPath)
    
    def disable_user_input(self, toggle):
        logging.info(self.__class__.__name__)
        self.cb_link.setDisabled(toggle)
        self.cb_overwrite.setDisabled(toggle)
        self.le_input.setDisabled(toggle)
        self.le_output.setDisabled(toggle)
        self.treeView.setDisabled(toggle)
        
    def start_conversion(self):
        logging.info(self.__class__.__name__)
        '''
          - assign data/sfrm paths
          - get files (again)
          - check for files
          - check if facility is set and proceed accordingly
             - check image name format
             - create sfrm directory
             - start conversion for facility
        '''
        #####################################
        ##     THIS MIGHT BE REDUNDANT     ##
        ## CHECK IF REASSIGNMENT IS NEEDED ##
        #####################################
        # QLineEdit current text to path
        path_input = os.path.abspath(self.le_input.text())
        path_output = os.path.abspath(self.le_output.text())
        #####################################
        
        # check if there are any files
        if not self.fList:
            self.popup_window('Information', 'No suitable image files found.', 'Please check path.')
            return
        
        # Make directories recursively
        self.create_output_directory(path_output)
        
        # disable main window elements
        # re-enabled after conversion finished
        # -> at end of 'start_conversion'
        self.disable_user_input(True)
        
        # check if overwrite flag is set and
        # pass it on to the conversion function
        overwrite_flag = self.cb_overwrite.isChecked()
        
        # create a pool of workers
        #  - pool.apply_async, map doesn't work since we need to specify the output directory!
        #  - the list 'results' together with 'callback=results.append' is used to track the conversion progress
        #     - 'while len(results) != _todo' constantly checks results to update the progressbar
        #  - pool.close(): close the pool when there are no more files left in 'self.fList'
        #  - pool.join(): wait for remaining processes to finish
        #########################################
        ##  Add new format identifiers here!   ##
        #########################################
        # fork here according to specified facility
        #  - conversion: what _Utility.py function to call
        #  - parameters: parameters for the conversion function
        #     - path_output, dimension1, dimension2, overwrite_flag
        #     - more if needed, e.g. SP8 2-th correction value
        if self.fSite == 'APS':
            rows, cols, offset = self.fInfo
            conversion = convert_frame_APS_Bruker
            beamflux = {}
            for f in glob.glob(os.path.join(path_input,'*_flux.txt')):
                with open(f) as ofile:
                    beamflux[int(f.split('_')[-2])] = [int(float(x)) for x in ofile.read().split()[1::2]]
            args = [path_output]
            kwargs = {'rows':rows, 'cols':cols, 'offset':offset, 'overwrite':overwrite_flag, 'beamflux':beamflux}
        elif self.fSite == 'SP8':
            rows, cols, offset = self.fInfo
            # check data collection timestamp
            with open(self.fPath, 'rb') as ofile:
                year = int(re.search(b'(\d{4}):\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}', ofile.read(64)).group(1).decode())
            SP8_tth_corr = 0.0
            if year < 2019:
                SP8_tth_corr = 0.048
            conversion = convert_frame_SP8_Bruker
            args = [path_output]
            kwargs = {'tth_corr':SP8_tth_corr, 'rows':rows, 'cols':cols, 'offset':offset, 'overwrite':overwrite_flag}
        elif self.fSite == 'DLS':
            rows, cols, offset = self.fInfo
            conversion = convert_frame_DLS_Bruker
            args = [path_output]
            kwargs = {'rows':rows, 'cols':cols, 'offset':offset, 'overwrite':overwrite_flag}
        else:
            self.popup_window('Information', 'Unknown facility!', '')
            return
        
        self.tb_convert.hide()
        self.pb_convert.show()
        self.statusBar.show()
        
        # Now uses QRunnable and QThreadPool instead of multiprocessing.pool()
        self.num_to_convert = len(self.fList)
        self.converted = []
        self.pool = QtCore.QThreadPool()
        for fname in self.fList:
            worker = self.__class__.Threading(conversion, fname, args, kwargs)
            worker.signals.finished.connect(self.conversion_process)
            self.pool.start(worker)

    class Threading(QtCore.QRunnable):
        class Signals(QtCore.QObject):
            '''
             Custom signals can only be defined on objects derived from QObject
            '''
            finished = QtCore.pyqtSignal(bool)
    
        def __init__(self, fn_conversion, file_name, fn_args, fn_kwargs):
            '''
             fn_conversion: Conversion function
             file_name:     File name to convert
             fn_args:       Arguments to pass to the function
             fn_kwargs:     Keywords to pass to the function
            '''
            super(self.__class__, self).__init__()
            self.conversion = fn_conversion
            self.name = file_name
            self.args = fn_args
            self.kwargs = fn_kwargs
            self.signals = self.__class__.Signals()
        
        def run(self):
            # conversion: returns True/False
            # signal to conversion_process to track the process
            self.signals.finished.emit(self.conversion(self.name, *self.args, **self.kwargs))
    
    def conversion_process(self, finished):
        self.converted.append(finished)
        num_converted = len(self.converted)
        progress = float(num_converted) / float(self.num_to_convert) * 100.0
        self.pb_convert.setValue(progress)
        self.status.setText('{}'.format(os.path.basename(self.fList[num_converted-1])))
        # conversion finished
        if num_converted == self.num_to_convert:
            self.popup_window('Information', 'Successfully converted {} images!'.format(np.count_nonzero(self.converted)), '')
            self.statusBar.hide()
            self.pb_convert.hide()
            self.tb_convert.show()
            # enable main window elements
            self.disable_user_input(False)
        
    def closeEvent(self, event):
        logging.info(self.__class__.__name__)
        '''
        User clicks the 'x' mark in window
        '''
        self.exitApp()

    def exitApp(self):
        logging.info(self.__class__.__name__)
        sys.exit()