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

"""Unittest for audit logger

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import cPickle
import datetime
import os
import time
import unicodedata
import unittest

from roster_core import audit_log

import roster_core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEMP_LOG = 'temp_log'
# Change SYSLOG according to your distribution and specific version
SYSLOG = ['/var/log/messages', '/var/log/syslog']

class TestAuditLog(unittest.TestCase):

  def setUp(self):
    config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.db_instance = db_instance
    self.audit_log_instance = audit_log.AuditLog(db_instance=db_instance,
                                                 log_file_name=TEMP_LOG)

  def testPrettyPrintLogString(self):
    self.assertEqual(self.audit_log_instance._PrettyPrintLogString(
      'sharrell', 'MakeUser', {'audit_args':
                                  {'user': 'ahoward', 'user_level': 64},
                               'replay_args': ['ahoward', 64]}, True,
      '2009-04-28 10:46:50'),  'User sharrell SUCCEEDED while executing '
      "MakeUser with data {'user_level': 64, 'user': 'ahoward'} at "
      '2009-04-28 10:46:50')

  def testLogToSyslog(self):
    current_time = time.time()
    unittest_string = 'unittest %s' % current_time
    self.audit_log_instance._LogToSyslog(unittest_string)
    found = False
    for syslogfile in SYSLOG:
      try:
        lines = open(syslogfile, 'r').readlines()
      except:
        continue
      for line in lines:
        if( line.endswith('dnsManagement: %s' % unittest_string) != -1):
          found = True
          break
    if( not found ):
      #If you get here and the test fails, check to make sure that
      #the permissions on the syslog file are such that anyone can
      #read it.
      self.fail()

    unittest_string = u'unicode \xc6 unittest %s' % current_time
    self.audit_log_instance._LogToSyslog(unittest_string)
    unittest_string = unicodedata.normalize('NFKD', unittest_string).encode(
        'ASCII', 'replace')
    found = False
    for syslogfile in SYSLOG:
      try:
        lines = open(syslogfile, 'r').readlines()
      except:
        continue
      for line in lines:
        if( line.endswith('dnsManagement: %s' % unittest_string) != -1):
          found = True
          break
    if( not found ):
      self.fail()

  def testLogToDatabase(self):
    audit_log_id = self.audit_log_instance._LogToDatabase(
        u'sharrell', u'MakeUser', u'user=ahoward user_level=64', True,
        datetime.datetime(2009, 4, 28, 10, 46, 50), False)
    self.assertEqual(audit_log_id, 1)

    audit_log_dict = self.db_instance.GetEmptyRowDict('audit_log')
    self.db_instance.StartTransaction()
    try:
      audit_row = self.db_instance.ListRow('audit_log', audit_log_dict)
      self.assertEqual(audit_row[0]['action'], u'MakeUser')
      self.assertEqual(audit_row[0]['audit_log_timestamp'],
                       datetime.datetime(2009, 4, 28, 10, 46, 50))
      self.assertEqual(cPickle.loads(str(audit_row[0]['data'])),
                       u'user=ahoward user_level=64')
      self.assertEqual(audit_row[0]['audit_log_user_name'], u'sharrell')
      self.assertEqual(audit_row[0]['success'], 1)
    finally:
      self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    try:
      audit_log_id = self.audit_log_instance._LogToDatabase(
          u'sharrell', u'MakeUser', u'user=scook user_level=64', True,
          datetime.datetime(2009, 4, 28, 10, 49, 50), True)
      self.assertEqual(audit_log_id, 2)
      audit_log_dict = self.db_instance.GetEmptyRowDict('audit_log')
      audit_log_dict['audit_log_id'] = audit_log_id
      audit_row = self.db_instance.ListRow('audit_log', audit_log_dict)
      self.assertEqual(audit_row[0]['action'], u'MakeUser')
      self.assertEqual(audit_row[0]['audit_log_timestamp'],
                       datetime.datetime(2009, 4, 28, 10, 49, 50))
      self.assertEqual(cPickle.loads(str(audit_row[0]['data'])),
                      u'user=scook user_level=64')
      self.assertEqual(audit_row[0]['audit_log_user_name'], u'sharrell')
      self.assertEqual(audit_row[0]['success'], 1)
    finally:
        self.db_instance.EndTransaction()


  def testLogToFile(self):
    current_time = time.time()
    unittest_string = 'unittest %s' % current_time
    try:
      self.audit_log_instance._LogToFile(unittest_string)
      lines = open(TEMP_LOG, 'r').readlines()
      for line in lines:
        if( line.endswith(unittest_string) != -1):
          break
      else:
        self.fail()
    finally:
      os.remove(TEMP_LOG)


if( __name__ == '__main__' ):
  unittest.main()
