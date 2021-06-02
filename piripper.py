#!/usr/bin/python3

import time
import sys
import os
import subprocess
import fcntl

# Configurable things, these things may need to change on different systems or
# versions of the pi OS

CD_DRIVE_DEVICE_PATH = "/dev/sr0"
RIPIT_BIN_PATH = "ripit"
RED_LED_DEVICE_PATH = "/sys/class/leds/led1"
GREEN_LED_DEVICE_PATH = "/sys/class/leds/led0"
RIPIT_OUTPUT_PATH = "/home/pi/ripit_output"
LOCK_FILE_PATH = "/home/pi/.piripper.lock"
MP3_BITRATE_KPBS = 320

# End of configurable things

green_led_path = GREEN_LED_DEVICE_PATH + "/trigger"
red_led_path = RED_LED_DEVICE_PATH + "/trigger"

# Constants copied from https://github.com/torvalds/linux/blob/master/include/uapi/linux/cdrom.h
IOCTL_CDROM_DRIVE_STATUS = 0x5326
IOCTL_RESULT_CDS_DISC_OK = 4


def run_shell_cmd(cmd):
    result = subprocess.Popen(cmd.split())
    output = result.communicate()[0]
    retcode = result.returncode

    return output, retcode

def wait_for_cd_loaded(poll_delay_secs=1):
    ret = IOCTL_RESULT_CDS_DISC_OK + 1
    fd = os.open(CD_DRIVE_DEVICE_PATH, os.O_RDONLY | os.O_NONBLOCK)

    while ret != IOCTL_RESULT_CDS_DISC_OK:
        ret = fcntl.ioctl(fd, IOCTL_CDROM_DRIVE_STATUS)
        time.sleep(poll_delay_secs)

    os.close(fd)
    return ret

def eject_drive():
    run_shell_cmd("eject %s" % CD_DRIVE_DEVICE_PATH)

def initialize_leds():
    for p in [green_led_path, red_led_path]:
        with open(p, "w") as fh:
            fh.write("gpio")

def set_led_state(led_dev_path, state):
    with open(led_dev_path + "/brightness", "w") as fh:
        fh.write("1" if state else "0")

def set_green_led_state(state):
    set_led_state(GREEN_LED_DEVICE_PATH, state)

def set_red_led_state(state):
    set_led_state(RED_LED_DEVICE_PATH, state)

def rip_inserted_cd():
    cmd_string = ("%s --device %s --bitrate %d --threads 4 --nointeraction --playlist 0 --outputdir %s" %
                  (RIPIT_BIN_PATH, CD_DRIVE_DEVICE_PATH, MP3_BITRATE_KPBS, RIPIT_OUTPUT_PATH))


    set_green_led_state(True)
    text, retcode = run_shell_cmd(cmd_string)
    set_green_led_state(False)

    if retcode != 0:
        set_red_led_state(True)

def main():
    initialize_leds()
    set_green_led_state(False)
    set_red_led_state(False)

    # Eject drive initially so disc can be inserted
    eject_drive()

    while True:
        wait_for_cd_loaded()

        # Rip tracks from CD and convert to mp3
        rip_inserted_cd()

        # Eject disc after ripping is done
        eject_drive()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        os.remove(LOCK_FILE_PATH)
        set_green_led_state(False)
        set_red_led_state(False)
