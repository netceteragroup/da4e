# Distribution Assembler for Eclipse

This project provides a distribution assembly script plus skeletons, examples and documentation for concrete distributions. It requires customization and does not work out of the box. 

# Quick Start

### Platform

From a technical point of view, the script should work on all platforms that can run Python and Eclipse. However, the script has so far only been tested and used on Linux and some extra work might be required to get it running on other platforms.
The following commands must be available from $PATH:

- Python >= 2.7
- unzip and zip (if creating distributions for Windows)
- tar (if creating distributions for Linux or OS X)
- convert (from ImageMagick)
- merge (from ImageMagick) 

### Eclipse Runtime Environment
A working Eclipse instance (standard SDK is OK) >= 3.6. Please note, this is the instance that executes the installer and not the installation target. 

#Installation
This project provides a distribution assembly script plus skeletons, examples and documentation for concrete distributions. It requires customization and does not work out of the box.

The core installation is therefore rather simple:

1. Make sure all your prerequisites are met
2. Export the source of this project 
