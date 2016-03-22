# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.tintri_filer
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to invoke HTPP REST API commands on a Tintri Filer

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

import copy
import logging
import requests
import json
import sys
from time import localtime, strftime

from schtob.tintri_http_api import constants
from schtob.tintri_http_api import errors

class TFiler(object):
    """Create a new connection to filer `filer` using `settings` dict.

    `settings` may consist of the following entries:

        ================== ========= ===================================
        Key                Default   Possible values
        ================== ========= ===================================
        **user**           "root"    `str`
        **password**       ""        `str`
        ================== ========= ===================================

    """

    def __init__(self, filer, settings=None):
        self._filer = filer
        self._log = logging.getLogger('tintri_http_api')

        self._settings = {
            'password': '',
            'user': 'admin',
        }

        if settings and isinstance(settings, dict):
            self._settings.update(settings)

        self.header = {'content-type': 'application/json'}
        self.session_id = None
        self.vm_info = None     # Cache for the VM-Info Dict
                                # We don't want to get all VM information again 
                                # and again
        self.vm_attr_dict = None

        self.login()

    @property
    def settings(self):
        return self._settings

    def __call_http_api_post(self, url, data=None, headers=None, verify=False):
        self._log.debug("""call_http_api_post:
    url     : %s
    data    : %s
    headers : %s
    verify  : %s
        """ % (url, data, headers, verify))
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers,
                                                                verify=verify)
        except requests.ConnectionError:
            err_msg = "API Connection error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.HTTPError:
            err_msg = "HTTP error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.Timeout:
            err_msg = "Request timed out"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except Exception:
            err_msg = "An unexpected error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)

        # check status code
        if r.status_code == 403:
            err_msg = "The response for the http call \'%s\' is 403 : Forbidden" % (url)
            self._log.error(err_msg)
            self._log.debug("settings\'%s\' " % (self._settings))
            raise errors.API_Failure(err_msg, r.status_code)
        elif r.status_code is not 200:
            err_msg = "The response for the http call \'%s\' is not 200 status: %s" % (url, r.status_code)
            self._log.error(err_msg)
            raise errors.API_Failure(err_msg, r.status_code)

        self._log.debug("call_http_api: r.cookies: %s" % r.cookies)

        return r

    def __call_http_api_get(self, url, headers=None, query=None, verify=False,
                                        get_all_pages=False, page_size=2000):

        # The Default page_size of the API is 2000
        offset = 0
        first_http_vals = None

        while True:
            curl = "%(url)s?offset=%(offset)s&limit=%(page_size)s" % ({
                            'url' : url,
                            'page_size' : str(page_size),
                            'offset' : str(offset),
                            })

            self._log.debug("""call_http_api_get:
    url     : %s
    params  : %s
    headers : %s
    verify  : %s
            """ % (curl, query, headers, verify))

            try:
                r = requests.get(curl, params=query, headers=headers, verify=verify)
            except requests.ConnectionError:
                err_msg = "API Connection error occurred"
                self._log.error(err_msg)
                raise errors.HTTP_Failure(err_msg)
            except requests.HTTPError:
                err_msg = "HTTP error occurred"
                self._log.error(err_msg)
                raise errors.HTTP_Failure(err_msg)
            except requests.Timeout:
                err_msg = "Request timed out"
                self._log.error(err_msg)
                raise errors.HTTP_Failure(err_msg)
            except Exception:
                err_msg = "An unexpected error occurred"
                self._log.error(err_msg)
                raise errors.HTTP_Failure(err_msg)

            if r.status_code == 204:
                # Empty return logout
                return None
            elif r.status_code is not 200:
                err_msg = """The response for the http call
\'%s\'
    is not 200 status: %s
    call_http_api_get: r.text: %s
                    """ % (url, r.status_code, r.text)
                self._log.error(err_msg)
                raise errors.API_Failure(err_msg, r.status_code)

            # check if we have more the one page
            #
            #  page        The current page number
            #  filteredTotal    The number of objects returned as specified by the filter.
            #                    If no filter was requested, then the value is the same as total.
            # Wenn das next field gesetzt ist kann man die nächsten Werte
            # auf folgende Art holen
            #
            # vm_paginated_result = {'next' : "offset=0&limit=" + str(page_size)}
            # while 'next' in vm_paginated_result:
            #       url = get_vm_url + "?" + vm_paginated_result['next']

            http_vals = json.loads(r.text)
            if not get_all_pages:
                break

            if http_vals['pageTotal'] < http_vals['absoluteTotal']:
                # we have more then ONE page
                offset += int(http_vals['limit'])
                if first_http_vals:
                    # second page
                    first_http_vals['items'] += copy.copy(http_vals['items'])
                    first_http_vals['filteredTotal'] += http_vals['filteredTotal']
                    first_http_vals['page'] += http_vals['page']
                else:
                    # first page
                    first_http_vals = copy.copy(http_vals)

                # check if it was the last page
                if http_vals['page'] * http_vals['limit'] > http_vals['absoluteTotal']:
                    return first_http_vals

        """
        if http_vals['pageTotal'] < http_vals['absoluteTotal'] and \
           not get_all_pages:
        """
        if 'overflow' in http_vals and http_vals['overflow']:
            self._log.warn("""__call_http_api_get: GOT an Overflow; Nr of VMs
        total: %s, filteredTotal: %s, pageTotal: %s, absoluteTotal: %s""" % (
                    http_vals['total'],
                    http_vals['filteredTotal'],
                    http_vals['pageTotal'],
                    http_vals['absoluteTotal'],))

        return http_vals


    def __call_http_api_put(self, url, headers=None, data=None, verify=False):

        self._log.debug("""call_http_api_put:
    url     : %s
    data    : %s
    headers : %s
    verify  : %s
        """ % (url, data, headers, verify))
        
        try:
            r = requests.put(url, data=json.dumps(data), headers=headers,       
                                                                verify=verify)
        except requests.ConnectionError:
            err_msg = "API Connection error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.HTTPError:
            err_msg = "HTTP error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.Timeout:
            err_msg = "Request timed out"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except Exception:
            err_msg = "An unexpected error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)

        if r.status_code == 204:
            # Empty return logout
            return None
        elif r.status_code is not 200:
            err_msg = """The response for the http call
\'%s\'
    is not 200 status: %s
    call_http_api_put: r.text: %s
                """ % (url, r.status_code, r.text)
            self._log.error(err_msg)
            raise errors.API_Failure(err_msg, r.status_code)

        http_vals = json.loads(r.text)
        return http_vals


    def __call_http_api_del(self, url, headers=None, data=None, verify=False):

        self._log.debug("""call_http_api_del:
    url     : %s
    data    : %s
    headers : %s
    verify  : %s
        """ % (url, data, headers, verify))
        
        try:
            r = requests.delete(url, data=json.dumps(data), headers=headers,
                                                                verify=False)
        except requests.ConnectionError:
            err_msg = "API Connection error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.HTTPError:
            err_msg = "HTTP error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except requests.Timeout:
            err_msg = "Request timed out"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)
        except Exception:
            err_msg = "An unexpected error occurred"
            self._log.error(err_msg)
            raise errors.HTTP_Failure(err_msg)

        if r.status_code is not 200:
            err_msg = """The response for the http call
\'%s\'
    is not 200 status: %s
    call_http_api_del: r.text: %s
                """ % (url, r.status_code, r.text)
            self._log.error(err_msg)
            raise errors.API_Failure(err_msg, r.status_code)

        http_vals = json.loads(r.text)
        return http_vals

    def login(self):
        self._log.debug("""login: """)

        url = constants.URLS['login'] % ({'ServerName' : self._filer})
        json_input = { "username" : self._settings['user'],
                       "password" : self._settings['password'],
                       "typeId"   : constants.TypeId,
                     }

        try:
            r = self.__call_http_api_post(url, json_input, self.header)
        except errors.API_Failure, err:
            if err.get_errno() == 403: # Forbidden
                print """
    Couldn't login to Tintri Storage System \'%s\'!
    Have you configured the local_settings.py file ???
    If you haven't, please read the REAMDE
                    """ % self._filer
            sys.exit(1)

        self.session_id = r.cookies['JSESSIONID']
        self.header['cookie'] = "JSESSIONID=%s" % self.session_id

    def logout(self):
        self._log.debug("""logout: """)
        if not self.session_id:
            return

        url = constants.URLS['logout'] % ({'ServerName' : self._filer})
        self.__call_http_api_get(url, headers=self.header)

        self.session_id = None
        self._log.info("LOGOUT DONE for Tintri-Filer: %s" % self._filer)

    def get_VMinfo(self, vmName=None, force=False):
        """
            get the Tintri Information for All or for 1 virtual machine
            vmName == "virtual machine name" of the hyper-visor

            The information will be cached for the lifetime of the Class-
            Object. If you need to actualize the information you should
            call the function with the force parameter.
        """
        self._log.debug("get_VMinfo: vmName: \'%s\' force: %s" % (
                                                        vmName, force))
        url = constants.URLS['get_vms'] % ({'ServerName' : self._filer})

        params = None
        if vmName:
            params = {
                'queryType': 'TOP_DOCS_BY_TIME',
                'name': vmName,
            }
            force = True
        if not self.vm_info or force:
            self.vm_info = self.__call_http_api_get(url, headers=self.header,
                        query=params)

        return self.vm_info

    def get_VMnames(self, only_live_vms=True):
        """
            return a list of all known virtual machine names of the Filer
        """
        self._log.debug("get_VMnames: only_live_vms: %s" % (only_live_vms))

        vmInfo = self.get_VMinfo()

        vms = []
        for vm in vmInfo['items']:
            if vm['isLive']:
                vms.append(vm['vmware']['name'])
            elif not only_live_vms:
                vms.append(vm['vmware']['name'])
        vms.sort()
        return vms

    def get_VMattrs(self, vmName=None, attrs=constants.vm_default_attrs,
                                                    only_live_vms=True, ):
        """
            return the 'vmware' attribute[s] of all or the requested virtual
            machines

            the attrs parameter defines which parameters are included in 
            the return dictionary
        """
        self._log.debug("get_VMattrs: vmName: \'%s\' only_live_vms: %s" % (
                                                    vmName, only_live_vms))
        vmInfo = self.get_VMinfo()

        vms = {}
        for vm in vmInfo['items']:
            # isLive is no VMware Attr, we add it to the attr list
            name = vm['vmware']['name']
            if not vm['isLive'] and only_live_vms:
                continue
            vms[name] = { 'isLive' : vm['isLive'] }
            for a in attrs:
                vms[name][a] = vm['vmware'][a]
        self.vm_attr_dict = vms
        if vmName:
            if vmName not in vms:
                return None
            return vms[vmName]
        return vms

    def get_VMuuid(self, vmName):
        """
            return the uuid of the given Virtual Machine Name
        """
        self._log.debug("get_VMuuid: vmName: \'%s\'" % (vmName))
        vmInfo = self.get_VMinfo()

        vms = {}
        for vm in vmInfo['items']:
            if vmName == vm['vmware']['name']:
                return vm['uuid']['uuid']
        return None

    def get_VMsnapshots(self, vmName=None, snapname=None):

        """
           get the Snapshots for the given VM (if the vmName is given)

           OR

           get Snapshot information for all virtual machines
        """
        self._log.debug("get_VMsnapshots: vmName: \'%s\'" % (vmName))

        url = constants.URLS['get_snapshots'] % ({'ServerName' : self._filer})

        if vmName or snapname:
            params = {
                'queryType': 'TOP_DOCS_BY_TIME',
            }
        else:
            params = None
        if vmName:
            params['contain'] = vmName,
        # I Know that snapname overrides the contain parameter if both
        # parameters are set. But the loop some lines deeper will filter
        # the vmName part.
        # The API Filter function doesn't work for both parameters :-(
        if snapname:
            params['contain'] = snapname

        self.snapshot_info = self.__call_http_api_get(url, headers=self.header,
                                                                query=params)

        if vmName:
            vm_snaps = []
            for snap in self.snapshot_info['items']:
                if not vmName == snap['vmName']:
                    continue
                else:
                    vm_snaps.append(snap)
            return vm_snaps
        else:
            return self.snapshot_info

    def create_VMsnapshot(self, vmName, snap_name,
                                                consistency='CRASH_CONSISTENT'):
        """
            Create a Snapshot for the given VM with the give snap_name
            the consitency could be one of
            'CRASH_CONSISTENT' | 'VM_CONSISTENT' | 'APP_CONSISTENT'
        """
        self._log.debug("""create_VMnapshot: vmName: \'%s\' snap_name: \'%s\'
                    consistency \'%s\'""" % (vmName, snap_name, consistency))
        url = constants.URLS['get_snapshots'] % ({'ServerName' : self._filer}) 

        vmuuid = self.get_VMuuid(vmName)
        data = {
             'typeId' : 'com.tintri.api.rest.v310.dto.domain.beans.snapshot.SnapshotSpec',
             'consistency': consistency,
             'snapshotName': snap_name,
             'sourceVmTintriUUID': vmuuid,
             'retentionMinutes': 2880,
             'type' : 'USER_GENERATED_SNAPSHOT',
        }
        return self.__call_http_api_post(url, data, self.header)

    def del_VMsnapshot(self, vmName, snap_info):
        """
            we only delete snaps for a given VM therefore we only use
            the API like this:
            ?vmUuid=0000-VIM-0000&replicaTintriUuids=0000-SST-0000&replicaTintriUuids=0000-SST-0001
        """
        url = constants.URLS['get_snapshots'] % ({'ServerName' : self._filer}) 
        vmuuid = self.get_VMuuid(vmName)
        curl = url + "/%s" % snap_info['uuid']['uuid']
        ret = self.__call_http_api_del(curl, headers=self.header)
        self._log.info(ret)

    def del_VMsnapshots(self, vmName, snap_name=[], force=False):
        """
            delete the given "snap_list" snapshots for the VM

        """
        self._log.debug("del_VMsnapshots: vmName: \'%s\' snap_name: \'%s\'" % (
                                                        vmName, snap_name))
        snaps = self.get_VMsnapshots(vmName, snap_name)
        if not snaps:
            print """
    No Snapshots found with matching Description
            """
            return
        for snap in snaps:
            if force:
                self.del_VMsnapshot(vmName, snap)
                continue

            answ = raw_input("""Delete the following Snapshot?
    %s %s 
[Y | N] (N): """ % (
                strftime("%x %X", localtime(snap['createTime']/1000)),
                snap['description']))
            if answ.lower().strip() == 'y':
                self.del_VMsnapshot(vmName, snap)


    def fetch_snapshot_disks(self, snapshotUUID):
        """
            fetch Snapshot Disks for a given SnapshotUUID
        """
        self._log.debug("fetch_snapshot_disks: snapshotUUID: \'%s\'" % (
                                                                snapshotUUID))
        url = constants.URLS['get_snapshot_disks'] % (
                                            {'ServerName'   : self._filer,
                                             'SnapshotUuid' : snapshotUUID,
                                            })

        self.disk_info = self.__call_http_api_get(url, headers=self.header)
        return self.disk_info

    def flr_recover(self, vm_uuid, snap_uuid):
        self._log.debug("""flr_recover:
    vm_uuid   : %s
    snap_uuid : %s """ % (vm_uuid, snap_uuid))
        url = constants.URLS['sync'] % ({'ServerName' : self._filer})

        data = {
            "type" : "FILE_RESTORE",
            "targetVmTintriUuids" : vm_uuid,
            "snapshotTintriUuid" : snap_uuid,
            "sourceDisks":[],
            "destDisks":[],
            "isAsync":True,
            "vmConfig" : {
                "isDiskAutoDetach" : True,
                "diskAutoDetachInMinutes" : 2880,
                "typeId" : "com.tintri.api.rest.v310.dto.domain.beans.vm.VirtualMachineSyncVmConfig"
                },
            "typeId" : "com.tintri.api.rest.v310.dto.domain.beans.vm.VirtualMachineSyncSpec"
        }

        r = self.__call_http_api_post(url, data, self.header)

    def del_flr_disks(self, vmName):
        """
            remove the sync disks for the given machine.
        """
        self._log.debug("del_flr_disks: vmName: \'%s\'" % (vmName))
        vmuuid = self.get_VMuuid(vmName)
        url = constants.URLS['deleteSyncDisks'] % ({'ServerName' : self._filer})

        #
        # the function doesn't return a result;
        # If it was a incorrect input parameter
        # the function ..api_put will throw an error
        #
        self.__call_http_api_put(url, data=vmuuid, headers=self.header)

        self._log.info("called del_flr_disks")


