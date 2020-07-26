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

Remove sure you are running this against a database that can be destroyed.

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
EXEC = '../roster-user-tools/scripts/dnsrmusergroup'


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

class Testdnsrmusergroup(unittest.TestCase):

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

  def testRemoveUserGroupUserGroupAssignments(self):
    self.core_instance.MakeUser(u'new_user', 128)
    self.core_instance.MakeUserGroupAssignment(u'new_user', u'cs')
    output = os.popen('python %s assignment -n new_user -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'REMOVED USER_GROUP_ASSIGNMENT: username: new_user group: cs\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'shuey': 64, u'new_user': 128, u'jcollins': 32,
                      u'tree_export_user': 0, u'sharrell': 128})
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs', u'eas'])
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'],
                      u'sharrell': [u'cs']})

  def testRemoveGroup(self):
    self.core_instance.MakeGroup(u'testgroup')
    output = os.popen('python %s group -g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED GROUP: group: testgroup\n')
    output.close()
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs', u'eas'])

  def testRemoveUser(self):
    self.core_instance.MakeUser(u'test_user', 128)
    output = os.popen('python %s user -n test_user -a 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED USER: username: test_user access_level: 128\n')
    output.close()
  def testRemoveuserGroupAssignment(self):
    self.core_instance.MakeUser(u'new_user', 128)
    self.core_instance.MakeUserGroupAssignment(u'new_user', u'cs')
    output = os.popen('python %s assignment -n new_user -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED USER_GROUP_ASSIGNMENT: username: new_user group: cs\n')
    output.close()
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'sharrell': [u'cs']})

  def testRemoveForwardPermission(self):
    self.core_instance.MakeGroup(u'testgroup')
    self.core_instance.MakeZone(u'test_zone', u'main', u'here.')
    self.core_instance.MakeForwardZonePermission(u'test_zone', u'testgroup',
                                                 [u'a', u'aaaa', u'cname',
                                                  u'ns'])
    output = os.popen('python %s forward -z test_zone -g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED FORWARD_ZONE_PERMISSION: zone_name: test_zone group: '
        'testgroup group_permission: [\'a\', \'aaaa\', \'cname\', \'ns\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [{'zone_name': u'bio.university.edu',
                                'group_permission': [u'a',u'aaaa']}],
                      u'cs': [{'zone_name': u'cs.university.edu',
                                 'group_permission': [u'a', u'aaaa', u'cname',
                                                      u'ns', u'soa']},
                                {'zone_name': u'eas.university.edu',
                                 'group_permission': [u'a', u'aaaa',
                                                      u'cname']}]})

  def testRemoveReverseRangeAssignment(self):
    self.core_instance.MakeGroup(u'testgroup')
    self.core_instance.MakeReverseRangePermission('192.168.1.4/30', u'testgroup',
                                                 [u'cname', u'ptr', u'soa'])

    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'cs': [{'cidr_block': u'192.168.0.0/24',
                               'group_permission': [u'cname', u'ns', u'ptr',
                                                    u'soa']}],
                      u'bio': [{'cidr_block': u'192.168.0.0/24',
                                'group_permission': [u'cname', u'ptr']},
                               {'cidr_block': u'192.168.1.0/24',
                                'group_permission': [u'ptr']}],
                      u'testgroup': [{'cidr_block': u'192.168.1.4/30',
                                      'group_permission': [u'cname', 
                                                           u'ptr', 
                                                           u'soa']}]})
    output = os.popen('python %s reverse -g testgroup '
                      '-b 192.168.1.4/30 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.4/30 '
        'group: testgroup group_permission: [\'cname\', \'ptr\', \'soa\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'cs': [{'cidr_block': u'192.168.0.0/24',
                               'group_permission': [u'cname', u'ns', u'ptr',
                                                    u'soa']}],
                      u'bio': [{'cidr_block': u'192.168.0.0/24',
                                'group_permission': [u'cname', u'ptr']},
                               {'cidr_block': u'192.168.1.0/24',
                                'group_permission': [u'ptr']}]})

  def testRemoveZoneAssignments(self):
    self.core_instance.MakeGroup(u'testgroup')
    self.core_instance.MakeReverseRangePermission('192.168.1.4/30', u'testgroup',
                                                 [u'cname', u'ptr', u'soa'])

    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'cs': [{'cidr_block': u'192.168.0.0/24',
                               'group_permission': [u'cname', u'ns', u'ptr',
                                                    u'soa']}],
                      u'bio': [{'cidr_block': u'192.168.0.0/24',
                                'group_permission': [u'cname', u'ptr']},
                               {'cidr_block': u'192.168.1.0/24',
                                'group_permission': [u'ptr']}],
                      u'testgroup': [{'cidr_block': u'192.168.1.4/30',
                                      'group_permission': [u'cname', 
                                                           u'ptr', 
                                                           u'soa']}]})
    output = os.popen('python %s reverse -b 192.168.1.4/30 '
                      '-g testgroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REMOVED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.4/30 '
        'group: testgroup group_permission: [\'cname\', \'ptr\', \'soa\']\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
        {u'cs': [{'group_permission': [u'cname', u'ns', u'ptr', u'soa'], 
                  'cidr_block': u'192.168.0.0/24'}], 
         u'bio': [{'group_permission': [u'cname', u'ptr'], 
                   'cidr_block': u'192.168.0.0/24'}, 
                  {'group_permission': [u'ptr'], 
                   'cidr_block': u'192.168.1.0/24'}]}) 

  def testErrors(self):
    self.core_instance.MakeGroup(u'testgroup')
    self.core_instance.MakeZone(u'test_zone1', u'main', u'here1.')
    self.core_instance.MakeZone(u'test_zone2', u'main', u'here2.')
    self.core_instance.MakeReverseRangePermission('192.168.1.4/30', u'testgroup',
                                                 [])
    self.core_instance.MakeForwardZonePermission(u'test_zone2', u'testgroup',
                                                 [])

    #Trying to remove permissions on a cidr not assigned to testgroup
    output = os.popen('python %s reverse -g testgroup '
                      '-b 192.168.0.4/30 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: Permissions not removed\n')
    output.close()

    #Trying to remove permissions on a cidr in which testgroup has no permissions
    output = os.popen('python %s reverse -g testgroup '
                      '-b 192.168.1.4/30 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: Permissions not removed\n')
    output.close()

    #Trying to remove permissions on a zone not assigned to testgroup
    output = os.popen('python %s forward -g testgroup '
                      '-z test_zone1 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: Permissions not removed\n')
    output.close()

    #Trying to remove permissions on a zone in which testgroup has no permissions
    output = os.popen('python %s forward -g testgroup '
                      '-z test_zone2 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'CLIENT ERROR: Permissions not removed\n')
    output.close()

    output = os.popen('python %s user -n jcollins -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -g/--group flag cannot be used with the user '
        'command.\n')
    output.close()
    output = os.popen('python %s user -n wronguser '
                      '-a 128 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Username does not exist.\n')
    output.close()
    output = os.popen('python %s assignment -n newuser '
                      '-g fakegroup '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Group does not exist.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
