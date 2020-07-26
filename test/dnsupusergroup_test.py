#!/usr/bin/python

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

"""Regression test for dnsupusergroup

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import sys
import socket
import threading
import time
import getpass
import unittest

import roster_core
import roster_server
from roster_user_tools import roster_client_lib


USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC = '../roster-user-tools/scripts/dnsupusergroup'


class options(object):
  password = u'test'
  username = u'sharrell'
  server = None
  ldap = u'ldaps://ldap.cs.university.edu:636'
  credfile = CREDFILE
  view_name = None
  ip_address = None
  target = u'machine1'
  ttl = 64


class DaemonThread(threading.Thread):
  def __init__(self, config_instance, port):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.daemon_instance = None

  def run(self):
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE)
    self.daemon_instance.Serve(port=self.port)

class Testdnsmkusergroup(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.daemon = True
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testUpdateForwardZonePermissions(self):
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname', u'ns', u'soa']}, 
                {'zone_name': u'eas.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname']}], 
         u'bio': [{'zone_name': u'bio.university.edu', 'group_permission': 
                    [u'a', u'aaaa']}]})

    #testing adding permissions
    output = os.popen('python %s forward '
                      '--group-permission=a,aaaa,cname,ns,soa,mx '
                      '-z cs.university.edu -g cs -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                                             PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '')
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname', u'ns', u'soa', u'mx']}, 
                 {'zone_name': u'eas.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname']}], 
         u'bio': [{'zone_name': u'bio.university.edu', 'group_permission': 
                    [u'a', u'aaaa']}]})
    output.close()
    
    #testing remove permissions
    output = os.popen('python %s forward '
                      '--group-permission=a,aaaa,cname,ns '
                      '-z cs.university.edu -g cs -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                                             PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '')
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname', u'ns']}, 
                 {'zone_name': u'eas.university.edu', 'group_permission': 
                    [u'a', u'aaaa', u'cname']}], 
         u'bio': [{'zone_name': u'bio.university.edu', 'group_permission': 
                    [u'a', u'aaaa']}]})
    output.close()

  def testUpdateReverseRangePermissions(self):
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
        {u'cs': [{'group_permission': [u'cname', u'ns', u'ptr', u'soa'], 
                       'cidr_block': u'192.168.0.0/24'}], 
         u'bio': [{'group_permission': [u'cname', u'ptr'], 
                       'cidr_block': u'192.168.0.0/24'}, 
                  {'group_permission': [u'ptr'], 
                       'cidr_block': u'192.168.1.0/24'}]})

    #testing adding permissions
    output = os.popen('python %s reverse '
                      '--group-permission=aaaa,cname,ptr,soa,ns '
                      '--cidr-block=192.168.0.0/24 -g cs -s %s -u %s -p %s '
                      '--config-file=%s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '')
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
        {u'cs': [{'group_permission': [u'cname', u'ns', u'ptr', u'soa',
                                       u'aaaa'], 
                       'cidr_block': u'192.168.0.0/24'}], 
         u'bio': [{'group_permission': [u'cname', u'ptr'], 
                       'cidr_block': u'192.168.0.0/24'}, 
                  {'group_permission': [u'ptr'], 
                       'cidr_block': u'192.168.1.0/24'}]})
    output.close()

    #testing removing permissions
    output = os.popen('python %s reverse --group-permission=ptr '
                      '--cidr-block=192.168.0.0/24 -g cs -s %s -u %s -p %s '
                      '--config-file=%s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '')
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
        {u'cs': [{'group_permission': [u'ptr'], 
                       'cidr_block': u'192.168.0.0/24'}], 
         u'bio': [{'group_permission': [u'cname', u'ptr'], 
                       'cidr_block': u'192.168.0.0/24'}, 
                  {'group_permission': [u'ptr'], 
                       'cidr_block': u'192.168.1.0/24'}]})
    output.close()

  def testForwardErrors(self):
    #testing a zone that is not assigned to group cs
    self.core_instance.MakeZone(u'test_zone', u'main', u'test_zone.')
    output = os.popen('python %s forward --group-permission=a,aaaa,cname,ns '
                      '-z test_zone -g cs -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'USER ERROR: Trying to update permissions on '
                     'zone test_zone not assigned to group cs.\n')
    output.close()

    #testing a zone that does not exist
    output = os.popen('python %s forward --group-permission=a,aaaa,cname,ns '
                      '-z no_zone -g cs -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'CLIENT ERROR: Zone no_zone does not exist.\n')
    output.close()
    
    #testing a record type that doesn't exist
    output = os.popen('python %s forward --group-permission=none,a,aaaa '
                      '-z cs.university.edu -g cs -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'CLIENT ERROR: Permission none does not exist.\n')
    output.close()

    #testing a group that doesn't exist
    output = os.popen('python %s forward --group-permission=a,aaaa '
                      '-z cs.university.edu -g no_group -s %s -u %s -p %s '
                      '--config-file=%s ' % (EXEC, self.server_name, USERNAME, 
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'CLIENT ERROR: Group no_group does not exist.\n')
    output.close()

  def testReverseErrors(self):
    #testing a cidr that is not assigned to group cs
    output = os.popen('python %s reverse '
                      '--group-permission=aaaa,cname,ptr,soa,ns '
                      '--cidr-block=192.168.1.0/24 -g cs -s %s -u %s -p %s '
                      '--config-file=%s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'USER ERROR: Trying to update permissions on cidr '
                     '192.168.1.0/24 not assigned to group cs.\n')
    output.close()

    #testing a record type that doesn't exist
    output = os.popen('python %s reverse '
                      '--group-permission=none '
                      '--cidr-block=192.168.1.0/24 -g cs -s %s -u %s -p %s '
                      '--config-file=%s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'CLIENT ERROR: Permission none does not exist.\n')
    output.close()

    #testing a group that doesn't exist
    output = os.popen('python %s reverse '
                      '--group-permission=aaaa,cname,ptr,soa,ns '
                      '--cidr-block=192.168.1.0/24 -g none -s %s -u %s -p %s '
                      '--config-file=%s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'CLIENT ERROR: Group none does not exist.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
