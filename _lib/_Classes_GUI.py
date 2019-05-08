import os, sys, logging, glob, multiprocessing, re
import numpy as np
from PyQt5 import QtCore, uic, QtWidgets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from _Classes_FrameView import FrameView
from _Utility import *

class Main_GUI(QtWidgets.QMainWindow, uic.loadUiType(os.path.join(os.path.dirname(__file__), '_Main_GUI.ui'))[0]):
    def __init__(self, parent=None):
        logging.info(self.__class__.__name__)
        super(QtWidgets.QMainWindow, self).__init__(parent)
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
        
        # initiate the filebrowse
        self.init_file_browser()
        
        # init FrameView class
        self.FVObj = FrameView()
        self.wi_frameContainer.insertWidget(0, self.FVObj)
        self.FVObj.mask_written.connect(self.mask_check_stored)
        self.FVObj.frame_loaded.connect(self.fix_to_frame_dimensions.setFixedSize)
        
        # link gui to functions
        self.tb_convert.clicked.connect(self.prepare_conversion)
        self.cb_link.stateChanged.connect(self.check_path_link)
        self.tb_mask_save.clicked.connect(self.mask_prepare_writing)
        self.hs_mask_int.valueChanged.connect(self.mask_change_frame_max_int)
        self.tb_mask_next_img.clicked.connect(lambda: self.mask_change_image_rel(inc =  1))
        self.tb_mask_prev_img.clicked.connect(lambda: self.mask_change_image_rel(inc = -1))
        self.cb_mask_fname.currentIndexChanged.connect(self.mask_change_image_abs)
        self.tb_mask_reset.clicked.connect(self.FVObj.reset_patches)
        self.tabWidget.currentChanged.connect(lambda: self.FVObj.frame_update(self.fList[0], *self.fdim, self.rfunct, self.rotate))
        
        # disable the beamstop draw tabWidget
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
        self.treeView.header().setStretchLastSection(False)
        self.treeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # hide 'size' and 'type' header columns
        self.treeView.setColumnHidden(1, True)
        self.treeView.setColumnHidden(2, True)
        
        # scroll the treeview to start_dir
        # apply start_dir as current dir
        # by calling the 'on_click' function
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
        self.frnum = None
        self.fstem = None
        self.fpath = None
        self.rList = []
        self.fList = []
        self.suffix = '_sfrm'
        
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
            with open(aFrame) as oFrame:
                id = re.search('_diffrn.id\s+(?P<id>.+)', oFrame.read(2048)).group('id')
            if not id == 'DLS_I19-1':
                return
            _split = bname.split('_')
            fnum = _split.pop()
            rnum = _split.pop()
            fstm = '_'.join(_split)
            ###############################
            ##    if this doesn't fail   ##
            ##   we assume DLS format!   ##
            ###############################
            _          = int(fnum)
            self.frnum = int(rnum)
            ###############################
            self.fstem = fstm
            self.fpath = aFrame
            self.first = '00001.'
            self.fdim = (1679, 1475, 0) # (rows, cols, offset)
            self.site = 'DLS'
            self.rfunct = read_pilatus_cbf
            self.rotate = False
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
            _split = bname.split('_')
            fnum = _split.pop()
            rnum = _split.pop()
            fstm = '_'.join(_split)
            ###############################
            ##    if this doesn't fail   ##
            ##   we assume APS format!   ##
            ###############################
            _          = int(fnum)
            self.frnum = int(rnum)
            ###############################
            self.fstem = fstm
            self.fpath = aFrame
            self.first = '0001.'
            self.fdim = (1043, 981, 4096) # (rows, cols, offset)
            self.site = 'APS'
            self.rfunct = read_pilatus_tif
            self.rotate = True
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
            fstm = bname[:-6]
            rnum = bname[-5:-3]
            fnum = bname[-3:]
            ###############################
            ##    if this doesn't fail   ##
            ##   we assume SP8 format!   ##
            ###############################
            _          = int(fnum)
            self.frnum = int(rnum)
            ###############################
            self.fstem = fstm
            self.fpath = aFrame
            self.first = '001.'
            self.fdim = (1043, 981, 4096) # (rows, cols, offset)
            self.site = 'SP8'
            self.rfunct = read_pilatus_tif
            self.rotate = True
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
        aMask = os.path.join(oPath, '{}_xa_{:>02}_0001.sfrm'.format(self.fstem, int(self.frnum)))
        self.FVObj.convert_patches_to_mask(self.fpath, aMask)
    
    def mask_check_stored(self, aFrame):
        logging.info(self.__class__.__name__)
        if aFrame in self.FVObj.masks:
            self.cb_mask_stored.setChecked(True)
        else:
            self.cb_mask_stored.setChecked(False)
    
    def mask_change_image_abs(self, idx):
        logging.info(self.__class__.__name__)
        aFrame = self.rList[idx]
        self.check_format(aFrame)
        self.FVObj.frame_update(aFrame, *self.fdim, self.rfunct, self.rotate)
        self.mask_check_stored(aFrame)
    
    def mask_change_image_rel(self, inc):
        logging.info(self.__class__.__name__)
        idx = self.cb_mask_fname.currentIndex() + int(inc)
        if idx < 0 or idx >= self.cb_mask_fname.count():
            return
        # setCurrentIndex calls self.mask_change_image_abs
        self.cb_mask_fname.setCurrentIndex(idx)
    
    def mask_change_frame_max_int(self):
        #logging.info(self.__class__.__name__)
        self.FVObj.intMax = self.hs_mask_int.value()
        self.FVObj.showFrame.set_clim(vmin=0, vmax=self.hs_mask_int.value())
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
        msgBox.exec()
    
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
        fPath = self.model.filePath(indexItem)
        
        if self.cb_link.isChecked():
            self.le_input.setText(fPath)
            self.le_output.setText(fPath + self.suffix)
        
        elif self.paths_active == self.le_input:
            self.le_input.setText(fPath)
        
        elif self.paths_active == self.le_output:
            self.le_output.setText(fPath)
            return
        
        self.tb_convert.setText('Convert Images')
        self.tb_convert.setEnabled(False)
        
        # find files
        fDir = QtCore.QDir()
        fDir.setPath(fPath)
        fDir.setNameFilters(self.exts)
        fDir.setFilter(QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
        nFrames = fDir.count()
        
        # - check frame format
        # - switch buttons (self.rb_SP8_Bruker or self.rb_APS_Bruker)
        if nFrames > 0:
            self.fList = [i.absoluteFilePath() for i in fDir.entryInfoList()]
            if not self.check_format(self.fList[0]):
                return
            
            # Incorrect/Incomplete runs may trigger this
            # - e.g. if first frame is missing it's not considered a run!
            # - self.first gets defined by self.check_format()
            self.rList = sorted([os.path.abspath(f) for f in self.fList if self.first in f])
            # generate the mask list here would save calling check_format a lot!
            # - getting the run name however is non-trivial due to different naming conventions!
            # - here: simple counting solution - bad idea!
            #self.mList = [os.path.join(self.le_output.text(), '{}_xa_{:>02}_0001.sfrm'.format(self.fstem, i)) for i in range(len((self.rList)))]
            if len(self.rList) == 0:
                return
            
            # clear combobox
            self.cb_mask_fname.blockSignals(True)
            # clearing calls self.mask_change_image_abs
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
        
    def prepare_conversion(self):
        logging.info(self.__class__.__name__)
        '''
         function preceding the actual conversion:
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
        
        # self.site tell start_conversion what to do!
        self.start_conversion(self.site, path_output, self.fList)
    
    def start_conversion(self, source, path_output, file_list):
        logging.info(self.__class__.__name__)
        '''
         create a pool of workers
          - pool.apply_async, map doesn't work since we need to specify the output directory!
          - the list 'results' together with 'callback=results.append' is used to track the conversion progress
             - 'while len(results) != _todo' constantly checks results to update the progressbar
          - pool.close(): close the pool when there are no more files left in 'self.fList'
          - pool.join(): wait for remaining processes to finish
        '''
        logging.info(source)
        # disable main window elements
        # re-enabled after conversion finished
        # -> at end of 'start_conversion'
        self.disable_user_input(True)
        
        # check if overwrite flag is set and
        # pass it on to the conversion function
        overwrite_flag = self.cb_overwrite.isChecked()
        
        with multiprocessing.Pool() as pool:
            #########################################
            ##  Add new format identifiers here!   ##
            #########################################
            # fork here according to specified facility
            #  - conversion: what _utility.py function to call
            #  - parameters: parameters for the conversion function
            #     - path_output, dimension1, dimension2, overwrite_flag
            #     - more if needed, e.g. SP8 2-th correction value
            if source == 'APS':
                conversion = convert_frame_APS_Bruker
                parameters = [path_output, overwrite_flag]
            elif source == 'SP8':
                # check data collection timestamp
                with open(file_list[0], 'rb') as ofile:
                    year = int(re.search(b'(\d{4}):\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}', ofile.read(64)).group(1).decode())
                SP8_tth_corr = 0.0
                if year < 2019:
                    SP8_tth_corr = 4.8
                conversion = convert_frame_SP8_Bruker
                parameters = [path_output, SP8_tth_corr, overwrite_flag]
            elif source == 'DLS':
                conversion = convert_frame_DLS_Bruker
                parameters = [path_output, overwrite_flag]
            else:
                self.popup_window('Information', 'Unknown facility!', '')
                return
            
            # hide button, show bar
            self.tb_convert.hide()
            self.pb_convert.show()
            
            # feed the pool
            results = []
            for fname in file_list:
                pool.apply_async(conversion, args=[fname] + parameters, callback=results.append)
            
            # update the progress
            _todo = len(file_list)
            while len(results) != _todo:
                progress = float(len(results)) / float(_todo) * 100.0
                self.pb_convert.setValue(progress)
                # use processEvents() to keep track of the loop / update the GUI
                # or: try to thread it -> in the future.
                QtWidgets.QApplication.processEvents()
                if len(results) > 0:
                    # conversion in progress
                    self.statusBar.show()
                    self.status.setText('{}'.format(os.path.basename(file_list[len(results)-1])))
            # exit and wait
            pool.close()
            pool.join()
            # conversion finished
            # show button, hide bar
            self.statusBar.hide()
            self.pb_convert.hide()
            self.tb_convert.show()
            # tell me that you are done
            self.popup_window('Information', 'Successfully converted {} images!'.format(np.count_nonzero(results)), '')
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
