import logging
import numpy as np
class DraggableObject:
    '''
     based on:
     draggable rectangle with the animation blit techniques;
     see http://www.scipy.org/Cookbook/Matplotlib/Animations
    '''
    lock = None# only one can be animated at a time
    def __init__(self, obj):
        logging.info(self.__class__.__name__)
        self.obj = obj
        self.press = None
        self.background = None
        # rectangle patch offset: displace the rectangle outside the
        # frame area to avoid unwanted active areas when tilting
        # self.rect_o: defined in _classes_FrameView.FrameView
        if self.obj.get_gid() == 'rect':
            _, self.rect_o = self.obj.get_xy()
        
    def connect(self):
        logging.info(self.__class__.__name__)
        'connect to all the events we need'
        self.cidpress = self.obj.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.obj.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.obj.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
            
    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.obj.axes:
            return
        
        if DraggableObject.lock is not None:
            return
        
        contains, attrd = self.obj.contains(event)
        if not contains:
            return
        
        if self.obj.get_gid() == 'rect':
            x0, y0 = self.obj.get_xy()
            w0 = self.obj.get_width()
            h0 = self.obj.get_height()
            a0 = self.obj.angle
            if event.dblclick:
                if y0 == self.rect_o:
                    self.obj.set_y(self.obj.figure.canvas.height() - self.rect_o)
                else:
                    self.obj.set_y(self.rect_o)
                self.obj.angle = 180 - a0
                self.obj.figure.canvas.draw()
                return
        elif self.obj.get_gid() == 'elli':
            x0, y0 = self.obj.get_center()
            w0 = self.obj.width
            h0 = self.obj.height
            a0 = self.obj.angle
        else:
            return
            
        self.press = x0, y0, w0, h0, a0, event.xdata, event.ydata
        DraggableObject.lock = self

        # draw everything but the selected object and store the pixel buffer
        canvas = self.obj.figure.canvas
        axes = self.obj.axes
        self.obj.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(axes.bbox)

        # now redraw just the object
        axes.draw_artist(self.obj)
        
        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if DraggableObject.lock is not self:
            return
        
        if event.inaxes != self.obj.axes:
            return
        
        x0, y0, w0, h0, a0, xp, yp = self.press
        xe = event.xdata
        ye = event.ydata
        ke = event.key
        be = event.button
        gid = self.obj.get_gid()
        
        if be == 1 and not (ke == 'control' or ke == 'shift'):
            if gid == 'elli':
                self.obj.set_center([x0 + xe - xp, y0 + ye - yp])
            elif gid == 'rect':
                self.obj.set_x(x0 + xe - xp)
                self.obj.set_height(h0)
                self.obj.angle = a0
        elif be == 2 or ke == 'shift':
            if gid == 'rect':
                self.obj.angle = np.rad2deg(np.arctan2(x0 - xe, ye - y0))
            elif gid == 'elli':
                self.obj.angle = np.rad2deg(-np.arctan2(x0 - xe, y0 - ye))
        elif be == 3 or ke == 'control':
            if gid == 'rect':
                self.obj.set_width(w0 + xe - xp)
                self.obj.set_height(h0 + ye - yp)
            elif gid == 'elli':
                # length: np.sqrt(x.dot(x))
                self.obj.width = w0 + xe - xp
                self.obj.height = h0 + ye - yp
                if self.obj.width > self.obj.height:
                    self.obj.width = self.obj.height
            
        canvas = self.obj.figure.canvas
        axes = self.obj.axes
        
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.obj)

        # blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_release(self, event):
        'on release we reset the press data'
        if DraggableObject.lock is not self:
            return

        self.press = None
        DraggableObject.lock = None

        # turn off the rect animation property and reset the background
        self.obj.set_animated(False)
        self.background = None

        # redraw the full figure
        self.obj.figure.canvas.draw()

    def disconnect(self):
        logging.info(self.__class__.__name__)
        'disconnect all the stored connection ids'
        self.obj.figure.canvas.mpl_disconnect(self.cidpress)
        self.obj.figure.canvas.mpl_disconnect(self.cidrelease)
        self.obj.figure.canvas.mpl_disconnect(self.cidmotion)
