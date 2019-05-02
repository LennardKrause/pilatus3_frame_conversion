import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, PathPatch
from PyQt5 import QtCore
import os, sys, logging
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from _classes_DraggableObject import DraggableObject
from _utility import *

class FrameView(FigureCanvas):
    '''
    
    '''
    mask_written = QtCore.pyqtSignal(str)
    frame_loaded = QtCore.pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        logging.info(self.__class__.__name__)
        '''
         
        '''
        self.fig = Figure()
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig.add_subplot(111)
        # turn off the white background
        self.fig.patch.set_visible(False)
        # turn off the axis
        self.axes.set_axis_off()
        # set margins to zero
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        # matplotlib imshow toolbar
        self.toolbar = NavigationToolbar(self, parent=None)
        # pan/zoom/home functions are not used
        self.toolbar.hide()
        # allow catching of event.key information
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        # init vars
        self.has_patches = False
        self.masks = {}
        self.frame_rows = 0
        self.frame_cols = 0
        self.rect_width = 12
        self.rect_offset = 25
        self.elli_width = 25
        self.elli_height = 25
        self.cmap_min = 0
        self.cmap_max = 25
        self.cmap = 'hot'
        self.showFrame = None
    
    def frame_update(self, fPath, rows, cols, offset, rFunct, rotate=True):
        logging.info(self.__class__.__name__)
        # initial frame dimensions
        # if the frame dimensions change we need to clear/redraw the figureCanvas
        # as set_data would distort the frame
        if not self.frame_rows == rows or not self.frame_cols == cols:
            self.frame_rows = rows
            self.frame_cols = cols
            self.showFrame = None
            if self.axes:
                self.axes.clear()
        
        _, data = rFunct(fPath, self.frame_rows, self.frame_cols, offset, np.uint32)
        # get the frame saint ready 
        # - multiple of 128x128 pixels
        # - pad with zeros
        self.data, offset_rows, offset_cols = pilatus_pad(data)
        
        # the frame has to be rotated by 90 degrees
        if rotate:
            self.data = np.rot90(self.data, k=1, axes=(1, 0))
        
        # send frame dimensions (w,h) to main window
        # - adjust/fix the widget size
        self.frame_loaded.emit(*np.flip(self.data.shape))
        
        if self.showFrame == None:
            self.showFrame = self.axes.imshow(self.data, interpolation='none')
        else:
            self.showFrame.set_data(self.data)
        
        self.showFrame.set_cmap(self.cmap)
        self.showFrame.set_clim(vmin=self.cmap_min, vmax=self.cmap_max)
        
        self.add_patches_and_draw(fPath)
        
    def add_patches_and_draw(self, fPath):
        logging.info(self.__class__.__name__)
        '''
         NOTE TO MATPLOTLIB PATCHES COLOR
         Turns out, you need to call axes.add_artist()
         to make the color specifications work
         Thanks to:
         https://stackoverflow.com/questions/10550477/how-do-i-set-color-to-rectangle-in-matplotlib
        '''
        if not self.has_patches:
            self.has_patches = True
            rows, cols = self.data.shape
            
            self.patch_rect = self.axes.add_patch(Rectangle(np.array([cols//2 - self.rect_width//2, -self.rect_offset]), self.rect_width, rows//2 +self.rect_offset, gid='rect', zorder=2))
            self.draggable_rect = DraggableObject(self.patch_rect)
            self.draggable_rect.connect()
            self.axes.add_artist(self.patch_rect)
            
            self.patch_elli = self.axes.add_patch(Ellipse(np.array([cols//2, rows//2]), self.elli_width, self.elli_height, gid='elli', zorder=3))
            self.draggable_elli = DraggableObject(self.patch_elli)
            self.draggable_elli.connect()
            self.axes.add_artist(self.patch_elli)
        
        if fPath in list(self.masks):
            self.update_patch_rect(self.patch_rect, *self.masks[fPath][self.patch_rect.get_gid()])
            self.update_patch_elli(self.patch_elli, *self.masks[fPath][self.patch_elli.get_gid()])
            self.patch_rect.set_color((0.,1.,0.75,.75))
            self.patch_elli.set_color((0.,1.,0.75,.75))
        else:
            self.patch_rect.set_color((0.,1.,1.,.75))
            self.patch_elli.set_color((0.,1.,1.,.75))
            
        self.draw()
    
    def reset_patches(self):
        logging.info(self.__class__.__name__)
        rows, cols = self.data.shape
        self.update_patch_rect(self.patch_rect, [cols//2 - self.rect_width//2, -self.rect_offset], self.rect_width, rows//2 +self.rect_offset, 0)
        self.update_patch_elli(self.patch_elli, [cols//2, rows//2], self.elli_width, self.elli_height, 0)
        self.draw()
        
    def update_patch_rect(self, aPatch, xy, w, h, a):
        logging.info(self.__class__.__name__)
        aPatch.set_xy(xy)
        aPatch.set_height(h)
        aPatch.set_width(w)
        aPatch.angle = a
        
    def update_patch_elli(self, aPatch, xy, w, h, a):
        logging.info(self.__class__.__name__)
        aPatch.set_center(xy)
        aPatch.height = h
        aPatch.width = w
        aPatch.angle = a
        
    def transform_and_clip(self, p):
        logging.info(self.__class__.__name__)
        '''
         
        '''
        # get the 'actual' rectangle path and not the 'box'
        path = p.get_path()
        transform = p.get_transform()
        path = transform.transform_path(path)
        p = PathPatch(path)
        # draw empty picture
        im = plt.imshow(np.zeros(self.data.shape, dtype=np.int8))#, zorder=n)
        # clip to path
        im.set_clip_path(p)
    
    def convert_patches_to_mask(self, fPath, mPath):
        logging.info(self.__class__.__name__)
        '''
         
        '''
        fstem, fname = os.path.split(fPath)
        # this figure has to be fixed size
        fig = plt.figure(figsize=(np.flip(self.data.shape)), dpi=1)
        axes = fig.add_subplot(111)
        # turn off the white background
        fig.patch.set_visible(False)
        # turn off the axis
        axes.set_axis_off()
        fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        self.transform_and_clip(self.patch_rect)
        self.transform_and_clip(self.patch_elli)
        # render the image
        fig.canvas.draw()
        # translate figure to np.array
        data_stacked = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.int8).reshape(self.data.shape[0], self.data.shape[1], 3)
        # continue with first layer
        data_clip = data_stacked[:,:,0]
        # set negatives to zero
        data_clip[data_clip < 0] = 0
        # set patch area to minus one
        data_clip[data_clip > 0] = -1
        # the dead areas are flagged -1
        self.data[self.data >=  0] = 1
        self.data[self.data < 0] = -1
        # combine data and patches
        data = self.data + data_clip
        data[data < 0] = 0
        
        # calculate detector pixel per cm
        # this is normalized to a 512x512 detector format
        # PILATUS3-1M pixel size is 0.172 mm 
        pix_per_512 = round((10.0 / 0.172) * (512.0 / ((self.frame_rows + self.frame_cols) / 2.0)), 6)
        
        # default Bruker header
        header = bruker_header()
        
        # fill known header items
        header['NCOLS']      = [self.data.shape[1]]             # Number of pixels per row; number of mosaic tiles in X; dZ/dX
        header['NROWS']      = [self.data.shape[0]]             # Number of rows in frame; number of mosaic tiles in Y; dZ/dY value
        header['CCDPARM'][:] = [0.00, 1.00, 1.00, 1.00, 1169523]
        header['DETPAR'][:]  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        header['DETTYPE'][:] = ['PILATUS3-1M', pix_per_512, 0.00, 0, 0.001, 0.0, 0]
        header['SITE']       = ['']                             # Site name
        header['MODEL']      = ['Synchrotron']                  # Diffractometer model
        header['TARGET']     = ['']                             # X-ray target material)
        header['USER']       = ['USER']                         # Username
        header['SOURCEK']    = ['?']                            # X-ray source kV
        header['SOURCEM']    = ['?']                            # Source milliamps
        header['FILENAM']    = [fname]
        header['TYPE']       = ['ACTIVE MASK']                  # String indicating kind of data in the frame
        header['NFRAMES']    = ['?']                            # Number of frames in the series
        header['NEXP'][2]    = 0
        header['MAXXY']      = np.array(np.where(data == data.max()), np.float)[:, 0]
        header['MAXIMUM']    = [np.max(data)]
        header['MINIMUM']    = [np.min(data)]
        header['NCOUNTS'][:] = [data.sum(), 0]
        header['NOVER64'][:] = [data[data > 64000].shape[0], 0, 0]
        header['NSTEPS']     = [1]                              # steps or oscillations in this frame
        header['NPIXELB'][:] = [1, 1]                           # bytes/pixel in main image, bytes/pixel in underflow table
        header['COMPRES']    = ['NONE']                         # compression scheme if any
        header['TRAILER']    = [0]                              # byte pointer to trailer info
        header['LINEAR'][:]  = [1.00, 0.00]     
        header['PHD'][:]     = [1.00, 0.00]
        header['OCTMASK'][:] = [0, 0, 0, 1023, 1023, 2046, 1023, 1023]
        header['DISPLIM'][:] = [0.0, 63.0]                      # Recommended display contrast window settings
        
        # write the frame
        write_bruker_frame(mPath, header, data)
        # store masks in a dict, saving pos and shape of the obj
        # retrieve on switch, changing color to green from light blue
        self.masks[fPath] = {}
        self.masks[fPath]['rect'] = [self.patch_rect.get_xy(),
                                     self.patch_rect.get_width(),
                                     self.patch_rect.get_height(),
                                     self.patch_rect.angle]
        self.masks[fPath]['elli'] = [self.patch_elli.get_center(),
                                     self.patch_elli.width,
                                     self.patch_elli.height,
                                     self.patch_elli.angle]
        self.mask_written.emit(fPath)
        self.add_patches_and_draw(fPath)
