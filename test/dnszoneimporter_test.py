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

"""Regression test for dnszoneimporter

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

USER_CONFIG = 'test_data/roster.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-config-manager/scripts/dnszoneimporter'

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

class TestDnsZoneImport(unittest.TestCase):

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
    self.core_instance.MakeView(u'test_view1')
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeZone(u'sub.university.lcl', u'main',
                                u'sub.university.lcl.', view_name=u'test_view1')
    self.core_instance.MakeZone(u'0.168.192.in-addr.arpa', u'main',
                                u'0.168.192.in-addr.arpa.',
                                view_name=u'test_view1')
    self.core_instance.MakeZone(u'8.0.e.f.f.3.ip6.arpa', u'main',
                                u'8.0.e.f.f.3.ip6.arpa.', 
                                view_name=u'test_view1')
    self.core_instance.MakeReverseRangeZoneAssignment(
        u'0.168.192.in-addr.arpa', u'192.168.0/24')
    self.core_instance.MakeReverseRangeZoneAssignment(
        u'8.0.e.f.f.3.ip6.arpa', u'3ffe:0800:0000:0000:0000:0000:0000:0000/24')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testErrors(self):
    output = os.popen('python %s -f test_data/test_zone.db -v no_view '
                      '-u %s --config-file %s -z sub.university.lcl' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(output.read(),
        'Loading in test_data/test_zone.db\n'
        'View no_view does not exist.\n')
    output.close()
    output = os.popen('python %s -f test_data/test_zone.db -v any '
                      '-u %s --config-file %s -z no_zone' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(output.read(),
        'Loading in test_data/test_zone.db\n'
        'Zone no_zone does not exist.\n')
    output.close()

  def testImportForwardZoneToAny(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db -v any '
                      '-u %s --config-file %s -z sub.university.lcl' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                     '17 total records added\n')
    output.close()

    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 796, u'refresh_seconds': 10800, 'target': u'@', 
        u'name_server': u'ns.university.lcl.', u'retry_seconds': 3600, 
        'ttl': 3600, u'minimum_seconds': 86400, 'record_type': u'soa', 
        'view_name': u'test_view1', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'admin_email': u'hostmain.ns.university.lcl.', 
        u'expiry_seconds': 3600000}, {'target': u'@', 
        u'name_server': u'ns.sub.university.lcl.', 'ttl': 3600, 
        'record_type': u'ns', 'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl'}, {'target': u'@', 
        u'name_server': u'ns2.sub.university.lcl.', 'ttl': 3600, 
        'record_type': u'ns', 'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl'}, {'target': u'@', 'ttl': 3600, 
        u'priority': 10, 'record_type': u'mx', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'mail_server': u'mail1.sub.university.lcl.'}, {'target': u'@', 
        'ttl': 3600, u'priority': 20, 'record_type': u'mx', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'mail_server': u'mail2.sub.university.lcl.'}, 
        {'target': u'@', 'ttl': 3600, 'record_type': u'txt', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'quoted_text': u'"Contact 1:  Stephen Harrell (sharrell@university.lcl)"'}, 
        {'target': u'@', 'ttl': 3600, 'record_type': u'a', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'assignment_ip': u'192.168.0.1'}, 
        {'target': u'ns', 'ttl': 3600, 'record_type': u'a', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.103'}, 
        {'target': u'desktop-1', 'ttl': 3600, 'record_type': u'aaaa', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'assignment_ip': u'3ffe:0800:0000:0000:02a8:79ff:fe32:1982'}, 
        {'target': u'desktop-1', 'ttl': 3600, 'record_type': u'a', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.100'}, 
        {'target': u'ns2', 'ttl': 3600, 'record_type': u'a', 
        'view_name': u'any', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.104'}, 
        {'target': u'ns2', 'ttl': 3600, u'hardware': u'PC', 
        'record_type': u'hinfo', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'os': u'NT'}, {'target': u'www', 'ttl': 3600, 
        'record_type': u'cname', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'assignment_host': u'sub.university.lcl.'}, {'target': u'localhost', 
        'ttl': 3600, 'record_type': u'a', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'assignment_ip': u'127.0.0.1'}, {'target': u'www.data', 
        'ttl': 3600, 'record_type': u'cname', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'assignment_host': u'ns.university.lcl.'}, {'target': u'mail1', 
        'ttl': 3600, 'record_type': u'a', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'assignment_ip': u'192.168.1.101'}, {'target': u'mail2', 
        'ttl': 3600, 'record_type': u'a', 'view_name': u'any', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'assignment_ip': u'192.168.1.102'}])

  def testImportForwardZoneToView(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db -v test_view1 '
                      '-u %s --config-file %s -z sub.university.lcl' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                     '17 total records added\n')
    output.close()

    #fix indenting
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 795, u'refresh_seconds': 10800, 'target': u'@', 
        u'name_server': u'ns.university.lcl.', u'retry_seconds': 3600, 
        'ttl': 3600, u'minimum_seconds': 86400, 'record_type': u'soa', 
        'view_name': u'test_view1', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'admin_email': u'hostmain.ns.university.lcl.', 
        u'expiry_seconds': 3600000}, {'target': u'@', 
        u'name_server': u'ns.sub.university.lcl.', 'ttl': 3600, 
        'record_type': u'ns', 'view_name': u'test_view1', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl'}, 
        {'target': u'@', u'name_server': u'ns2.sub.university.lcl.', 
        'ttl': 3600, 'record_type': u'ns', 'view_name': u'test_view1', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl'}, 
        {'target': u'@', 'ttl': 3600, u'priority': 10, 'record_type': u'mx', 
        'view_name': u'test_view1', 'last_user': u'sharrell', 
        'zone_name': u'sub.university.lcl', 
        u'mail_server': u'mail1.sub.university.lcl.'}, 
        {'target': u'@', 'ttl': 3600, u'priority': 20, 
        'record_type': u'mx', 'view_name': u'test_view1', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
        u'mail_server': u'mail2.sub.university.lcl.'}, {'target': u'@', 
        'ttl': 3600, 'record_type': u'txt', 'view_name': u'test_view1', 
        'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'quoted_text': u'"Contact 1:  Stephen Harrell (sharrell@university.lcl)"'}, 
         {'target': u'@', 'ttl': 3600, 'record_type': u'a', 
         'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.0.1'}, 
         {'target': u'ns', 'ttl': 3600, 'record_type': u'a', 
         'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.103'}, 
         {'target': u'desktop-1', 'ttl': 3600, 'record_type': u'aaaa', 
         'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', 
         u'assignment_ip': u'3ffe:0800:0000:0000:02a8:79ff:fe32:1982'}, 
         {'target': u'desktop-1', 'ttl': 3600, 'record_type': u'a', 
         'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.100'}, 
         {'target': u'ns2', 'ttl': 3600, 'record_type': u'a', 
         'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.104'}, 
         {'target': u'ns2', 'ttl': 3600, u'hardware': u'PC', 
         'record_type': u'hinfo', 'view_name': u'test_view1', 
         'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'os': u'NT'}, {'target': u'www', 'ttl': 3600, 
         'record_type': u'cname', 'view_name': u'test_view1', 
         'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'assignment_host': u'sub.university.lcl.'}, {'target': u'localhost', 
         'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view1', 
         'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'assignment_ip': u'127.0.0.1'}, {'target': u'www.data', 
         'ttl': 3600, 'record_type': u'cname', 'view_name': u'test_view1', 
         'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'assignment_host': u'ns.university.lcl.'}, {'target': u'mail1', 
         'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view1', 
         'last_user': u'sharrell', 'zone_name': u'sub.university.lcl', 
         u'assignment_ip': u'192.168.1.101'}, {'target': u'mail2', 'ttl': 3600, 
         'record_type': u'a', 'view_name': u'test_view1', 'last_user': u'sharrell', 
         'zone_name': u'sub.university.lcl', u'assignment_ip': u'192.168.1.102'}])

  def testImportReverseIPV6ZoneToAny(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                      '-v any -u %s --config-file %s '
                      '-z 8.0.e.f.f.3.ip6.arpa' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'Loading in test_data/test_reverse_ipv6_zone.db\n'
        '5 records loaded from zone test_data/test_reverse_ipv6_zone.db\n'
        '5 total records added\n')

    self.assertEqual(self.core_instance.ListRecords(), 
         [{u'serial_number': 6, u'refresh_seconds': 10800, 'target': u'@', 
          u'name_server': u'ns.university.lcl.', u'retry_seconds': 3600, 'ttl': 86400, 
          u'minimum_seconds': 86400, 'record_type': u'soa', 'view_name': u'test_view1', 
          'last_user': u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'admin_email': 
          u'hostmain.university.lcl.', u'expiry_seconds': 3600000}, {'target': 
          u'@', u'name_server': u'ns.university.lcl.', 'ttl': 86400, 'record_type': 
          u'ns', 'view_name': u'any', 'last_user': u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa'}, 
          {'target': u'@', u'name_server': u'ns2.university.lcl.', 'ttl': 86400, 
          'record_type': u'ns', 'view_name': u'any', 'last_user': u'sharrell', 'zone_name': 
          u'8.0.e.f.f.3.ip6.arpa'}, {'target': u'2.8.9.1.2.3.e.f.f.f.9.7.8.a.2.0.0.0.0.0.0.0.0.0.0.0', 
          'ttl': 86400, 'record_type': u'ptr', 'view_name': u'any', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'assignment_host': 
          u'router.university.lcl.'}, {'target': u'0.8.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0', 
          'ttl': 86400, 'record_type': u'ptr', 'view_name': u'any', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'assignment_host': 
          u'desktop-1.university.lcl.'}])

  def testImportReverseIPV6ZoneToView(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                      '-v test_view1 -u %s --config-file %s '
                      '-z 8.0.e.f.f.3.ip6.arpa' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'Loading in test_data/test_reverse_ipv6_zone.db\n'
        '5 records loaded from zone test_data/test_reverse_ipv6_zone.db\n'
        '5 total records added\n')
    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 5, u'refresh_seconds': 10800, 'target': u'@', u'name_server': 
          u'ns.university.lcl.', u'retry_seconds': 3600, 'ttl': 86400, u'minimum_seconds': 
          86400, 'record_type': u'soa', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'admin_email': u'hostmain.university.lcl.', 
          u'expiry_seconds': 3600000}, {'target': u'@', u'name_server': u'ns.university.lcl.', 
          'ttl': 86400, 'record_type': u'ns', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa'}, {'target': u'@', u'name_server': 
          u'ns2.university.lcl.', 'ttl': 86400, 'record_type': u'ns', 'view_name': 
          u'test_view1', 'last_user': u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa'}, 
          {'target': u'2.8.9.1.2.3.e.f.f.f.9.7.8.a.2.0.0.0.0.0.0.0.0.0.0.0', 'ttl': 
          86400, 'record_type': u'ptr', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'assignment_host': 
          u'router.university.lcl.'}, {'target': u'0.8.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0', 
          'ttl': 86400, 'record_type': u'ptr', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'8.0.e.f.f.3.ip6.arpa', u'assignment_host': 
          u'desktop-1.university.lcl.'}])

  def testImportReverseZoneToAny(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_reverse_zone.db '
                      '-v any -u %s --config-file %s '
                      '-z 0.168.192.in-addr.arpa' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'Loading in test_data/test_reverse_zone.db\n'
        '6 records loaded from zone test_data/test_reverse_zone.db\n'
        '6 total records added\n')
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 6, u'refresh_seconds': 10800, 'target': u'@', u'name_server': 
          u'ns.university.lcl.', u'retry_seconds': 3600, 'ttl': 86400, u'minimum_seconds': 
          86400, 'record_type': u'soa', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', u'admin_email': u'hostmain.university.lcl.', 
          u'expiry_seconds': 3600000}, {'target': u'@', u'name_server': u'ns.university.lcl.', 
          'ttl': 86400, 'record_type': u'ns', 'view_name': u'any', 'last_user': u'sharrell', 
          'zone_name': u'0.168.192.in-addr.arpa'}, {'target': u'@', u'name_server': 
          u'ns2.university.lcl.', 'ttl': 86400, 'record_type': u'ns', 'view_name': 
          u'any', 'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa'}, 
          {'target': u'1', 'ttl': 86400, 'record_type': u'ptr', 'view_name': u'any', 
          'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', u'assignment_host': 
          u'router.university.lcl.'}, {'target': u'11', 'ttl': 86400, 'record_type': 
          u'ptr', 'view_name': u'any', 'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', 
          u'assignment_host': u'desktop-1.university.lcl.'}, {'target': u'12', 'ttl': 
          86400, 'record_type': u'ptr', 'view_name': u'any', 'last_user': u'sharrell', 
          'zone_name': u'0.168.192.in-addr.arpa', u'assignment_host': u'desktop-2.university.lcl.'}])

  def testImportReverseZoneToView(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_reverse_zone.db '
                      '-v test_view1 -u %s --config-file %s '
                      '-z 0.168.192.in-addr.arpa' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'Loading in test_data/test_reverse_zone.db\n'
        '6 records loaded from zone test_data/test_reverse_zone.db\n'
        '6 total records added\n')
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 5, u'refresh_seconds': 10800, 'target': u'@', u'name_server': 
          u'ns.university.lcl.', u'retry_seconds': 3600, 'ttl': 86400, u'minimum_seconds': 
          86400, 'record_type': u'soa', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', u'admin_email': u'hostmain.university.lcl.', 
          u'expiry_seconds': 3600000}, {'target': u'@', u'name_server': u'ns.university.lcl.', 
          'ttl': 86400, 'record_type': u'ns', 'view_name': u'test_view1', 'last_user': 
          u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa'}, {'target': u'@', 
          u'name_server': u'ns2.university.lcl.', 'ttl': 86400, 'record_type': u'ns', 
          'view_name': u'test_view1', 'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa'}, 
          {'target': u'1', 'ttl': 86400, 'record_type': u'ptr', 'view_name': u'test_view1', 
          'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', u'assignment_host': 
          u'router.university.lcl.'}, {'target': u'11', 'ttl': 86400, 'record_type': 
          u'ptr', 'view_name': u'test_view1', 'last_user': u'sharrell', 'zone_name': 
          u'0.168.192.in-addr.arpa', u'assignment_host': u'desktop-1.university.lcl.'}, 
          {'target': u'12', 'ttl': 86400, 'record_type': u'ptr', 'view_name': u'test_view1', 
          'last_user': u'sharrell', 'zone_name': u'0.168.192.in-addr.arpa', u'assignment_host': 
          u'desktop-2.university.lcl.'}])

if( __name__ == '__main__' ):
      unittest.main()
