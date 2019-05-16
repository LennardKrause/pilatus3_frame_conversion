# pilatus3_frame_conversion

pilatus3-fc.py offers an easy-to-use GUI to convert Pilatus3 images to the Bruker .sfrm format and helps generating proper integration masks for the Bruker SAINT+ integration engine that is part of the [APEX3 Software](https://www.bruker.com/products/x-ray-diffraction-and-elemental-analysis/single-crystal-x-ray-diffraction/sc-xrd-software/overview/sc-xrd-software/apex3.html).

It is currently designed to convert data collected at the following facilities / beamlines:
  - [Advanced Photon Source](https://www.aps.anl.gov/) / 15ID-D
  - [SPring-8](http://www.spring8.or.jp/en/) / BL02B1
  - [Diamond Light Source](https://www.diamond.ac.uk/Home.html) / I19-1

## Requirements

### Bruker SAINT+ Integration Engine V8.35A or later
  - requirement that frames consist of multiples of 512 pixels has been lifted
  - any frame size is now allowed

### Python 3.5 or later

### Libraries (tested with):
  - [numpy (1.16.3)](https://www.numpy.org/)
  - [matplotlib (3.0.3)](https://matplotlib.org/)
  - [PyQt5 (5.12.2)](https://www.riverbankcomputing.com/software/pyqt/intro/)
