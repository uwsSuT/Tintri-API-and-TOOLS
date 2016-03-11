# Tintri-API-and-TOOLS
Easy to use API for the Tintri-Storage-System. Including some CLI tools

================================================================================
                README: for the Python HTTP-API for Tintri Storage Systems
                Version: 0.0.1
                Copyright (c) 2016  -  The MIT License (MIT)
                      Uwe W. Schäfer 
                      Schäfer & Tobies Software u. Consulting GmbH
                      www.schaefer-tobies.de
                uws: 2016.03.11
================================================================================

This repository is a wrapper implementation of the Tintri-REST-API in a object 
oriented Python Class.
The Library includes a python setup.py script which will install the library
into the local python dist-packages.
But you can test and work with the library without installation too.
The only other thin you have to do for initialisation is a definition of
your user credentials in a local_settings.py file (see local_settings later on in this
README)
After that just set the Python-Path and use the lib functions like this:

    from schtob.tintri_http_api import TFilers
    TFilers('tintri-adm').create_VMsnapshot(vm_name, snap_name)

There are two binaries you can use for working or for getting an idea how to use
the API.

__tintri_snap.py        list, create and delete Snapshots on the Tintri-Storage System__

__tintri_flr.py         mount a Tintri Storage Snapshot at a local linux system__

================================================================================
##      local_settings.py 
### Defining the credentials for different Storage-Systems and Users
================================================================================
You must define the user credentials for your Tintri-Systems in a Python-file.
There are two possible places for the configuration file.

1. Global definition
    Define the __TINTRI_CONFIG__ dictionary in the python library area.
    i.e. 
    _/usr/local/lib/python2.7/dist-packages/schtob/tintri_http_api/local_settings.py_
2. User specific definition
    Define the __TINTRI_CONFIG__ dictionary in you HOME directory.
    i.e. 
    _/home/uws/.tintri/local_settings.py_

If both files are existent the local one will override the global one.

And here is the needed dictionary:
        
    TINTRI_CONFIG = {
        # Global definition
        'roles': {
            # the default user if no other role an "filer-role" matches
            'default': {
                'user': 'admin',
                'password': 'admin-password',
            },
            # a different user for a different role, you can define the role
            # parameter in the connection call
            'my-fancy-default-role': {
                'user': 'fancy-user',
                'password': '1234',
            },
        },
        # Filer specific definitions
        'filer-roles': {
            # The user for the Filer 'tintri-adm' should be the user 'uws'
            'tintri-adm': {
                'default': {
                    'user' : 'uws',
                    'password': 'uws-password',
                },
                'yet-another-fancy-role-only-for-this-filer': {
                    'user': 'yet-another-fancy-user',
                },
            },
        }
    }

================================================================================
#      tintri_snap.py
================================================================================
The _*tintri_snap.py*_ opens an easy CLI possibility to handle Tintri-Snapshots.

Here are the actual possible options

1. List the actual Snapshots of a virtual machine
2. Create a new Snapshot for a virtual machine
3. Delete __all__ or the given Snapshot-Names for a virtual machine

The functionality is more or less an example of the API usage, but it could be usefull too.
But be carefull the __delete__ function will delete without any further inquery and it
will delete all _matching_ snapshots.

Here is the complete _Usage_:

================================================================================
##      tintri_snap.py Usage:
================================================================================
    USAGE: tintri_snap.py [-v]* (-f | --filer) [--vm <vm-name>] [--description <snap-name>] --list
       tintri_snap.py [-v]* (-f | --filer) [--vm <vm-name>] --create [<snap-name>]
       tintri_snap.py [-v]\* (-f | --filer) [--vm <vm-name>] --delete (--all | <snap-name> [<snap-name]\*)

    the meaning of the options:

    -v               add verbosity
    --all            delete ALL snapshots (see --delete)
    -q | --quiet     be quiet (only Error output)
    -f | --filer     Tintri-Filername          
    --vm | --vmname  hypervisor virtual machine name 
    --list           List the Snapshots of the selected machine
    --create         Create a new Snapshot for the selected machine.
                     if now snap-name is given the script will be asked for one
    --delete         Delete the the given snap_names or ALL snapshots if
                     the option --all is given
    --version        print programm version and exit
    --logging <lvl>  Activate Logging of the API commands to the terminal.
                     possible Levels are:
                         DEBUG, INFO, WARNING, ERROR, CRITICAL
                     the programm and the http_api are using the python "logging"
                     module.

================================================================================
#       tintri_flr.py
================================================================================
This python script __tintri_flr.py__ intends to mount a snapshot from a
Tintri-Storage on the actual LINUX-System.

After you recovered a Tintri-Snapshot you need to mount the newly generated
SCSI-Devices on your LINUX System. You can do this by using several LINUX
commands or by the __tintri_flr.py__ Python script.

The only thing you have to do for mounting the snapshot is:
* call the __tintri_flr.py__ without any option!

__You must be "root" or use "sudo" to get the script working!__

### Without any option the script does the following:
1. check if the local virtual machine name is equal to a vmware machine name. If 
   this is not the case, list all virtual machines and asks which one should be 
   used.
2. lists all available snapshots of the selected virtual machine. Let the user select one of them.
3. maps the snapshot disks of the selected snapshot at the virtual machine
4. determine the actual filesystem infomation.
5. search for new Snapshot-Disks in the SCSI environment.
6. generate new Mount-Points for the snapshot disks (if not allready existent).
7. mount the disks.

### Umounting of the previously mounted partitions
* call the script with __--reset__ option

================================================================================
##                Limitations
================================================================================
This script can only be used with "normal" partitions.
Volumemanager partitions couldn't be mounted from a tintri snapshot!

================================================================================
##                USAGE
================================================================================
    USAGE: tintri_flr.py [-v]* [-q] [(-f | --filer) <file-name>] [--vm <vm-name>] 
           tintri_flr.py [-v]* [-q] [--reset | --reset_all]
           tintri_flr.py --version

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

================================================================================
##                Environment
================================================================================
The filesystem information is stored in a information directory in the
home directory of the "root" user. This can be changed on top of the script
in the setting of the variable __DBG_PATH__.

The mount-points are generated in a directory named **/tintri_recover**.
This can also be changed by editing the vraiable __TINTRI_RECOVER_DIR__ in the top area of the script.


================================================================================
#       the actual existing API functions
================================================================================

    login()
    logout()
    get_VMinfo(vmName=None, force=False)
    get_VMnames(only_live_vms=True)
    get_VMattrs(vmName=None, attrs=constants.vm_default_attrs, only_live_vms=True)
    get_VMuuid(vmName)
    get_VMsnapshots(vmName=None, snapname=None)
    create_VMsnapshot(vmName, snap_name, consistency='CRASH_CONSISTENT')
    del_VMsnapshots(vmName, snap_name=[])
    flr_recover(vm_uuid, snap_uuid)
    del_flr_disks(vmName)
