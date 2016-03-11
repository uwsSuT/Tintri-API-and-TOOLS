#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    tintri_flr.py
    ~~~~~~~~~~~~~~~~~~~~~~~~

    CLI programm to Map and Unmap a Tintri Snapshot to a virtual LINUX machine

    Requirements:
        The programm needs "root" rights or "sudo" to run.
        This is needed because it uses the commands "mount" and "unmount".

        The Tintri http_api is also needed!

    Functionality:

        First of all the programm let you choose the vmware virtual machine name of
        your LINUX machine.
        After that you will get a list of all usable Snapshots for this machine.
        The Snapshot-disks will be mapped to the running system.

        After the "mapping" you can step into the Snapshot partitions and copy out the
        "old" data.
        The programm generates a MountPoint for each partition in the
        "TINTRI_RECOVER_DIR" (You can define this directory further down.
    
        The needed status information for a successfull unmapping is stored in
        the directory which is defined in the variable "dbg_path".

    Syntax:
        A complete Syntax information and all options are listet if you call the
        the "usage" of the command itself

        use: tintri_flr.py -?


    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

#===============================================================================
# Changeable Part
#===============================================================================

TINTRI_RECOVER_DIR = "/tintri_recover"
dbg_path = "/root/.tintri"

#===============================================================================
# END OF user changeable Part
#===============================================================================

#
# uws: 01.12.2015
# File Level Recovery Support for Tintri FLR Snapshot Feature
#
# uws: 07.03.2016
#    added Tintri-HTTP-API calls with the schtob/tintri/http_api library
#
#    New Functionality:
#
#    now the script asks for the virtual machine name, if the name is not found
#    in the virtual machine name list.
#
#    the scripts lists the tintri snapshots and askes which one should be
#    restored for FLR.
#
#    the reset Option removes the mounts and after that it removes the
#    synced snapshot-disks from the VM
#
import sys, os
try:
    # check if the schtob/tintri api lib is installed
    from schtob.tintri_http_api import TFilers
except:
    # check if this is a copy from GitHub without installation
    if os.path.isdir('../src/schtob'):
        sys.path.append('../src')
        from schtob.tintri_http_api import TFilers
    else:
        print "Installation Error: Couln't find the schtob Tintri API Lib"
        sys.exit(1)

import getopt, pickle
from os.path import join, basename, islink
from subprocess import Popen, PIPE
from time import strftime, localtime

from schtob.tintri_http_api import constants
from schtob.tintri_http_api import errors

Version = "1.1.0"

DISK_BY_PATH = "/dev/disk/by-path"
SCSI_SEARCH_PATH = "/sys/class/scsi_host"
MOUNT = "/bin/mount"
UMOUNT = "/bin/umount"
FDISK = "/sbin/fdisk -l"
PING = '/bin/ping'

first_fdisk_file = join(dbg_path, 'first_fdisk_info.pickle')

verbose = 1
dbg_fd = None

def get_disk_mnt_info():
    """
        Get partition infos for the actual visible disks
    """

    part_info = {}

    #
    # get the mount information for the disk partitions
    #
    proc = Popen(MOUNT,
        stdin = PIPE,
        stdout = PIPE,
        stderr = PIPE,
        shell = True)

    for l in proc.stdout:
        if verbose > 2:
            print "l: %s" % l.strip()
        parms = l.split()
        if parms[0].find('/dev/') == 0:
            part_info[basename(parms[0])] = {'mnt_path' : parms[2]}

    if not os.path.exists(DISK_BY_PATH):
        print "ERROR: couldn't find directory \'%s\'" % DISK_BY_PATH
        sys.exit(5)
    for part in os.listdir(DISK_BY_PATH):
        fname = join(DISK_BY_PATH, part)
        if islink(fname):
            dev = basename(os.readlink(fname))
            if dev in part_info.keys():
                part_info[dev]['disk_path'] = part 
        else:
            print "ERROR: disk_path isn't a symbolic link: \'%s\'" % fname
            sys.exit(6)
    if verbose > 1:
        print part_info
    return part_info

def get_fdisk_info(dbg_fd, old_info=None):
    """
        Get FDISK info for machine
    """

    fdisk_info = {}
    proc = Popen(FDISK,
        stdin = PIPE,
        stdout = PIPE,
        stderr = PIPE,
        shell = True)

    for l in proc.stdout:
        if verbose > 1:
            print "fdisk: %s" % l.strip()

        dbg_fd.write(l)

        if l.find('Disk') == 0 and '/dev' in l:
            # new Disk Information
            parms = l.split()
            disk = basename(parms[1].strip(':'))

            if old_info and disk in old_info:
                old_disk = True # Disk Info exists and should not be added
                                # into the "new" dict
                continue
            else:
                old_disk = False
            fdisk_info[disk] = { 'size' : "%s %s" % (
                                                parms[2], parms[3].strip(',')),
                                 'partitions' : [],
                               }
        elif l.find('/dev/') == 0:
            if old_disk:
                continue
            boot = False
            parms = l.split()
            if parms[1] == '*': # boot flag
                second_param = 2
                boot = True
            else:
                second_param = 1
            part_info = { 'name' : basename(parms[0]),
                          'boot' : boot,
                          'start': parms[second_param],
                          'end'  : parms[second_param+1],
                        }
            fdisk_info[disk]['partitions'].append(part_info)
        else:
            continue

    if verbose > 1:
        print """fdisk_info: 
    %s """ % fdisk_info

    return fdisk_info


def search_for_new_disks():
    """
        send scsi search command to find new disks
    """
    for d in os.listdir(SCSI_SEARCH_PATH):
        scan_file = join(SCSI_SEARCH_PATH, d, "scan")
        cmd = "echo \"- - -\" >%s" % scan_file
        if verbose > 1:
            print "search_for_new_disks: cmd : %s" % cmd
        os.system(cmd)

def init_env(quiet=False):
    """
        initialize dbg area in "root" dir
    """
    global dbg_fd

    first_fdisk = None
    mnt_info = None
    filername = None
    vm_name = os.uname()[1]
    if not 'linux' in sys.platform.lower():
        print "ERROR: this script is only usable on a LINUX system"
        sys.exit(99)

    if not os.path.isdir(dbg_path):
        os.makedirs(dbg_path)

    dbg_file = join(dbg_path, 'flr.dbg')
    dbg_fd = open(dbg_file, 'w')
    dbg_fd.write("""
================================================================================
    Start of script: %s    Version. %s
    """ % (strftime("%x %X "), Version))

    cache_info = {}
    if os.path.exists(first_fdisk_file):
        msg = """
    INFO: orig_fdisk info allready exists! I will use this \'old\' info
              """
        dbg_fd.write("%s\n" % msg)
        if verbose and not quiet:
            print msg

        fd = open(first_fdisk_file, 'r')
        pic = pickle.Unpickler(fd)
        cache_info['first_fdisk'] = pic.load()
        cache_info['mnt_info'] = pic.load()
        cache_info['filername'] = pic.load()
        cache_info['vm_name'] = pic.load()
        cache_info['active'] = pic.load()
        fd.close()
        dbg_fd.write("""OLD fdisk info:
    %s 
    \n""" % first_fdisk)

    return cache_info


def write_first_fdisk(first_fdisk, mnt_info, filername=None, vm_name=None,
                                                                active=False):
    """
        Write the First fdisk information into a python pickle file
    """
    fd = open(first_fdisk_file, 'w')
    pic = pickle.Pickler(fd)
    pic.dump(first_fdisk)
    pic.dump(mnt_info)
    pic.dump(filername)
    pic.dump(vm_name)
    pic.dump(active)
    fd.close()


def mount_snap_disks(first_disk, new_disk, mnt_info):
    """
        Mount the new found partitions on "recover" paths
    """
    global TINTRI_RECOVER_DIR
    # Plausi
    if not len(first_disk.keys()) == len(new_disk.keys()):
        print """ERROR: Number of disks before snapshot Recover is not equal the
    number of the newly found disks:
        Nr of primary disks    : %s 
        Nr of new Disks        : %s
    """ % (len(first_disk.keys()), len(new_disk.keys()))
        sys.exit(8)

    for disk in first_disk:
        for part in first_disk[disk]['partitions']:
            for ndisk in new_disk:
                if first_disk[disk]['size'] == new_disk[ndisk]['size'] and\
                   len(first_disk[disk]['partitions']) == \
                                        len(new_disk[ndisk]['partitions']):
                    # OK Size and nr. of partitions is equal search the
                    # correct partition and mount it
                    for npart in new_disk[ndisk]['partitions']:
                        if part['boot'] == npart['boot'] and \
                           part['start'] == npart['start'] and \
                           part['end'] == npart['end']:
                            if part['name'] not in mnt_info:
                                # swap or other not mounted partition
                                continue
                            mnt_name = mnt_info[part['name']]['mnt_path']
                            if mnt_name == '/':
                                mnt_name = 'SLASH'
                            mnt_dir = join(TINTRI_RECOVER_DIR,
                                                        basename(mnt_name))
                            cmd = "%s /dev/%s %s" % (MOUNT, npart['name'],
                                                                       mnt_dir)
                            if verbose:
                                print cmd
                            if not os.path.isdir(mnt_dir):
                                os.makedirs(mnt_dir)
                            os.system(cmd)

def reset(reset_all=False, log_lvl=None):
    """
        unmount the FLR Partitions
        reset_all : the pickle info will be removed too
    """
    if os.path.isdir(TINTRI_RECOVER_DIR):
        for fname in os.listdir(TINTRI_RECOVER_DIR):
            mnt_dir = join(TINTRI_RECOVER_DIR, fname)
            if os.path.ismount(mnt_dir):
                cmd = "%s -l %s" % (UMOUNT, mnt_dir)
                if verbose:
                    print "... " + cmd
                os.system(cmd)
            if reset_all:
                os.rmdir(mnt_dir)

    #
    # remove the mapped disks from virtual machine
    #
    try:
        cache_info = init_env(quiet=True)
    except:
        cache_info = {}

    if 'filername' in cache_info:
        if verbose > 0:
            print "... Remove mapped snapshot disks from virtual machine"

        try:
            filer = init_connection(cache_info['filername'], log_lvl)
            filer.del_flr_disks(cache_info['vm_name'])
        except:
            pass

    if reset_all:
        if os.path.exists(first_fdisk_file):
            os.unlink(first_fdisk_file)
        if os.path.exists(TINTRI_RECOVER_DIR):
            os.rmdir(TINTRI_RECOVER_DIR)
    else:
        write_first_fdisk(cache_info['first_fdisk'], cache_info['mnt_info'],
                cache_info['filername'], cache_info['vm_name'],
                active=False)
    sys.exit(0)

def ping(address):
    import subprocess

    args = [PING, '-c', '1', address]
    cmd = "%s -c 1 %s" % (PING, address)
    popen = subprocess.Popen(args,
            stdin  = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
    try:
        stdoutdata, stderrdata = popen.communicate()
    except:
        import traceback
        print cmd
        traceback.print_exc()
        return False

    if popen.returncode == 0:
        return True
    elif popen.returncode == 2:
        print("no response from %s" % address)
        return False
    else:
        print("ping to %s failed" % address)
    return False

def check_tfiler(filer):
    """
        Get the name of the Tintri Storage-System (Filername)
    """
    filername = None
    while not filername:
        if not filer:
            filer = raw_input("""Please enter the Tintri Storage-System-Name or address: """)
        if not filer or len(filer) == 0:
            print("No name given; Giving Up")
            sys.exit(255)

        if ping(filer):
            filername = filer
        else:
            print("""Could not reach Storage-System : \'%s\'
    """ % filer)
            filer = None

    return filername

def get_vm_name_from_user(filername, vm_name):
    """
        the hostname is not equivalent to the virtual machine name ask
        user for the virtual machine name
    """
    # get virtual machine names from filer
    vm_names = TFilers(filername).get_VMnames()
    if vm_name in vm_names:
        # given vm_name exists in the virtual machine names
        return vm_name

    while True:
        print """
Please select the virtual machine for the local host """
        i = 1
        for vm in vm_names:
            print "%3d : %s" % (i, vm)
            i += 1
        answ = raw_input("""
Please type the Nr. of the virtual machine name for the local host
[%s-%s] : """ % (1, i-1) )

        if not answ.isdigit():
            print "Input ERROR: Please type a number between 1 and %s" % i-1
        else:
            return vm_names[int(answ)-1]

def get_vm_snapshot(filername, vm_name):
    """
        get the snapshts for the virtual machine from the filer
        print the list of Snapshots and ask the user which snapshot
        should be used for the FLR 
    """
    snapshots = TFilers(filername).get_VMsnapshots(vmName = vm_name)
    if not snapshots:
        print "No Snapshots found for VM"
        sys.exit(0)
    # sort the snapshots 
    snapshots.sort(cmp=lambda x,y: cmp(x['createTime'], y['createTime']))

    attrs=constants.snap_default_attrs
    header = ['Nr.']
    for a in attrs:
        # pimp the header entrys
        if a == 'sizeChangedPhysicalMB':
            header.append('Changed MB')
        else:
            header.append(a)

    vm_length = len('vmName')
    rows = []
    nr = 1
    for snap in snapshots:
        row = [nr]
        for a in attrs:
            if a == 'createTime':
                # generate a date format
                row.append(strftime("%x %X", localtime(snap[a]/1000)))
            elif a == 'type':
                # the values are USER_GENERATED_SNAPSHOT, SCHEDULED_SNAPSHOT
                if snap[a] == 'USER_GENERATED_SNAPSHOT':
                    row.append('manual')
                elif snap[a] == 'SCHEDULED_SNAPSHOT':
                    row.append('scheduled')
                else:
                    row.append(snap[a])
            elif a == 'vmName':
                if vm_length < len(snap[a]):
                    vm_length = len(snap[a])
                row.append(snap[a])
            else:
                row.append(snap[a])
        nr += 1
        rows.append(row)

    header.insert(1, vm_length)
    print("%3s %*s %17s %11s %22s %10s %7s" % (tuple(header)))
    for row in rows:
        row.insert(1, vm_length)
        print("%3d %*s %17s %11s %22s %10s %7s" % ((tuple(row))))

    snap_nr = raw_input("""
Please enter the number of the Snapshot you want to recover from : """)
    if not snap_nr or len(snap_nr.strip()) == 0:
        print("No number given; Giving Up")
        sys.exit(255)

    return snapshots[int(snap_nr)-1]


def map_snapshot(filername, vm_name, snap):
    """
        map the disks of the given snapshot to the VM
    """
    vm_uuid = TFilers(filername).get_VMuuid(vmName=vm_name)
    snap_uuid = snap['uuid']['uuid']

    if verbose > 2:
        print "vm_uuid: %s \nsnap_uuid: %s" % (vm_uuid, snap_uuid)

    if verbose:
        print "... snapshot disks will be mapped to VM; Please be patient"
    TFilers(filername).flr_recover(vm_uuid, snap_uuid)


def init_connection(filername, log_lvl):
    """
        initialize the connection with the Filer
    """

    import logging
    # Set LOGGING
    if log_lvl == 'DEBUG':
        LOG_LEVEL = logging.DEBUG
    elif log_lvl == 'INFO':
        LOG_LEVEL = logging.INFO
    elif log_lvl == 'WARNING':
        LOG_LEVEL = logging.WARNING
    elif log_lvl == 'ERROR':
        LOG_LEVEL = logging.ERROR
    elif log_lvl == 'CRITICAL':
        LOG_LEVEL = logging.CRITICAL
    else:
        LOG_LEVEL = logging.NOTSET

    try:
        tfiler = TFilers(filername, log_lvl=LOG_LEVEL)
    except errors.HTTP_Failure, err:
        print("ERROR: %s" % err.get_error())
        sys.exit(1)
    except errors.API_Failure, err:
        print("ERROR: %s" % err.get_error())
        sys.exit(1)
    return tfiler

def usage():
    print """
USAGE: %(prog)s [-v]* [-q] [(-f | --filer) <file-name>] [--vm <vm-name>] 
       %(prog)s [-v]* [-q] [--reset | --reset_all]
       %(prog)s --version

    the meaning of the options:

        -v               add verbosity
        -q | --quiet     be quiet (only Error output)
        -f | --filer     Tintri-Filername          
        --vm | --vmname  hypervisor virtual machine name 
        --reset          Unmount the FLR Partitions
        --reset_all      Unmount the FLR Partitions and remove all cached
                         informations about the Linux-partitions
        --version        print programm version and exit
        --logging <lvl>  Activate Logging of the API commands to the terminal.
                         possible Levels are:
                         DEBUG, INFO, WARNING, ERROR, CRITICAL
                         the programm and the http_api are using the python "logging"
                         module.

    The "reset" functionality doesn't need "filer" and "vm" parameters because these
    informations are stored in a temporary file in the "dbg_path".

    """ % { 'prog' : basename(sys.argv[0])}
    sys.exit(1)

if __name__ == '__main__':
    #
    # Start of the Main-Prog
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'qvf:?',
            ['help', 'quiet', 'filer=', 'vmname=', 'reset', 'reset_all',
             'version', 'logging=', ])
    except:
        usage()

    filer = None
    vm_name = None
    log_lvl = None
    mRESET = False
    mRESET_ALL = False

    for o, a in opts:
        if o == "-v":
            verbose += 1
        elif o == '--quiet' or o == '-q':
            verbose = 0
        elif o == '--filer' or o == '-f':
            filer = a
        elif o == '--vmname':
            vm_name = a
        elif o == '--reset':
            mRESET = True
        elif o == '--reset_all':
            mRESET_ALL = True
        elif o == '--logging':
            log_lvl = a
        elif o == '--version':
            print "%s : %s" % (basename(sys.argv[0]), Version)
            sys.exit(0)
        else:
            usage()

    if mRESET:
        reset(log_lvl)
    elif mRESET_ALL:
        reset(True, log_lvl)


    # check if we have cached information about the Storage
    cache_info = init_env()
    if 'active' in cache_info and cache_info['active']:
        # it looks like an other snapshot is still mapped
        print """
    ERROR: it looks like an other snapshot is still mapped
    Please call the command with the '--reset' option and restart again.
        """
        sys.exit(3)

    if not 'first_fdisk' in cache_info or not cache_info['first_fdisk']:
        mnt_info = get_disk_mnt_info()
        first_fdisk = get_fdisk_info(dbg_fd)
    else:
        mnt_info = cache_info['mnt_info']
        first_fdisk = cache_info['first_fdisk']
        if not filer:
            filer = cache_info['filername']
        if not vm_name:
            vm_name = cache_info['vm_name']

    filername = check_tfiler(filer)
    init_connection(filername, log_lvl)

    # get virtual machine name; Could be different from hostname
    vm_name = get_vm_name_from_user(filername, vm_name)

    # write the found information to cache; Usefull for next call needed
    # for RESET
    write_first_fdisk(first_fdisk, mnt_info, filername, vm_name)

    # get Snapshots from Filer and ask user which one
    # should be mountet
    snap = get_vm_snapshot(filername, vm_name)
    map_snapshot(filername, vm_name, snap)

    search_for_new_disks()
    new_fdisk = get_fdisk_info(dbg_fd, first_fdisk)

    if not new_fdisk:
        print "ERROR: no new Disks found: :-("
        sys.exit(0)

    mount_snap_disks(first_fdisk, new_fdisk, mnt_info)
    write_first_fdisk(first_fdisk, mnt_info, filername, vm_name, active=True)
