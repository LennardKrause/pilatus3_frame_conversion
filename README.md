# pilatus3_frame_conversion

pilatus3-fc.py offers an easy-to-use GUI to convert Pilatus3 images to the Bruker .sfrm format and helps generating proper integration masks for the Bruker integration engine SAINT.

It is currently designed to convert data collected at the following facilities / beamlines:
  - Advanced Photon Source / 15ID-D
  - SPring-8 / BL02B1
  - Diamond Light Source / I19-1

# Requirements

Bruker SAINT+ Integration Engine V8.35A
  - requirement that frames consist of multiples of 512 pixels has been lifted
  - any frame size is now allowed

Python > 3.5

Used libraries (tested with):
  - numpy (1.16.3) https://www.numpy.org/
  - matplotlib (3.0.3) https://matplotlib.org/
  - PyQt5 (5.12.2) https://www.riverbankcomputing.com/software/pyqt/intro/
