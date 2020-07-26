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

"""Regression test for dnsmkhost

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
from roster_user_tools  import roster_client_lib

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnsmkhost'

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

class TestDnsMkHost(unittest.TestCase):

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

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'main',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'main',
                                u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'main',
                                u'university.edu.',
                                view_name=u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'main',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
    self.core_instance.MakeZone(u'ipv6zone', u'main',
                                u'ip6.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view3')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view2')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'ipv6zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host2', u'forward_zone', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host1', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host2', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.11'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host4', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.10'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host5', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.17'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'cname', u'www.host5', u'forward_zone',
                                  {u'assignment_host':
                                      u'host5.university.edu.'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host6', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.8'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'www.host6', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.8'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'8',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host6.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'4',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host2.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'5',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host3.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'10',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host4.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'7',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host5.university.edu.'},
                                  view_name=u'test_view2')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testMakeHost(self):
    self.maxDiff = None
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')
    output = os.popen('python %s add -q -i 192.168.1.6 -z forward_zone -t '
                      'machine1 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s add -q -i 192.168.1.6 -z forward_zone -t '
                      'www.machine1 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s add -q -i 192.168.1.10 -z forward_zone -t '
                      '@ -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s findfirst -q --cidr-block 192.168.1.0/24 -z '
                      'forward_zone -t machine2 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s findfirst -q --cidr-block 192.168.1.0/24 -z '
                      'forward_zone -t machine3 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s findfirst -q --cidr-block 192.168.1.25 -z '
                      'forward_zone -t machine25 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ptr'),
        [{'target': u'8', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host6.university.edu.'},
         {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view2', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host2.university.edu.'},
         {'target': u'5', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host3.university.edu.'},
         {'target': u'10', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view2', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host4.university.edu.'},
         {'target': u'7', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view2', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host5.university.edu.'},
         {'target': u'6', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'machine1.university.edu.'},
         {'target': u'6', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'www.machine1.university.edu.'},
         {'target': u'10', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'university.edu.'},
         {u'assignment_host': u'machine2.university.edu.',
          'last_user': u'sharrell', 'record_type': u'ptr',
          'target': u'0', 'ttl': 3600, 'view_name': u'test_view',
          'zone_name': u'reverse_zone'},
         {u'assignment_host': u'machine3.university.edu.',
          'last_user': u'sharrell', 'record_type': u'ptr',
          'target': u'1', 'ttl': 3600, 'view_name': u'test_view',
          'zone_name': u'reverse_zone'},
          {u'assignment_host': u'machine25.university.edu.',
          'last_user': u'sharrell', 'record_type': u'ptr',
          'target': u'25', 'ttl': 3600, 'view_name': u'test_view',
          'zone_name': u'reverse_zone'},])
    self.assertEqual(self.core_instance.ListRecords(target=u'machine1'),
        [{'target': u'machine1', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.6'}])
    self.assertEqual(self.core_instance.ListRecords(target=u'machine2'),
        [{'target': u'machine2', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.0'}])
    self.assertEqual(self.core_instance.ListRecords(target=u'machine3'),
        [{'target': u'machine3', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.1'}])
    self.assertEqual(self.core_instance.ListRecords(target=u'machine25'),
        [{'target': u'machine25', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.25'}])

  def testMakeIPV6(self):
    self.core_instance.MakeReverseRangeZoneAssignment(u'ipv6zone',
        u'3ffe:0800:0000:0000:0000:0000:0000:0000/24')

    test_ipv6_addr = '3ffe:0800::0567'
    output = os.popen('python %s add -i 3ffe:0800::0567 -t '
                      'machine1 -z forward_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (EXEC, self.server_name,
                                                  USERNAME, PASSWORD,
                                                  USER_CONFIG))
    self.assertEqual(
        output.read(),
        'ADDED AAAA: machine1 zone_name: forward_zone view_name: '
        'test_view ttl: 3600\n'
        '    assignment_ip: 3ffe:0800:0000:0000:0000:0000:0000:0567\n'
        'ADDED PTR: 7.6.5.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.0.e.'
        'f.f.3.ip6.arpa. zone_name: ipv6zone view_name: test_view ttl: 3600\n'
        '    assignment_host: machine1.university.edu.\n')
    output.close()
    self.assertEqual(self.core_instance.ListRecords(target=u'machine1'),
        [{'target': u'machine1', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'assignment_ip': u'3ffe:0800:0000:0000:0000:0000:0000:0567'}])

  def testErrors(self):
    output = os.popen('python %s add -t t -i 192168414b -z'
                      'forward_zone -v test_view -s %s -u %s -p %s '
                      '--config-file %s' % (
                           EXEC, self.server_name, USERNAME, PASSWORD,
                           USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Incorrectly formatted IP address.\n')
    output.close()
    output = os.popen('python %s add -i 192.168.1.4 -t '
                      'machine1.university.edu. -z'
                      'forward_zone -v test_view -s %s -u %s -p %s '
                      '--config-file %s' % (
                           EXEC, self.server_name, USERNAME, PASSWORD,
                           USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Hostname cannot end with domain name.\n')
    output.close()
    output = os.popen('python %s add -i 192.168.1.6 -z forward_zone -t '
                      'machine1 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: No reverse zone found for "192.168.1.6"\n')
    output.close()
    output = os.popen('python %s add -t t -z test_zone -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The -i/--ip-address flag is required.\n')
    output.close()
    output = os.popen('python %s add -s %s -u %s -i 192.168.0.1 -z '
                      'reverse_zone '
                      '-v test_view -t machine1 '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: This tool requres a forward zone as an '
                     'argument. Reverse zones are handled automatically.\n')
    output.close()

    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      '192.168.1/24')
    output = os.popen('python %s findfirst --cidr-block 192.168.1.25 -z '
                      'forward_zone -t machine25 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    output.close()
    output = os.popen('python %s findfirst --cidr-block 192.168.1.25 -z '
                      'forward_zone -t machine25 -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'No available IP\'s in 192.168.1.25.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
