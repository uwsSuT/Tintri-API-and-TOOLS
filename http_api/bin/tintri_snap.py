#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    tintri_snap.py
    ~~~~~~~~~~~~~~~~~~~~~~~~

    CLI programm to handle the Tintri Snapshots 

    You can list, create and delete Snapshots on the Tintri-Storage System

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""
#
# uws: 11.03.2016
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

import getopt
from os.path import join, basename, islink
from time import strftime, localtime

from schtob.tintri_http_api import constants
from schtob.tintri_http_api import tintri_util
from schtob.tintri_http_api import errors

Version = "0.9.0"

verbose = 1

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
        tfilers = TFilers(filername, log_lvl=LOG_LEVEL)
    except errors.HTTP_Failure, err:
        print("ERROR: %s" % err.get_error())
        sys.exit(1)
    except errors.API_Failure, err:
        print("ERROR: %s" % err.get_error())
        sys.exit(1)
    return tfilers

def usage(err_msg=None):
    print """
%(err_msg)s

USAGE: %(prog)s [-v]* (-f | --filer) [--vm <vm-name>] [--description <snap-name>] --list
       %(prog)s [-v]* (-f | --filer) [--vm <vm-name>] --create [<snap-name>]
       %(prog)s [-v]* (-f | --filer) [--vm <vm-name>] --delete (--all | <snap-name> [<snap-name]*)

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

    """ % { 'prog': basename(sys.argv[0]),
            'err_msg' : err_msg,
          }
    sys.exit(1)

if __name__ == '__main__':
    #
    # Start of the Main-Prog
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'qvf:',
            ['all', 'quiet', 'filer=', 'vm=', 'vmname=',
             'list', 'create', 'delete', 'logging=', ])
    except:
        usage("SYNTAX Error")

    filer = None
    vm_name = None
    log_lvl = None
    CREATE = False
    DELETE = False
    LIST = False
    ALL = False

    for o, a in opts:
        if o == "-v":
            verbose += 1
        elif o == '--quiet' or o == '-q':
            verbose = 0
        elif o == '--filer' or o == '-f':
            filer = a
        elif o == '--vm' or o == '--vmname':
            vm_name = a
        elif o == '--all':
            ALL = True
        elif o == '--create':
            CREATE = True
        elif o == '--delete':
            DELETE = True
        elif o == '--list':
            LIST = True
        elif o == '--logging':
            log_lvl = a
        elif o == '--version':
            print "%s : %s" % (basename(sys.argv[0]), Version)
            sys.exit(0)

    # check if we have the needed parameter
    if not filer or not vm_name:
        usage("""Missing input parameter: 
    needed params are:
        filername: %s
        vmname   : %s
        """ % (filer, vm_name))
    filer = init_connection(filer, log_lvl)

    if CREATE and DELETE or \
       CREATE and LIST   or \
       DELETE and LIST:
        usage("2 commands given")
    elif not CREATE and not DELETE and not LIST:
        usage("NO command given")

    if LIST:
        snaps = filer.get_VMsnapshots(vmName = vm_name)
        if not snaps:
            print """
    No Snapshots found
    """
            sys.exit(0)
        tintri_util.print_snapshots(snaps)
    elif DELETE:
        if ALL:
            snap_names = []
        elif not len(args) > 0:
            usage("MISSING Argument")
        else:
            snap_names = args
        filer.del_VMsnapshots(vm_name, snap_names)
    elif CREATE:
        if not len(args) > 0:
            usage("MISSING Argument")
        elif len(args) > 1:
            usage("to many arguments; Only one name allowed")
        else:
            snap_name = args[0]
        filer.create_VMsnapshot(vm_name, snap_name)
