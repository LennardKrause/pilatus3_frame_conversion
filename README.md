# pilatus3_frame_conversion

pilatus3-fc.py offers an easy-to-use GUI to convert Pilatus3 images to the Bruker *.sfrm* format and helps generating proper integration masks for the Bruker SAINT+ integration engine that is part of the [APEX3 Software](https://www.bruker.com/products/x-ray-diffraction-and-elemental-analysis/single-crystal-x-ray-diffraction/sc-xrd-software/overview/sc-xrd-software/apex3.html).

It is currently designed to convert data collected at the following synchrotron facilities / beamlines:
  - [Advanced Photon Source](https://www.aps.anl.gov/) / 15ID-D
  - [SPring-8](http://www.spring8.or.jp/en/) / BL02B1
  - [Diamond Light Source](https://www.diamond.ac.uk/Home.html) / I19-1

## Requirements

### Bruker SAINT+ Integration Engine V8.35A or later
  - requirement that frames consist of multiples of 512 pixels has been lifted
  - any frame size is now allowed

### [Python](https://www.python.org/) 3.5 or later

### Libraries (tested with):
  - [numpy (1.16.3)](https://www.numpy.org/)
  - [matplotlib (3.0.3)](https://matplotlib.org/)
  - [PyQt5 (5.12.2)](https://www.riverbankcomputing.com/software/pyqt/intro/)

## Program Layout
Filebrowser / Image Conversion - Tab | Draw Beamstop - Tab
------------------------------------ | -------------------
![img_gui_convert](https://user-images.githubusercontent.com/48315771/57973478-82a81c00-79a9-11e9-88e6-2addb86d70c7.png) | ![img_gui_draw](https://user-images.githubusercontent.com/48315771/57973484-9a7fa000-79a9-11e9-9144-379d21f10f01.png)

### Filebrowser / Image Conversion
Use the filebrowser to navigate to the frame folder, it may take a while to read a folder containing a large number of frames! The output folder line (*Output Directory*) can be edited freely and non-existing folders will be created recursively. By default, the output directory is linked to the input directory and a suffix (*_sfrm*) is added automatically. If the *link?* box is unchecked the input and output fields (*Input* and *Output Directory*) can be selected manually to be controlled by the filebrowser, a green ring indicates the currently active field. The *ow* box toggles between overwrite/skip if the converted frame is already existing.

### Draw Beamstop
Once a folder with valid frames is selected, the *Draw Beamstop* tab becomes available. The filebrowser is disabled during conversion, however, the drawing tab is not. It is recommended to start the frame conversion prior to drawing masks as it assures that the mask files are stored in the same folder as the converted frames. The image is shown in native resolution, use the scroll bars to navigate to the beamstop shadow. Drag and adjust the patches (rectangle, ellipse) to where they are needed. The intrinsic dead areas of the Pilatus3 detector and bad pixels are masked automatically. If a patch is not needed, simply adjust its size and put it onto a dead area. General usage:
 - *Left* click/drag on either patch to move it
 - *Right* click/drag (hold Control) to adjust shape and size
 - *Middle* click/drag (hold Shift) Rectangle adjusts angle
 - *Double click* on Rectangle to flip up/down
 - Use the *Intensity* slider to adjust the contrast
 - Use the *arrow keys* to switch between runs
 - Press *Save Mask* to save the current mask
 - *Reset Mask* resets both patches to their initial states

The masks are saved to *Output Directory* (once Save Mask is pressed) and follow a name convention internally used by SAINT so no further steps are needed in order to use the masks!
