#!/usr/bin/python3

import time
import sys
import os
import subprocess
import datetime
import fcntl
import shutil
import logging


# Configurable things, these things may need to change on different systems or
# versions of the pi OS

CD_DRIVE_DEVICE_PATH = "/dev/sr0"
RIPIT_BIN_PATH = "ripit"
RED_LED_DEVICE_PATH = "/sys/class/leds/led1"
GREEN_LED_DEVICE_PATH = "/sys/class/leds/led0"
PIRIPPER_PATH = "/home/pi/.piripper"
LOCK_FILE_PATH = os.path.join(PIRIPPER_PATH, "lock")
RIPIT_OUTPUT_PATH = os.path.join(PIRIPPER_PATH, "ripit-output")
STORAGE_MOUNT_PATH = os.path.join(PIRIPPER_PATH, "usb-mount")
MP3_BITRATE_KPBS = 320

# End of configurable things


PIRIPPER_DIR_PREFIX = "piripper"
green_led_path = GREEN_LED_DEVICE_PATH + "/trigger"
red_led_path = RED_LED_DEVICE_PATH + "/trigger"

# Constants copied from https://github.com/torvalds/linux/blob/master/include/uapi/linux/cdrom.h
IOCTL_CDROM_DRIVE_STATUS = 0x5326
IOCTL_RESULT_CDS_DISC_OK = 4

logging.basicConfig(format="[%(asctime)-15s][%(module)s] %(message)s")
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
logger.setLevel(logging.INFO)


def run_shell_cmd(cmd):
    result = subprocess.Popen(cmd.split())
    output = result.communicate()[0]
    retcode = result.returncode

    return output, retcode

def wait_for_cd_loaded(poll_delay_secs=1):
    logger.info("waiting for a CD-ROM to be inserted...")
    ret = IOCTL_RESULT_CDS_DISC_OK + 1
    fd = os.open(CD_DRIVE_DEVICE_PATH, os.O_RDONLY | os.O_NONBLOCK)

    while ret != IOCTL_RESULT_CDS_DISC_OK:
        ret = fcntl.ioctl(fd, IOCTL_CDROM_DRIVE_STATUS)
        time.sleep(poll_delay_secs)

    os.close(fd)
    return ret

def eject_drive():
    logger.info("ejecting drive")
    run_shell_cmd("eject %s" % CD_DRIVE_DEVICE_PATH)

def initialize_leds():
    logger.info("turning LEDs off")
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

def fatal_error(msg):
    log_error(msg)
    set_green_led_state(False)
    set_red_led_state(True)

def rip_inserted_cd():
    dirname = PIRIPPER_DIR_PREFIX + "_" + datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    output_dir = os.path.join(RIPIT_OUTPUT_PATH, dirname)

    cmd_string = ("%s --device %s --bitrate %d --threads 4 --nointeraction --playlist 0 --outputdir %s" %
                  (RIPIT_BIN_PATH, CD_DRIVE_DEVICE_PATH, MP3_BITRATE_KPBS, output_dir))

    logger.info("ripping tracks to %s" % output_dir)
    set_green_led_state(True)
    text, retcode = run_shell_cmd(cmd_string)
    set_green_led_state(False)

    if retcode != 0:
        fatal_error("failed to start %s, ripit return code was %d" % (RIPIT_BIN_PATH, retcode))

def find_connected_storage():
    device_dir = "/dev"

    for fname in os.listdir(device_dir):
        if fname.startswith("sda") or fname.startswith("sdb"):
            end = fname[3:]

            if end == "":
                continue

            try:
                _ = int(end)
            except:
                continue
            else:
                return os.path.join(device_dir, fname)

    return None

def copy_files_to_storage():
    drivename = find_connected_storage()
    if drivename is None:
        # No connected USB drive, nothing to do
        logger.info("no external storage connected")
        return

    _, ret = run_shell_cmd("mount %s %s" % (drivename, STORAGE_MOUNT_PATH))
    if ret != 0:
        fatal_error("failed to mount %s, error: %d" % (drivename, ret))
        return

    for src in os.listdir(RIPIT_OUTPUT_PATH):
        if not src.startswith(PIRIPPER_DIR_PREFIX):
            continue

        # Destination dir already exists
        dstpath = os.path.join(STORAGE_MOUNT_PATH, src)
        if os.path.isdir(dstpath):
            continue

        srcpath = os.path.join(RIPIT_OUTPUT_PATH, src)

        logger.info("copying %s to %s" % (srcpath, RIPIT_OUTPUT_PATH))
        shutil.copytree(srcpath, dstpath)

        logger.info("deleting %s" % srcpath)
        shutil.rmtree(srcpath)

    _, ret = run_shell_cmd("umount %s" % drivename)
    if ret != 0:
        fatal_error("failed to unmount %s, error: %d" % (drivename, ret))

def main():
    initialize_leds()
    set_green_led_state(False)
    set_red_led_state(False)


    if os.path.isfile(LOCK_FILE_PATH):
        log.info("piripper is already running!")
        return

    with open(LOCK_FILE_PATH, 'w') as fh:
        pass

    if not os.path.isdir(STORAGE_MOUNT_PATH):
        os.makedirs(STORAGE_MOUNT_PATH)

    if not os.path.isdir(RIPIT_OUTPUT_PATH):
        os.makedirs(RIPIT_OUTPUT_PATH)

    # Eject drive initially so disc can be inserted
    eject_drive()

    while True:
        wait_for_cd_loaded()

        # Rip tracks from CD and convert to mp3
        rip_inserted_cd()

        # Copy files to USB drive, if any is inserted
        copy_files_to_storage()

        # Eject disc after ripping is done
        eject_drive()

    os.remove(LOCK_FILE_PATH)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        os.remove(LOCK_FILE_PATH)
        set_green_led_state(False)
        set_red_led_state(False)
