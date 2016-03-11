# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.tintri_util
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module is a helper modue for the tintri API commands 

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

from time import strftime, mktime, localtime

from schtob.tintri_http_api import TFilers
import constants

def print_snapshots(snapshots, sort_column='createTime'):
    """
        print the "snap_default_attrs" of the snapshots
        sort the snapshot list with the given "sort_column"

        the functions adds a Nr. attribute in Front of the other attrs
    """
    snapshots.sort(cmp=lambda x,y: cmp(x[sort_column], y[sort_column]))

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


def PT_print_snapshots(tsnaps, attrs=constants.snap_default_attrs):
    """
        print the snapshots of a given Snapshot list with the
        python module "PrettyTable"
    """
    from prettytable import PrettyTable

    # check if we got the real list of snaps or the http list
    if 'items' in tsnaps:
        snaps = tsnaps['items']
    else:
        snaps = tsnaps
    table = PrettyTable()
    header = ['Nr.']
    for a in attrs:
        # pimp the header entrys
        if a == 'sizeChangedPhysicalMB':
            header.append('Changed MB')
        else:
            header.append(a)
    table.field_names = header

    nr = 0
    for snap in tsnaps:
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
            else:
                row.append(snap[a])
        table.add_row(row)
        nr += 1

    print table


def print_vm_attrs(vm_attrs):
    """
        print the given attributes of all Virtual Machine in a human readable table
    """

    table = PrettyTable()
    first = True
    for vm in vm_attrs:
        if first:
            first = False
            keys = vm_attrs[vm].keys()
            table.field_names = keys
        row = []
        for a in keys:
            row.append(vm_attrs[vm][a])
        table.add_row(row)
    print table
