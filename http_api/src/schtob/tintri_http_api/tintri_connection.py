# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.tintri_connection
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is intended to be used for handling a bunch of
    :class:`schtob.tintri_http_api.TFiler` objects in an environment where you have
    a single user, which is allowed to run API commands on all your filers.
    Instead of manually creating multiple :class:`TFiler` objects, you can
    use the :class:`TFilers` class which encapsulates all the required
    connection and authentication settings for each filer. The only thing you
    have to do is defining the `TINTRI_CONFIG` dict in
    :mod:`schtob.tintri_http_api.settings`.
    See :ref:`configuration` for more details.

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

import copy
import logging

from schtob.tintri_http_api.tintri_filer import TFiler

# Custom log level for tintri_http_api logger. set to logging.DEBUG for debugging
# if set to logging.NOTSET, the default logger settings are used
# visit http://docs.python.org/library/logging.html for more details.
LOG_LEVEL = logging.NOTSET
#LOG_LEVEL = logging.DEBUG

class TFilers(object):
    """Connections to multiple filers.

    Use it in a static way like this::

        >>> TFilers('my-filer').vm.list_vms()
    """

    __filers = {}
    __config = {}
    __unset = True

    def __new__(cls, name, role='default', log_lvl=None):
        # you can access a connection by typing TFilers(filername).foo
        # Connection is created with default params, defined in TINTRI_CONFIG

        cls._log = logging.getLogger('tintri_http_api')
        if log_lvl:
            cls._log.setLevel(log_lvl)
        else:
            cls._log.setLevel(LOG_LEVEL)

        # XXX set logging to console
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        cls._log.addHandler(ch)

        cls._log.debug("TFilers:__new__: name: \'%s\' " % (name))
        return cls.get_connection(name, role)

    def setup_config(cls, config):
        """Setup the configuration for all your Tintri-Filers.
        """
        cls.__config = config
        cls.__unset = False

    setup_config = classmethod(setup_config)

    def get_connection(cls, name, role='default'):
        """Get connection to filer `name`.
        """
        cls._log.debug("TFilers:get_connection: name: \'%s\' " % (name))
        if (name, role) not in cls.__filers:
            if cls.__unset:
                cls.__config = __import__(
                    'schtob.tintri_http_api.settings', {}, {}, ['TINTRI_CONFIG']
                ).TINTRI_CONFIG
                cls.__unset = False
            roles = copy.deepcopy(cls.__config['roles'])
            filer_roles = cls.__config.get('filer-roles', {})

            rolesettings = roles['default']

            if name in filer_roles and 'default' in filer_roles[name]:
                rolesettings.update(filer_roles[name]['default'])

            if role in roles:
                rolesettings.update(roles[role])

            if name in filer_roles and role in filer_roles[name]:
                rolesettings.update(filer_roles[name][role])

            return cls.create_connection(name, rolesettings, role)
        return cls.__filers[(name, role)]

    get_connection = classmethod(get_connection)

    def create_connection(cls, name, settings, role='default'):
        """Create a connection to filer `name` with `settings`.

        Use this to instantiate a "special" connection where settings differ
        from `TINTRI_CONFIG` instead of just using TFilers(name).

        """
        cls._log.debug("TFilers:create_connection: name: \'%s\' role \'%s\' " %(
                                                                name, role))
        cls.__filers[(name, role)] = TFiler(name, settings)
        return cls.__filers[(name, role)]

    create_connection = classmethod(create_connection)

    def drop_connection(cls, name, role='default'):
        """Drops connection to filer `name`."""
        cls._log.debug("TFilers:drop_connection: name: \'%s\' " % (name))
        if (name, role) in cls.__filers:
            cls.__filers.pop((name, role))

    drop_connection = classmethod(drop_connection)

    def list_connections(cls):
        for (name, role) in cls.__filers:
            #print "Active connections: %s : %s" % (name, role)
            pass
        return cls.__filers

    list_connections = classmethod(list_connections)


#
# Be sure that all active connections are closed at the end of a prog
#
import atexit
def exit_handler():
    for (name, role) in TFilers.list_connections():
        TFilers(name, role).logout()

atexit.register(exit_handler)
