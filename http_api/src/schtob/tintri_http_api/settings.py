# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Settings for the :class:`TFilers` class. You may want to define
    authentication settings for all your storage systems here.

    See :ref:`configuration` for more details.

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

import os, sys
from schtob.tintri_http_api import constants

# Define your TINTRI_CONFIG here
TINTRI_CONFIG = {
    'roles': {
        'default': {
            'user': 'admin',
            'password': '',
        },
        'my-fancy-default-role': {
            'user': 'fancy-user',
            'password': '',
        },
    },

    'filer-roles': {

        'my-fancy-filer': {
            'default': {
                'password': 'fancy-password',
            },
            'yet-another-fancy-role-only-for-this-filer': {
                'user': 'yet-another-fancy-user',
            },
        },

    }
}


def __import_local_settings():
    """Tries to import ``TINTRI_CONFIG`` from `local_settings.py`."""

    TINTRI_CONFIG = None
    try:
        TINTRI_CONFIG = __import__('schtob.tintri_http_api.local_settings', {},
                                {}, ['TINTRI_CONFIG']).TINTRI_CONFIG
    except ImportError:
        pass
    except AttributeError:
        pass

    # and now try $HOME/.tintri/local_settings.py
    tconfigd = os.path.join(os.environ['HOME'], constants.Tconfig_dir)
    if os.path.exists(tconfigd) and \
       os.path.exists(os.path.join(tconfigd, 'local_settings.py')):
        sys.path.insert(0, tconfigd)
    try:
        TINTRI_CONFIG = __import__('local_settings', {}, {},
                                      ['TINTRI_CONFIG']).TINTRI_CONFIG
    except ImportError:
        pass
    except AttributeError:
        pass

    return TINTRI_CONFIG



if __import_local_settings():
    TINTRI_CONFIG = __import_local_settings()
