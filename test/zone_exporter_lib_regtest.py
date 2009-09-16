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

"""Regression test for zone_exporter_lib.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import unittest

import roster_core
from roster_config_manager import zone_exporter_lib
from roster_config_manager import zone_importer_lib


CONFIG_FILE = 'test_data/roster_server.conf'
ZONE_FILE = 'test_data/test_zone.db'
REVERSE_ZONE_FILE = 'test_data/test_reverse_zone.db'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'

class TestZoneExport(unittest.TestCase):

  def setUp(self):
    config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.CommitTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.CommitTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(u'sharrell', config_instance)
    importer_instance = zone_importer_lib.ZoneImport(ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell',
                                                            u'external')
    importer_instance.MakeRecordsFromZone()
    importer_instance = zone_importer_lib.ZoneImport(REVERSE_ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell',
                                                            u'external')
    importer_instance.MakeRecordsFromZone()

  def testGetRecordsForZone(self):
    self.core_instance.MakeRecord(u'a', u'desktop-2',
                                  u'sub.university.edu',
                                  {u'assignment_ip': '192.168.2.102'},
                                  view_name=u'any')
    records = self.core_instance.ListRecords(zone_name=u'sub.university.edu')
    self.assertEqual(zone_exporter_lib.FormatRecordsForZone(
      unsorted_records=records, origin='@'),
                     {'bulk': [
                         {'target': u'@', 'ttl': 3600,
                          'record_type': u'a', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'assignment_ip': u'192.168.0.1'},
                         {'target': u'desktop-1',
                          'ttl': 3600,
                          'record_type': u'a', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'assignment_ip': u'192.168.1.100'},
                         {'target': u'desktop-1',
                          'ttl': 3600,
                          u'hardware': u'PC', 'record_type': u'hinfo',
                          'view_name': u'external', 'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu', u'os': u'NT'},
                         {'target': u'desktop-2',
                          'ttl': 3600,
                          'record_type': u'a', 'view_name': u'any',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'assignment_ip': u'192.168.2.102'},
                         {'target': u'localhost',
                           'ttl': 3600, 'record_type': u'a',
                           'view_name': u'external', 'last_user': u'sharrell',
                           'zone_name': u'sub.university.edu',
                           u'assignment_ip': u'127.0.0.1'},
                         {'target': u'www', 'ttl': 3600,
                          'record_type': u'cname', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'assignment_host': u'sub.university.edu.'}],
                      u'soa': [
                         {u'serial_number': 804, u'refresh_seconds': 10800,
                          'target': u'@',
                          u'name_server': u'ns.university.edu.',
                          u'retry_seconds': 3600, 'ttl': 3600,
                          u'minimum_seconds': 86400, 'record_type': u'soa',
                          'view_name': u'external', 'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'admin_email': u'hostmaster.ns.university.edu.',
                          u'expiry_seconds': 3600000}],
                      u'ns': [
                         {'target': u'@',
                          u'name_server': u'ns.university.edu.', 'ttl': 3600,
                          'record_type': u'ns', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu'},
                         {'target': u'@',
                          u'name_server': u'ns2.university.edu.', 'ttl': 3600,
                          'record_type': u'ns', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name':u'sub.university.edu'}],
                      u'txt': [
                         {'target': u'@', 'ttl': 3600,
                          'record_type': u'txt', 'view_name': u'external',
                          'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'quoted_text': u'"Contact 1:  Stephen Harrell '
                                          u'(sharrell@university.edu)"'}],
                      u'mx': [
                         {'target': u'@', 'ttl': 3600,
                          u'priority': 10, 'record_type': u'mx',
                          'view_name': u'external', 'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'mail_server': u'mail1.university.edu.'},
                         {'target': u'@', 'ttl': 3600,
                          u'priority': 20, 'record_type': u'mx',
                          'view_name': u'external', 'last_user': u'sharrell',
                          'zone_name': u'sub.university.edu',
                          u'mail_server': u'mail2.university.edu.'}]})


  def testMakeZoneString(self):
    records = self.core_instance.ListRecords(zone_name=u'sub.university.edu')
    argument_definitions = self.core_instance.ListRecordArgumentDefinitions()
    self.assertEqual(zone_exporter_lib.MakeZoneString(
        records, u'sub.university.edu.', argument_definitions),
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN sub.university.edu.\n'
        '@ 3600 in soa ns.university.edu. '
            'hostmaster.ns.university.edu. 804 10800 3600 3600000 86400\n'
        '@ 3600 in ns ns.university.edu.\n'
        '@ 3600 in ns ns2.university.edu.\n'
        '@ 3600 in mx 10 mail1.university.edu.\n'
        '@ 3600 in mx 20 mail2.university.edu.\n'
        '@ 3600 in txt "Contact 1:  Stephen Harrell '
            '(sharrell@university.edu)"\n'
        '@ 3600 in a 192.168.0.1\n'
        'desktop-1 3600 in a 192.168.1.100\n'
        'desktop-1 3600 in hinfo PC NT\n'
        'localhost 3600 in a 127.0.0.1\n'
        'www 3600 in cname sub.university.edu.\n')


if( __name__ == '__main__' ):
  unittest.main()
