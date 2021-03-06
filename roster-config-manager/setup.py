#!/usr/bin/env python

# Copyright (c) 2009, Purdue University
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
# 
# Neither the name of the Purdue University nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Setup script for roster config manager."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

current_version = __version__
if( __version__.startswith('#') ):
  current_version = '1000'

setup(name='RosterConfigManager',
      version=current_version,
      description='RosterConfigManager is a Bind9 config importer/exporter for '
                  'Roster',
      long_description='Roster is DNS management software for use with Bind 9. '
                       'Roster is written in Python and uses a MySQL database '
                       'with an XML-RPC front-end. It contains a set of '
                       'command line user tools that connect to the XML-RPC '
                       'front-end. The config files for Bind are generated '
                       'from the MySQL database so a live MySQL database is '
                       'not needed.',
      maintainer='Roster Development Team',
      maintainer_email='roster-discussion@googlegroups.com',
      url='http://code.google.com/p/roster-dns-management/',
      packages=['roster_config_manager'],
      license=__license__,
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: System Administrators',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python :: 2.5',
                   'Topic :: Internet :: Name Service (DNS)'],
      install_requires = ['dnspython>=1.6.0', 'IPy>=0.62',
                          'iscpy>=1.0.5', 'fabric>=1.4.0',
                          'RosterCore>=%s' % current_version],
      scripts = ['scripts/dnsconfigsync', 'scripts/dnszoneimporter',
                 'scripts/dnstreeexport', 'scripts/dnscheckconfig',
                 'scripts/dnsexportconfig', 'scripts/dnsrecover',
                 'scripts/dnszonecompare', 'scripts/dnsquerycheck', 
                 'scripts/dnsservercheck', 'scripts/dnsversioncheck']
     )
