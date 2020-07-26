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

"""Regression test for dnsmkzone

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
EXEC='../roster-user-tools/scripts/dnsmkzone'
ZONE_OPTIONS_FILE = 'zone_options.txt'

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

class TestDnsMkZone(unittest.TestCase):

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
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)
    if( os.path.exists(ZONE_OPTIONS_FILE) ):
      os.remove(ZONE_OPTIONS_FILE)

  def testNoReverseRangeZoneAssignmentForMakeSubordinateZone(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z test_zone1 --cidr-block '
                      '192.168.1.0/24 --type main '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED REVERSE ZONE: zone_name: test_zone1 '
        'zone_type: main zone_origin: 1.168.192.in-addr.arpa. '
        'zone_options: None view_name: test_view\n'
        'ADDED REVERSE RANGE ZONE ASSIGNMENT: zone_name: test_zone1 '
        'cidr_block: 192.168.1.0/24 \n')
    output.close()

    output = os.popen('python %s reverse -v test_view -z test_zone2 --cidr-block '
                      '192.168.2.0/24 --type subordinate '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    #Note, since this is a subordinate zone, there is no added reverse range zone
    #assignment. The previous zone, a main zone, does have add a reverse
    #range zone assignment.
    self.assertEqual(output.read(),
        'ADDED REVERSE ZONE: zone_name: test_zone2 '
        'zone_type: subordinate zone_origin: 2.168.192.in-addr.arpa. '
        'zone_options: None view_name: test_view\n')
    output.close()

  def testMakeZoneWithBootstrap(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -v test_view -z test_zone1 --origin '
                      'dept1.univiersity.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s --bootstrap-zone' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone1 zone_type: main '
        'zone_origin: dept1.univiersity.edu. zone_options: None '
        'view_name: test_view\n'
        'ADDED SOA: @ zone_name: test_zone1 view_name: test_view ttl: 3600 '
        'refresh_seconds: 3600 expiry_seconds: 1814400 '
        'name_server: ns.dept1.univiersity.edu. minimum_seconds: 86400 '
        'retry_seconds: 600 serial_number: 3 '
        'admin_email: admin.dept1.univiersity.edu.\n'
        'ADDED NS: @ zone_name: test_zone1 view_name: test_view ttl: 3600 '
        'name_server: ns.dept1.univiersity.edu.\n')
    output.close()
    output = os.popen('python %s forward -v test_view -z test_zone2 --origin '
                      'dept2.univiersity.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s --bootstrap-zone '
                      '--bootstrap-nameserver=broserver.' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone2 zone_type: main '
        'zone_origin: dept2.univiersity.edu. zone_options: None '
        'view_name: test_view\n'
        'ADDED SOA: @ zone_name: test_zone2 view_name: test_view ttl: 3600 '
        'refresh_seconds: 3600 expiry_seconds: 1814400 '
        'name_server: broserver. minimum_seconds: 86400 '
        'retry_seconds: 600 serial_number: 3 '
        'admin_email: admin.dept2.univiersity.edu.\n'
        'ADDED NS: @ zone_name: test_zone2 view_name: test_view ttl: 3600 '
        'name_server: broserver.\n')
    output.close()
    output = os.popen('python %s forward -v test_view -z test_zone3 --origin '
                      'dept3.univiersity.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s --bootstrap-zone '
                      '--bootstrap-admin-email=bromail.' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone3 zone_type: main '
        'zone_origin: dept3.univiersity.edu. zone_options: None '
        'view_name: test_view\n'
        'ADDED SOA: @ zone_name: test_zone3 view_name: test_view ttl: 3600 '
        'refresh_seconds: 3600 expiry_seconds: 1814400 '
        'name_server: ns.dept3.univiersity.edu. minimum_seconds: 86400 '
        'retry_seconds: 600 serial_number: 3 '
        'admin_email: bromail.\n'
        'ADDED NS: @ zone_name: test_zone3 view_name: test_view ttl: 3600 '
        'name_server: ns.dept3.univiersity.edu.\n')
    output.close()

  def testMakeZoneWithView(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED FORWARD ZONE: zone_name: test_zone zone_type: '
                     'main zone_origin: dept.univiersity.edu. '
                     'zone_options: None view_name: test_view\n')
    output.close()

    self.assertEqual(self.core_instance.ListZones(),
        {u'test_zone':
            {u'test_view':
                {'zone_type': u'main', 'zone_options': '',
                 'zone_origin': u'dept.univiersity.edu.'}}})
    output = os.popen('python %s forward -z test_zone2 -v test_view --origin '
                      'dept2.univiersity.edu. --type main --dont-make-any '
                      '--options="recursion no;\n" '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone2 zone_type: main '
        'zone_origin: dept2.univiersity.edu. zone_options: recursion no;\n '
        'view_name: test_view\n')
    output.close()
    self.assertEqual(self.core_instance.ListZones(),
        {u'test_zone':
            {u'test_view':
                {'zone_type': u'main', 'zone_options': '',
                 'zone_origin': u'dept.univiersity.edu.'}},
         u'test_zone2':
             {u'test_view':
                 {'zone_type': u'main', 'zone_options': u'recursion no;',
                  'zone_origin': u'dept2.univiersity.edu.'}}})

    open(ZONE_OPTIONS_FILE, 'w').write('recursion no;\n')
    output = os.popen('python %s forward -z test_zone3 -v test_view --origin '
                      'dept3.univiersity.edu. --type main --dont-make-any '
                      '--file=%s -s %s -u %s -p %s --config-file %s' % (
                          EXEC, ZONE_OPTIONS_FILE, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED FORWARD ZONE: zone_name: test_zone3 zone_type: '
                     'main zone_origin: dept3.univiersity.edu. '
                     'zone_options: recursion no; view_name: test_view\n')
    output.close()
    self.assertEqual(self.core_instance.ListZones(),
        {u'test_zone':
            {u'test_view':
                {'zone_type': u'main', 'zone_options': '',
                 'zone_origin': u'dept.univiersity.edu.'}},
         u'test_zone2':
             {u'test_view':
                 {'zone_type': u'main', 'zone_options': u'recursion no;',
                  'zone_origin': u'dept2.univiersity.edu.'}},
         u'test_zone3':
             {u'test_view':
                 {'zone_type': u'main', 'zone_options': u'recursion no;',
                  'zone_origin': u'dept3.univiersity.edu.'}}})

  def testMakeZoneWithViewAny(self):
    self.core_instance.MakeView(u'any')
    output = os.popen('python %s forward -v any -z test_zone --origin '
                      'dept.university.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Cannot make view "any"\n')
    output.close()
    self.assertEqual(self.core_instance.ListZones(), {})

  def testMakeZoneWithEmptyView(self):
    self.core_instance.MakeView(u'any')
    output = os.popen('python %s forward -z test_zone --origin '
                      'dept.university.edu. --type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (EXEC,
                          self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: The -v/--view-name flag is '
                     'required.\n')
    output.close()
    self.assertEqual(self.core_instance.ListZones(), {})

  def testMakeReverseZoneOrigin(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--origin 168.192.in-addr.arpa. '
                      '--type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: main zone_origin: 168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/16 \n')
    output.close()

  def testMakeReverseZoneCidr(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--cidr-block 192.168/16 '
                      '--type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: main zone_origin: 168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/16 \n')
    output.close()

  def testmakeReverseZoneWeird(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--cidr-block 192.168/27 '
                      '--type main --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: main zone_origin: 0/27.168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/27 \n')
    output.close()

  def testMakeMultipleZonesWithSameZoneOriginError(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -z test_zone1 -v test_view --origin '
                      'dept.university.edu. --type main '
                      '-s %s -u %s -p %s --config-file %s' % (EXEC,
                          self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone1 zone_type: main '
        'zone_origin: dept.university.edu. zone_options: None view_name: test_view\n')
    output.close()
    output = os.popen('python %s forward -z test_zone2 -v test_view --origin '
                      'dept.university.edu. --type main '
                      '-s %s -u %s -p %s --config-file %s' % (EXEC,
                          self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    output_string = output.read()
    output.close()
    self.assertTrue('UNKNOWN ERROR(IntegrityError)' in output_string)
    self.assertTrue('Duplicate entry' in output_string)
    output = os.popen('python %s forward -z test_zone3 -v test_view --origin '
                      'dept.university.edu. --type subordinate '
                      '-s %s -u %s -p %s --config-file %s' % (EXEC,
                          self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone3 zone_type: subordinate '
        'zone_origin: dept.university.edu. zone_options: None view_name: test_view\n')
    output.close()

  def testErrors(self):
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. --type main '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The view specified does not exist.\n')
    output.close()
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -v test_view -z test_zone --type main '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The --origin flag is required.\n')
    output.close()
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The -t/--type flag is required.\n')
    output.close()
    output = os.popen('python %s reverse -v test_view -z reverse_zone --origin '
                      '168.192.in-addr.arpa. --cidr-block 192.168/16 '
                      '--type main '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: --cidr-block and --origin cannot be used '
                     'simultaneously.\n')
    output.close()
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--type main '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Either --cidr-block or --origin must be '
                     'used.\n')
    output.close()
    output = os.popen('python %s forward --origin test '
                      '-v view -s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The -z/--zone-name flag is required.\n')
    output.close()
    output = os.popen('python %s reverse -z test_rev -t main --origin foo.com '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Zone origin must terminate with "."\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
