# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.constants
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Tintri HTTP REST API constants.

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""


URLS = {
    'login': "https://%(ServerName)s/api/v310/session/login",
    'logout': "https://%(ServerName)s/api/v310/session/logout",
    'get_vms': "https://%(ServerName)s/api/v310/vm",
    'get_snapshots': "https://%(ServerName)s/api/v310/snapshot",
    'get_snapshot_disks': "https://%(ServerName)s/api/v310/snapshot/%(SnapshotUuid)s/disks",
    'sync' : "https://%(ServerName)s/api/v310/vm/sync",
    'deleteSyncDisks' : "https://%(ServerName)s/api/v310/vm/deleteSyncDisks",
}

TypeId = 'com.tintri.api.rest.vcommon.dto.rbac.RestApiCredentials'

vm_default_attrs = ['name',
                    'isPowered',
                    'host',
                    'hasSnapshots',
                    'vcenterName',
                    'hypervisorPath',
                   ]
vm_all_attrs = vm_default_attrs + [
                    'folderPath',
                    'hypervisorType',
                    'instanceUuids',
                    'isTemplate',
                    'lastUpdateFromHypervisor',
                    'mor',
                    'storageContainers',
                    'subdir',
                    'supportedSnapshotConsistencyTypes',
                    'typeId',
                    'vcenterName',
                ]

snap_default_attrs = ['vmName',
                      'createTime',
                      'creatorName',
                      'description',
                      'sizeChangedPhysicalMB',
                      'type',
                     ]
snap_all_attrs = snap_default_attrs + [
                      'expirationTime',
                      'cloneReferenceCount',
                      'consistency',
                      'deletionPolicy',
                      'expirationTime',
                      'hypervisorType',
                      'id',
                      'isCollapsed',
                      'isDeleted',
                      'isLastReplicatedSnapshot',
                      'isOrphaned',
                      'isReplica',
                      'lastUpdatedTime',
                      'replicaRetentionMinutes',
                      'sizeChangedMB',
                      'typeId',
                      'uuid',
                      'typeId',
                      'uuid',
                      'vcenterInstanceUuid',
                      'vmIsTemplate',
                     ]

Tconfig_dir = '.tintri'
