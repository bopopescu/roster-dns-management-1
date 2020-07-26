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

"""Regression test for server check

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'

import ConfigParser
import datetime
import getpass
import iscpy
import os
import shutil
import unittest
import roster_core
import tarfile

from roster_config_manager import config_lib
from roster_config_manager import tree_exporter
from roster_core import errors

CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
SSH_USER = unicode(getpass.getuser())

class TestConfigLib(unittest.TestCase):

  def setUp(self):
    if( not os.path.exists(TESTDIR) ):
      os.system('mkdir %s' % TESTDIR)
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.root_config_dir = self.config_instance.config_file['exporter']['root_config_dir'].rstrip('/')
    self.backup_dir = self.config_instance.config_file['exporter']['backup_dir'].rstrip('/')
    
    db_instance = self.config_instance.GetDb()
    
    db_instance.CreateRosterDatabase()
    
    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    
    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)
    
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')

    self.core_instance.MakeACL(u'internal', u'127.0.0.1')
    self.core_instance.MakeView(u'external')
    self.core_instance.MakeDnsServer(u'localhost', SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'255.254.253.252', SSH_USER, 
                                     BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'main')
    self.core_instance.MakeDnsServerSetAssignments(u'localhost', u'main')
    self.core_instance.MakeDnsServerSetAssignments(u'255.254.253.252', u'main')
    self.core_instance.MakeDnsServerSetViewAssignments(u'external', 1, u'main')
    self.core_instance.MakeViewToACLAssignments(u'external', u'main',
                                                u'internal', 1)
    self.core_instance.MakeZone(u'forward_zone', u'main', u'university.lcl.', u'external')
    self.core_instance.MakeRecord(u'soa', u'@', u'forward_zone', {u'refresh_seconds':500,
        u'expiry_seconds':500, u'name_server':u'ns.university.lcl.', u'minimum_seconds':500,
        u'retry_seconds': 500, u'serial_number':1000, u'admin_email': u'admin.localhost.lcl.'}, u'external')
    self.core_instance.MakeRecord(u'ns', u'@', u'forward_zone', {u'name_server':u'ns.university.lcl.'})
    self.core_instance.MakeRecord(u'a', u'ns', u'forward_zone', {u'assignment_ip':u'1.2.3.4'})
    self.core_instance.MakeNamedConfGlobalOption(
        u'main', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\n'
        'controls { inet 127.0.0.1 port 5555 allow{localhost;} keys {rndc-key;};};' % (os.getcwd()))

  def tearDown(self):
    if( os.path.exists(self.config_instance.config_file['exporter']['backup_dir']) ):
      shutil.rmtree(self.config_instance.config_file['exporter']['backup_dir'])
    if( os.path.exists(self.config_instance.config_file['exporter']['root_config_dir']) ):
      shutil.rmtree(self.config_instance.config_file['exporter']['root_config_dir'])
    if( os.path.exists('test_data/root_config_dir') ):
      shutil.rmtree('test_data/root_config_dir')
    if( os.path.exists('test_data/root_config_dir_abs') ):
      shutil.rmtree('test_data/root_config_dir_abs')
    if( os.path.exists('test_data/config_test_dir') ):
      shutil.rmtree('test_data/config_test_dir')

  #Testing the exporting of a subordinate zone with no records to make sure
  #that config_lib tars an empty folder.
  def testTarringSubordinateZone(self):
    for zone in self.core_instance.ListZones():
      self.core_instance.RemoveZone(zone)
    self.core_instance.MakeDnsServer(u'server1', u'some_user', u'/bind/dir/',
        u'/test/dir/')
    self.core_instance.MakeDnsServerSet(u'server_set1')
    self.core_instance.MakeDnsServerSetAssignments(u'server1', u'server_set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'external', 1, u'server_set1')

    self.core_instance.MakeZone(u'test_zone', u'subordinate', u'test_zone.', 
        view_name=u'external', make_any=False)
    self.core_instance.MakeNamedConfGlobalOption(u'server_set1', u'recursion no;')

    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    config_lib_instance.UnTarDnsTree()
    #Make sure we exported the empty 'external' folder
    self.assertTrue(os.path.exists(os.path.join(self.root_config_dir, 
        'server1/named/external')))

    config_lib_instance.TarDnsBindFiles(u'server1')

    try:
      untarred_path = os.path.join(self.root_config_dir, 'server1_untarred')
      tar_file = tarfile.open(
          os.path.join(self.root_config_dir, 'server1', 'server1.tar.bz2'), 
          'r:bz2')
      tar_file.extractall(path=untarred_path)
      #Make sure we tarred the empty 'external' folder
      self.assertTrue(os.path.exists(os.path.join(untarred_path, 
          'named/external')))
    finally:
      tar_file.close()

  def testFindDnsTreeFilename(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    file_name = 'dns_tree_%s-18.tar.bz2' %  datetime.datetime.now().strftime('%d_%m_%yT%H_%M')
    self.assertEqual(config_lib_instance.FindDnsTreeFilename('18'), file_name)
    self.assertRaises(config_lib.ExporterAuditIdError, config_lib_instance.FindDnsTreeFilename, None)

    config_lib_instance.backup_dir = '/bad/dir/'
    self.assertRaises(config_lib.ExporterFileError, config_lib_instance.FindDnsTreeFilename, '16')
    config_lib_instance.backup_dir = self.backup_dir

    self.assertEqual(config_lib_instance.FindDnsTreeFilename('16'), None)
    os.rename('%s/%s' % (self.backup_dir, file_name), 
              '%s/dns_tree_fail_file.tar.bz2' % self.backup_dir)
    self.assertRaises(config_lib.ExporterFileError, config_lib_instance.FindDnsTreeFilename, '16')

  def testFindNewestDnsTreeFilename(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    
    os.mkdir(self.backup_dir)
    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.FindNewestDnsTreeFilename)

    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    file_name = 'dns_tree_%s-18.tar.bz2' %  datetime.datetime.now().strftime('%d_%m_%yT%H_%M')
    audit_id, filename = config_lib_instance.FindNewestDnsTreeFilename()
    self.assertEqual(filename, file_name)
    self.assertEqual(audit_id, 18)
    
    os.rename('%s/%s' % (self.backup_dir, file_name),
              '%s/dns_tree_fail.tar.bz2' % self.backup_dir)
    self.assertRaises(config_lib.ExporterFileNameError, config_lib_instance.FindNewestDnsTreeFilename)
    os.remove('%s/dns_tree_fail.tar.bz2' % self.backup_dir)
    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.FindNewestDnsTreeFilename)
    
    config_lib_instance.backup_dir = '/bad/directory'
    self.assertRaises(config_lib.ExporterListFileError, config_lib_instance.FindNewestDnsTreeFilename)

  def testUnTarDnsTree(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()

    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.UnTarDnsTree, 96)
    config_lib_instance.UnTarDnsTree()
    self.assertTrue(os.path.exists('%s/%s' % (self.root_config_dir, 'localhost')))

  def testTarDnsTree(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    self.assertRaises(config_lib.ExporterAuditIdError, config_lib_instance.TarDnsTree, None)
    self.assertRaises(config_lib.ExporterListFileError, config_lib_instance.TarDnsTree, '16')
    os.mkdir(self.root_config_dir)
    config_lib_instance.UnTarDnsTree('18')

    self.assertEqual(config_lib_instance.TarDnsTree('16'), None)

  def testUnTarInCorrectLocation(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance.UnTarDnsTree()
    self.assertTrue(os.path.exists('%s/localhost' % self.root_config_dir))
    config_lib_instance.backup_dir = '%s/%s' % (os.getcwd(), config_lib_instance.backup_dir)
    
    config_lib_instance.root_config_dir = 'config_test_dir/config'
    os.chdir('test_data')
    config_lib_instance.UnTarDnsTree()
    os.chdir('../')
    self.assertTrue(os.path.exists('test_data/config_test_dir/config/localhost'))
    self.assertTrue(os.path.exists('test_data/config_test_dir/config/localhost/named/named.ca'))
    shutil.rmtree('test_data/config_test_dir')
    
    config_lib_instance.root_config_dir = '../root_config_dir'
    os.chdir('test_data/named')
    config_lib_instance.UnTarDnsTree()
    os.chdir('../../')
    self.assertTrue(os.path.exists('test_data/root_config_dir/localhost'))
    shutil.rmtree('test_data/root_config_dir')
    
    config_lib_instance.root_config_dir = '%s/test_data/root_config_dir_abs' % os.getcwd()
    config_lib_instance.UnTarDnsTree()
    self.assertTrue(os.path.exists('test_data/root_config_dir_abs/localhost'))
    shutil.rmtree('test_data/root_config_dir_abs')


  def testCheckDnsServer(self):
    # This does not test the raise ServerCheckError: Unable to run 'named'
    #   since we would have to run a controlled server that does not have
    #   named installed.
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()

    # ExporterFileError: Can not list files in root dir
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    self.assertRaises(config_lib.ExporterFileError, 
        config_lib_instance.CheckDnsServer, 'localhost', [])

    # ServerCheckError: DNS server doesn't exist
    config_lib_instance.UnTarDnsTree()
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.CheckDnsServer,
        'junk', [])
    
    ########################33
    # Once tree exporter if complete, this will be removed
    ########################33
    # This is temporary until DNS tree exporter is committed, at which it will be unnecessary.
    if( os.path.exists('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir) ):
      os.remove('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir)
    if( os.path.exists('%s/localhost/named/localhost_config' % self.root_config_dir) ):
      os.remove('%s/localhost/named/localhost_config' % self.root_config_dir)
    # End of needing to remove

    server_info1 = {'server_info':{
                        'server_name': 'localhost',
                        'server_user': SSH_USER,
                        'bind_dir': BINDDIR,
                        'test_dir': TESTDIR,
                        'bind_version': 'UNKNOWN'}}
    server_info2 = {'server_info':{
                        'server_name': '255.254.253.252',
                        'server_user': SSH_USER,
                        'bind_dir': BINDDIR,
                        'test_dir': TESTDIR,
                        'bind_version': 'UNKNOWN'}}
    config_lib_instance.WriteDnsServerInfo(server_info1)
    config_lib_instance.WriteDnsServerInfo(server_info2)
    ########################33
    ########################33
    ########################33

    # ServerCheckError: Metadata file incorrectly written/DNE
    shutil.move('%s/localhost/localhost.info' % self.root_config_dir,
              '%s/localhost/localhost_bad.info' % self.root_config_dir)
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.CheckDnsServer,
        'localhost', [])
    shutil.move('%s/localhost/localhost_bad.info' % self.root_config_dir,
              '%s/localhost/localhost.info' % self.root_config_dir)

    # ServerCheckError: Can not connect via SSH
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.CheckDnsServer,
        '255.254.253.252', [])

    # ServerCheckError: Remote BIND directory doesn't exist
    self.core_instance.UpdateDnsServer(u'localhost', u'localhost', SSH_USER,
        u'/junk/', u'/junk/test/')
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance.UnTarDnsTree()
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.CheckDnsServer,
        'localhost', [])

    # ServerCheckError: Remote test directory doesn't exist
    self.core_instance.UpdateDnsServer(u'localhost', u'localhost', SSH_USER, 
        BINDDIR, u'/junk/test/')
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance.UnTarDnsTree()
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.CheckDnsServer,
        'localhost', [])

    # Everything Passes
    self.core_instance.UpdateDnsServer(u'localhost', u'localhost', SSH_USER,
        BINDDIR, TESTDIR)
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance.UnTarDnsTree()
    
    ########################33
    # Once tree exporter if complete, this will be removed
    ########################33
    # This is temporary until DNS tree exporter is committed, at which it will be unnecessary.
    if( os.path.exists('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir) ):
      os.remove('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir)
    if( os.path.exists('%s/localhost/named/localhost_config' % self.root_config_dir) ):
      os.remove('%s/localhost/named/localhost_config' % self.root_config_dir)
    # End of needing to remove

    server_info1 = {'server_info':{
                        'server_name': 'localhost',
                        'server_user': SSH_USER,
                        'bind_dir': BINDDIR,
                        'test_dir': TESTDIR,
                        'bind_version': 'UNKNOWN'}}
    server_info2 = {'server_info':{
                        'server_name': '255.254.253.252',
                        'server_user': SSH_USER,
                        'bind_dir': BINDDIR,
                        'test_dir': TESTDIR,
                        'bind_version': 'UNKNOWN'}}
    config_lib_instance.WriteDnsServerInfo(server_info1)
    config_lib_instance.WriteDnsServerInfo(server_info2)
    ########################33
    ########################33
    ########################33

    self.assertEqual(config_lib_instance.CheckDnsServer(
        'localhost', ['named-checkzone', 'named-checkconf', 'named-compilezone', 'tar']), None)
    # Check that info file has additional information
    localhost_info = ConfigParser.SafeConfigParser()
    localhost_info.read('%s/localhost/localhost.info' % self.root_config_dir)
    self.assertTrue(localhost_info.has_section('tools'))
    self.assertTrue(localhost_info.has_option('tools', 'named-checkzone'))
    self.assertTrue(localhost_info.has_option('tools', 'named-checkconf'))
    self.assertTrue(localhost_info.has_option('tools', 'named-compilezone'))
    self.assertTrue(localhost_info.has_option('tools', 'tar'))

    self.assertRaises(errors.FunctionError, config_lib_instance.CheckDnsServer, 'localhost', ['bad_tool'])

  def testWriteDnsServerInfo(self):
    server_information = {'server_info': {
                              'server_name': 'localhost',
                              'server_user': SSH_USER,
                              'ssh_host':'%s@localhost:22' % SSH_USER,
                              'bind_dir': BINDDIR,
                              'test_dir': TESTDIR,
                              'bind_version': 'UNKNOWN'},
                          'tools': {}}
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)

    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    audit_id, filename = config_lib_instance.FindNewestDnsTreeFilename()
    config_lib_instance.UnTarDnsTree(audit_id)

    # This is temporary until DNS tree exporter is committed, at which it will be unnecessary.
    if( os.path.exists('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir) ):
      os.remove('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir)
    if( os.path.exists('%s/localhost/named/localhost_config' % self.root_config_dir) ):
      os.remove('%s/localhost/named/localhost_config' % self.root_config_dir)
    # End of needing to remove

    config_lib_instance.WriteDnsServerInfo(server_information)
    self.assertTrue(os.path.exists('%s/localhost/localhost.info' % self.root_config_dir))

    server_information = {'server_info': {
                             'server_name': '255.254.253.252',
                             'server_user': SSH_USER,
                             'ssh_host':'%s@255.254.253.252:22' % SSH_USER,
                             'bind_dir': BINDDIR,
                             'test_dir': TESTDIR,
                             'bind_version': 'UNKNOWN'},
                          'tools': {}}
    config_lib_instance.WriteDnsServerInfo(server_information)
    self.assertTrue(os.path.exists('%s/255.254.253.252/255.254.253.252.info'%self.root_config_dir))

    server_file = ConfigParser.SafeConfigParser()
    server_file.read('%s/localhost/localhost.info' % self.root_config_dir)
    self.assertTrue(server_file.has_section('server_info'))
    self.assertTrue(server_file.has_section('tools'))
    self.assertTrue(server_file.has_option('server_info', 'ssh_host'))
    self.assertTrue(server_file.has_option('server_info', 'bind_dir'))
    self.assertTrue(server_file.has_option('server_info', 'test_dir'))
    self.assertEqual(len(server_file.options('tools')), 0)
    self.assertEqual(server_file.get('server_info', 'ssh_host'), '%s@localhost:22' % SSH_USER)
    self.assertEqual(server_file.get('server_info', 'bind_dir'), BINDDIR)
    self.assertEqual(server_file.get('server_info', 'test_dir'), TESTDIR)

    del(server_file)
    server_file = ConfigParser.SafeConfigParser()
    server_file.read('%s/255.254.253.252/255.254.253.252.info' % self.root_config_dir)
    self.assertTrue(server_file.has_section('server_info'))
    self.assertTrue(server_file.has_section('tools'))
    self.assertTrue(server_file.has_option('server_info', 'ssh_host'))
    self.assertTrue(server_file.has_option('server_info', 'bind_dir'))
    self.assertTrue(server_file.has_option('server_info', 'test_dir'))
    self.assertEqual(len(server_file.options('tools')), 0)
    self.assertEqual(server_file.get('server_info', 'ssh_host'), '%s@255.254.253.252:22' % SSH_USER)
    self.assertEqual(server_file.get('server_info', 'bind_dir'), BINDDIR)
    self.assertEqual(server_file.get('server_info', 'test_dir'), TESTDIR)

    # Redo this after finished refactoring dns_server_info dictionary
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.WriteDnsServerInfo, {})
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.WriteDnsServerInfo, {'server_info': 
        {'server_name':'bad_server','server_user':'user', 'bind_dir':'/dir','test_dir':'/dir/test', 'bind_version':'UNKNOWN'}})

    config_lib_instance.TarDnsTree(audit_id)
    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.WriteDnsServerInfo, server_information)
    
    config_lib_instance.UnTarDnsTree(audit_id)
    server_information = {'server_info': {
                             'server_name': 'localhost',
                             'server_user': SSH_USER,
                             'ssh_host':'%s@localhost:22' % SSH_USER,
                             'bind_dir': '/some/bind/',
                             'test_dir': TESTDIR,
                             'bind_version': 'UNKNOWN'},
                           'tools': {
                             'named-compilezone': True,
                             'named-checkzone': True,
                             'named-checkconf': True,
                             'tar': True}}
    config_lib_instance.WriteDnsServerInfo(server_information)
    self.assertEqual(config_lib_instance.GetDnsServerInfo('localhost'), server_information)

  def testGetDnsServerInfo(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()

    audit_id, filename = config_lib_instance.FindNewestDnsTreeFilename()
    config_lib_instance.UnTarDnsTree(audit_id)
    # This is temporary until DNS tree exporter is committed, at which it will be unnecessary.
    if( os.path.exists('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir) ):
      os.remove('%s/255.254.253.252/named/255.254.253.252_config' % self.root_config_dir)
    if( os.path.exists('%s/localhost/named/localhost_config' % self.root_config_dir) ):
      os.remove('%s/localhost/named/localhost_config' % self.root_config_dir)
    # End of needing to remove
    
    # No .info file
    #self.assertRaises(config_lib.ServerCheckError, config_lib_instance.GetDnsServerInfo, 'localhost')

    # Invalid .info file
    invalid_file = open('%s/localhost/localhost.info' % self.root_config_dir, 'w')
    invalid_file.write('[tools]')
    invalid_file.close()
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.GetDnsServerInfo, 'localhost')

    server1_information = {'server_info': {
                               'server_name': 'localhost',
                               'server_user': SSH_USER,
                               'ssh_host': '%s@localhost:22' % SSH_USER,
                               'bind_dir': BINDDIR,
                               'test_dir': TESTDIR,
                               'bind_version': 'UNKNOWN'},
                           'tools': {}}
    config_lib_instance.WriteDnsServerInfo(server1_information)
    server2_information = {'server_info': {
                               'server_name': '255.254.253.252',
                               'server_user': SSH_USER,
                               'ssh_host': '%s@255.254.253.252:22' % SSH_USER,
                               'bind_dir': BINDDIR,
                               'test_dir': TESTDIR,
                               'bind_version': 'UNKNOWN'},
                           'tools': {
                               'named-compilezone': True,
                               'named-checkzone': True,
                               'named-checkconf': False ,
                               'tar': False}}
    config_lib_instance.WriteDnsServerInfo(server2_information)
    config_lib_instance.TarDnsTree(audit_id)

    # No exported trees
    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.GetDnsServerInfo, 'localhost')
    
    config_lib_instance.UnTarDnsTree(audit_id)
    
    # Checking for correct read in
    self.assertEqual(config_lib_instance.GetDnsServerInfo('localhost'),
                     server1_information)
    self.assertEqual(config_lib_instance.GetDnsServerInfo('255.254.253.252'),
                     server2_information)
    
    # No existing server
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.GetDnsServerInfo, 'bad_server')

  def testTarDnsBindFiles(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    
    # No DNS tree yet
    self.assertRaises(config_lib.ExporterNoFileError, config_lib_instance.TarDnsBindFiles, 'localhost')
    
    tree_exporter_instance.ExportAllBindTrees()
    audit_id, filename = config_lib_instance.FindNewestDnsTreeFilename()
    config_lib_instance.UnTarDnsTree(audit_id)

    # No such DNS server
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.TarDnsBindFiles, 'bad')

    # Invalid tree format
    f = open('%s/localhost/named/bad.txt' % self.root_config_dir, 'w')
    f.close()
    self.assertRaises(config_lib.ExporterListFileError, config_lib_instance.TarDnsBindFiles, 'localhost')
    os.remove('%s/localhost/named/bad.txt' % self.root_config_dir)

    # Success
    config_lib_instance.TarDnsBindFiles('localhost')
    self.assertTrue(os.path.exists('%s/localhost/localhost.tar.bz2' % self.root_config_dir))
    os.mkdir('%s/test/' % self.root_config_dir)
    shutil.move('%s/localhost/localhost.tar.bz2' % self.root_config_dir,
                '%s/test/localhost.tar.bz2' % self.root_config_dir)
    tar_file = tarfile.open('%s/test/localhost.tar.bz2' % self.root_config_dir, 'r:bz2')
    tarred_files = tar_file.getnames()
    for tarred in tarred_files:
      self.assertTrue(os.path.exists('%s/localhost/%s' % (self.root_config_dir, tarred)))

  def testGetZoneList(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.assertRaises(config_lib.ServerCheckError, config_lib_instance.GetZoneList, 'bad')
    tree_exporter_instance.ExportAllBindTrees()

    config_lib_instance.UnTarDnsTree()
    f = open('%s/localhost/named/external/local.db' % self.root_config_dir, 'wb')
    f.close()
    self.assertRaises(errors.FunctionError, config_lib_instance.GetZoneList, 'localhost')
    os.remove('%s/localhost/named/external/local.db' % self.root_config_dir)

    self.assertEqual(config_lib_instance.GetZoneList('localhost'), {'external':{'university.lcl':'forward_zone.db'}})

  def testMergeOptionsDicts(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    global_options_dict = {'directory': '"/home/cookie/Dropbox/Roster/compilezone/trunk/test/test_data/named/named"', 
                           'pid-file': '"test_data/named.pid"'}
    view_dict = {'zone "."': 
                    {'type': 'hint', 'file': '"named.ca"'}, 
                 'zone "university.lcl"': 
                    {'type': 'main', 'file': '"external/forward_zone.db"'}, 
                 'match-clients': {'internal': True}}
    zone_dict = {'type': 'main', 'file': '"external/forward_zone.db"'}
    self.assertEqual(config_lib_instance.MergeOptionsDicts(global_options_dict, view_dict, zone_dict),
            {'check-integrity': 'yes',
             'check-siblings': 'yes',
             'check-srv-cname': 'warn',
             'check-wildcard': 'yes',
             'check-names': 'warn',
             'check-mx': 'warn',
             'check-dup-records': 'warn',
             'check-mx-cname': 'warn'})

  def testGenerateAdditionalNamedCheckzoneArgs(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    merged_options_dict = {'check-integrity': 'yes',
                           'check-siblings': 'yes',
                           'check-srv-cname': 'warn',
                           'check-wildcard': 'yes',
                           'check-names': 'warn',
                           'check-mx': 'warn',
                           'check-dup-records': 'warn',
                           'check-mx-cname': 'warn'}
    self.assertEqual(config_lib_instance.GenerateAdditionalNamedCheckzoneArgs(merged_options_dict),
                     ['-i', 'full-sibling',
                      '-S', 'warn',
                      '-W', 'warn',
                      '-k', 'warn',
                      '-m', 'warn',
                      '-r', 'warn',
                      '-M', 'warn'])

  def testGetNamedZoneToolArgs(self):
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    tree_exporter_instance.ExportAllBindTrees()
    config_lib_instance.UnTarDnsTree()
    self.assertEqual(config_lib_instance.GetNamedZoneToolArgs('localhost', 'external', 'forward_zone.db'),
        '-i full-sibling -S warn -W warn -k warn -m warn -r warn -M warn')

if( __name__ == '__main__' ):
  unittest.main()
