PiRipper
########

PiRipper is a python script that allows you to turn a Raspberry Pi and any external
USB optical drive into an automatic CD-ripping machine. As soon as you put in a disc,
the Raspberry Pi will rip all audio tracks and copy the resulting mp3 files to whatever
USB storage device is connected (if no storage is connected, the ripped files will just
stay on the Pi's internal storage, and the next time a CD is ripped with a connected storage
device, then all un-copied mp3 files on the Pi's internal storage will be copied over).

Disclaimer
----------

I've only tested this on a Raspberry Pi 3B+. It can probably be made to work on other
Raspberry Pi models, but you may have to go in and tweak some things in the piripper.py script.

Getting Started
###############

First things first, you need Raspberry Pi with an optical drive connected via USB.
Make sure your optical drive appears as ``sr0``. If for some reason your optical
drive appears as a different device name, you may have to modify the
``CD_DRIVE_DEVICE_PATH`` variable at the top of the ``piripper.py`` file to match
your device name.

Download this repo from github to your Raspberry Pi
---------------------------------------------------

::

    git clone https://github.com/eriknyquist/piripper /home/pi/piripper


Install required packages
-------------------------

::

    sudo apt-get install ripit lame eject


Install piripper systemd service
--------------------------------

This will set up piripper to start automatically whenever the Pi boots and keep
running in the background

::

    sudo cp /home/pi/piripper/piripper.service /etc/systemd/system
    sudo systemctl enable piripper.service


Start the piripper service
--------------------------

After enabling, the piripper service will start automatically when the Pi next boots,
but you can start it right away like this:

::

   sudo systemctl start piripper.service

When the piripper service is running, any time an audio CD-ROM is inserted into
the connected optical drive, all tracks will automatically ripped and converted
to 320kpbs mp3 files. If there is a USB storage device connected, the mp3 files
will be copied there, otherwise the mp3 files will remain on the Pi's internal
storage until the next time a CD is ripped with a USB storage device connected.

piripper takes control of the built-in green and red LEDs on the Raspberry Pi.
while a CD ripping is in progress, the green LED will be lit.
When a CD ripping completes, the green LED will be turned off and the CD will be
ejected. If any errors occur that prevent piripper from doing what it wants to do,
the red LED will be lit.
