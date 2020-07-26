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

"""Regression test for dnsmkusergroup

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
EXEC = '../roster-user-tools/scripts/dnsmkusergroup'


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

  def testMakeUserGroupUserGroupAssignments(self):
    output = os.popen('python %s user -n new_user '
                      '-a 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED USER: username: new_user access_level: 128\n')
    output.close()
    output = os.popen('python %s assignment -n new_user -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: new_user group: cs\n')
    output.close()
    output = os.popen('python %s assignment -n new_user -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: User-Group assignment "new_user-cs" already exists\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'shuey': 64, u'new_user': 128, u'jcollins': 32,
                      u'tree_export_user': 0, u'sharrell': 128})
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs', u'eas'])
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'new_user': [u'cs'],
                      u'sharrell': [u'cs']})

  def testMakeUserGroupUserGroupAssignmentsWithStringAccessLevel(self):
    output = os.popen('python %s user -n new_dns_admin '
                      '-a dns_admin '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED USER: username: new_dns_admin access_level: 128\n')
    output.close()
    output = os.popen('python %s user -n new_unlocked_user '
                      '-a unlocked_user '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED USER: username: new_unlocked_user access_level: 64\n')
    output.close()
    output = os.popen('python %s user -n new_user '
                      '-a user '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED USER: username: new_user access_level: 32\n')
    output.close()

    output = os.popen('python %s assignment -n new_user -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: new_user group: cs\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'shuey': 64, u'new_user': 128, u'jcollins': 32,
                      u'tree_export_user': 0, u'sharrell': 128, u'new_dns_admin': 128,
                      u'new_unlocked_user': 64, u'new_user': 32})
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs', u'eas'])
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'new_user': [u'cs'],
                      u'sharrell': [u'cs']})

  def testMakeUserWithZone(self):
    self.core_instance.MakeZone(u'test_zone', u'main', u'here.')
    output = os.popen('python %s group -g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED GROUP: group: testgroup\n')
    output.close()
    output = os.popen('python %s user -n new_user -a 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED USER: username: new_user access_level: 128\n')
    output.close()
    output = os.popen('python %s assignment -n new_user -g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: new_user group: testgroup\n')
    output.close()
    output = os.popen('python %s forward -z test_zone -g testgroup '
                      '--group-permission a,aaaa,cname '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED FORWARD_ZONE_PERMISSION: zone_name: test_zone group: '
        'testgroup group_permission: [\'a\', \'aaaa\', \'cname\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [{'zone_name': u'bio.university.edu',
                                'group_permission': [u'a', u'aaaa']}],
                      u'testgroup': [{'zone_name': u'test_zone',
                                      'group_permission': [u'a', u'aaaa',
                                                           u'cname']}],
                      u'cs': [{'zone_name': u'cs.university.edu',
                                 'group_permission': [u'a', u'aaaa', u'cname',
                                                      u'ns', u'soa']},
                                {'zone_name': u'eas.university.edu',
                                 'group_permission': [u'a', u'aaaa',
                                                      u'cname']}]})
    output = os.popen('python %s user -n newuser --access-level 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED USER: username: newuser access_level: 128\n')
    output.close()
    output = os.popen('python %s assignment -n newuser -g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: newuser group: testgroup\n')
    output.close()
    output = os.popen('python %s reverse -g testgroup -z test_zone '
                      '-b 192.168.1.4/30 --group-permission cname '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: The -z/--zone-name flag cannot be used with the reverse '
        'command.\n')
    output.close()
    output = os.popen('python %s reverse -g testgroup '
                      '-b 192.168.1.4/30 --group-permission cname,ptr '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.4/30 '
        'group: testgroup group_permission: [\'cname\', \'ptr\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio':
                          [{'cidr_block': u'192.168.0.0/24',
                            'group_permission': [u'cname', u'ptr']},
                           {'cidr_block': u'192.168.1.0/24',
                            'group_permission': [u'ptr']}],
                      u'testgroup':
                          [{'cidr_block': u'192.168.1.4/30',
                            'group_permission': [u'cname', u'ptr']}],
                      u'cs': [{'cidr_block': u'192.168.0.0/24',
                                 'group_permission': [u'cname', u'ns', u'ptr',
                                                      u'soa']}]})

  def testMakeZoneAssignments(self):
    self.core_instance.MakeGroup(u'test_group')
    self.core_instance.MakeZone(u'test_zone', u'main', u'here.')
    output = os.popen('python %s reverse -z test_zone -b '
                      '192.168.1.0/24 -g test_group --group-permission '
                      'cname,ptr -s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: The -z/--zone-name flag cannot be used with the reverse '
        'command.\n')
    output.close()
    output = os.popen('python %s reverse -b 192.168.1.0/24 '
                      '-g test_group --group-permission cname,ptr,ns '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.0/24 '
        'group: test_group group_permission: [\'cname\', \'ptr\', \'ns\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio':
                          [{'cidr_block': u'192.168.0.0/24',
                            'group_permission': [u'cname', u'ptr']},
                           {'cidr_block': u'192.168.1.0/24',
                            'group_permission': [u'ptr']}],
                      u'test_group':
                          [{'cidr_block': u'192.168.1.0/24',
                            'group_permission': [u'cname', u'ptr', u'ns']}],
                      u'cs':
                          [{'cidr_block': u'192.168.0.0/24',
                            'group_permission': [u'cname', u'ns', u'ptr',
                                                 u'soa']}]})

  def testMakeGroup(self):
    output = os.popen('python %s group -g test_group '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'ADDED GROUP: group: test_group\n')
    output.close()
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs',
                                                       u'eas', u'test_group'])


  def testErrors(self):
    output = os.popen('python %s user -n jcollins '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -a/--access-level flag is required.\n')
    output.close()
    output = os.popen('python %s user -n dchayes '
                      '-s %s -u %s -a super-user -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ERROR: KeyError: \'super-user\'\n')
    output.close()
    output = os.popen('python %s user -n jcollins -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -g/--group flag cannot be used with the user '
        'command.\n')
    output.close()
    output = os.popen('python %s user -n jcollins '
                      '-a 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Username already exists.\n')
    output.close()
    output = os.popen('python %s assignment -n newuser '
                      '-g fakegroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Group does not exist.\n')
    output.close()
    self.core_instance.MakeZone(u'test_zone', u'main', u'here.')
    self.core_instance.MakeGroup(u'testgroup')
    output = os.popen('python %s forward '
                      '-g testgroup -z test_zone --group-permission x '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'USER ERROR: Invalid data type GroupPermission for '
        'group_forward_permissions_group_permission: x\n')
    output.close()
    # check duplicate group permission assignment
    output = os.popen('python %s forward -z test_zone -g testgroup '
                      '--group-permission soa,ns,soa -s %s -u %s -p %s '
                      '--config-file %s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Duplicate permission: soa\n')
    output.close()

    # also check duplicate reverse range group permission
    output = os.popen('python %s reverse -b 192.168.0.1/24 -g testgroup '
                      '--group-permission soa,ptr,soa -s %s -u %s -p %s '
                      '--config-file %s' % (EXEC, self.server_name, USERNAME,
                                            PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Duplicate permission found: soa\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
