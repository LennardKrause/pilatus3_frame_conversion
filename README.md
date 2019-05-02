# frame_conversion
Pil1M-FC.py converts Pilatus3 images to the Bruker .sfrm format. It is currently designed to convert data collected at Advanced Photon Source / 15ID-D, SPring-8 / BL02B1 or Diamond Light Source / I19-1.

IMPORTANT
Bruker is not associated with this software and will not support this. Please direct any queries to lkrause@chem.au.dk

General remark: Tooltips are used extensively throughout the program.
Use the filebrowser to navigate to the frame folder, if valid frames are found the program will indicate it by showing the number of frames on the Convert X Frames button at the bottom (it may take a while to read a folder containing a large number of frames!). Next step is to specify the facility the frames were collected at (indicated by a green text) and the output format (Bruker or RAxis). For SPring-8 data a 2-theta correction might be needed because the goniometer was misaligned (pre January 2019 data), this value can be changed by clicking the edit button, however, it is strongly recommended to leave it at the pre-set value of 0.0%. The output folder line (Output Directory) can be edited freely and non-existing folders will be created recursively. By default, the output directory is linked to the input directory and a suffix is added and updated automatically (_sfrm for Bruker and _img for RAxis). If the link? box is unchecked the input and output fields (Input and Output Directory) can be chosen separately using the filebrowser, a green ring indicates the currently active field. From the frame name, the program tries to guess the facility. Here, any_name_rrr_ffff.tif belongs to 15ID-D@APS and any_name_rrfff.tif comes from BL02B1@SPring-8, the output name is always any_name_rr_ffff.sfrm (Bruker), where r is the run and f is the frame number, respectively. For the conversion of APS data only the .tif files are required as all information is either predetermined or written in the frame header. For SPring-8 data conversion, the experimental information (e.g. Goniometer angles, exposure time) is stored in .inf files. These files are assumed to be provided along with the .tif files and are stored in the same folder as the frames.
Draw integration masks
Once a folder with valid frames is selected, the Draw Beamstop tab becomes available. The filebrowser is disabled during conversion, however, the drawing tab is not. It is recommended to start the frame conversion prior to drawing the mask as it assures that the mask files are stored in the same folder as the converted frames. The image is shown in native resolution, use the scroll bars to navigate to the beamstop shadow. Drag and adjust the patches (rectangle, circle) to where they are needed. The intrinsic dead areas of the Pilatus3 detector and dead pixels are masked automatically. If a patch is not needed, simply adjust its size and put it onto a dead area. The conversion process can have been started while drawing the masks. General usage:
 Left click on either patch to move it
 Right click (Control) Circle to adjust its size
 Right click (Control) Rectangle adjusts angle
 Middle click (Shift) Rectangle adjusts size
 Use the slider to adjust the contrast
 Use the arrows to switch between runs
 Save Mask to save the current mask
The masks are saved to Output Directory (once Save Mask is pressed) and follow a name convention internally used by the data reduction software SAINT so no further steps are needed in order for SAINT to use the masks!
