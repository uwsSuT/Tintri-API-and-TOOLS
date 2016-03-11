#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    setup
    ~~~~~

    Pyontapi setup script.

    :copyright: 2010-2015 Schaefer & Tobies SuC GmbH.
    :author: Markus Grimm <mgr@schaefer-tobies.de>;
             Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

import distutils.core
import os
import shutil
import sys
import tempfile


def main():
    """ run distutils.setup """

    # Exclude local_settings.py from being added to package/installation
    local_settings_py = os.path.join('src', 'schtob', 'tintri_http_api',
                                     'local_settings.py')
    temp_file_path = None
    if os.path.exists(local_settings_py):
        temp_file_path = os.path.join(tempfile.gettempdir(),
                                      'tintri_http_api_local_settings.py')
        shutil.move(local_settings_py, temp_file_path)

    handle = open(local_settings_py, 'w')
    handle.write('')
    handle.close()

    sys.path.append('src')
    from schtob.tintri_http_api import VERSION

    distutils.core.setup(
        name='tintri_http_api',
        version=VERSION,
        description='Python Tintri HTTP API Implementation',
        long_description=('tintri_http_api is a Python implementation '
                          'for the Tintri HTTP-Rest API. '
                          'It is a wrapper around the Tintri HTTP-Rest-API.'),
        author='Uwe W. Schäfer',
        author_email='uws@schaefer-tobies.de',
        url='http://www.schaefer-tobies.de',
        download_url='http://www.schaefer-tobies.de/dist/%s/'
                     'tintri_http_api-%s.tar.gz' % (VERSION, VERSION),
        license='LGPL',
        platforms=['POSIX', 'Windows'],
        packages=['schtob', 'schtob.tintri_http_api'],
        package_dir = {'': 'src'},
        scripts=[os.path.join('bin', 'tintri_flr.py'),
                 os.path.join('bin', 'tintri_snap.py'),
                ],
        classifiers=[
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.0',
            'Programming Language :: Python :: 3.1',
            'Programming Language :: Python :: 3.2',
            'Operating System :: POSIX',
            'Operating System :: Microsoft',
            'Operating System :: MacOS',
        ]
    )

    # restore local_settings.py
    if temp_file_path:
        shutil.move(temp_file_path, local_settings_py)


if __name__ == '__main__':
    main()
