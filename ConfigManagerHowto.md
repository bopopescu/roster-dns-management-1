# Roster Config Manager How To #
A how to on different uses of the Roster Config Manager's tools.



## Exporting BIND Trees from Roster ##
Using the command [dnstreeexport](ConfigManagerUsage#dnstreeexport.md) will export Roster into 3 compressed files:
  * **_audit\_log\_replay\_dump-33.bz2_** - Contains the database backup of Roster for the coresponding audit log ID.  The number **_33_** is the audit log ID, which is the number of commands that Roster has logged up to this point.
  * **_full\_database\_dump-33.bz2_** - Contains a MySQL dump coresponding to the audit log ID.  The number **_33_** is the audit log ID.
  * **_dns\_tree\_25\_12\_11T18\_30-33.tar.bz2_** - Contains the copy of the zone and configuration files, coresponding to the audit log ID, for the BIND servers.  The first sequence of numbers is a time stamp in the form of '**_day\_month\_year(2 digit)Thour\_minute_**'.  The last number, **_33_**, is the audit log ID.

These files are placed into the backup directory specified by the [Roster server config file](RosterServerConfigFile.md).  Run this command as a user with permissions to read the [Roster server config file](RosterServerConfigFile.md).

## Restoring DNS Servers to Older Backups ##
Roster provides the ability to restore your DNS servers to a previous backup with the **_dnsconfigsync_** command.  To do this, a copy of the backup tar ball must be in the backup directory specified by the [Roster server config file](RosterServerConfigFile.md) and the audit log ID of the backup must be known.  Once these requirements are met, run the following command as a user with permissions to read the [Roster server config file](RosterServerConfigFile.md):

`dnsconfigsync -i 499`

  * **_499_** is the audit log ID.
This command will sync all of the servers in Roster at the time of the backup with their respective config and zone files from the same backup.

## Restoring Roster with Audit Log Replay ##
**NOTE: You can only restore or replay Roster if you have a backup made before the point of which you are trying to resotre/replay, otherwise Roster will revert to the closest backup after the point given.**
If a serious mistake was made to Roster that can not easily be fixed, it is possible to restore and replay Roster to the state prior to the mistake.  To do this, follow these steps:

1. Find the audit log ID for the mistake that was made.  Use the command [dnslsauditlog](UserToolsUsage#Audit_Log.md) to display the actions performed in Roster.  Locate the log of the mistake and the ID corresponding to it.
```
user@comp:~$ dnslsauditlog
ID Action              Timestamp           Username         Success Data
------------------------------------------------------------------------
14 MakeRecord          2012-07-10T10:03:29 user             1       {'target': u'machine01', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.106'}, 'zone_name': u'forward_zone'}
15 MakeRecord          2012-07-10T10:03:33 user             1       {'target': u'machine02', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.107'}, 'zone_name': u'forward_zone'}
16 MakeRecord          2012-07-10T10:03:36 user             1       {'target': u'machine03', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.108'}, 'zone_name': u'forward_zone'}
17 MakeRecord          2012-07-10T10:03:40 user             1       {'target': u'machine04', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.109'}, 'zone_name': u'forward_zone'}
18 MakeRecord          2012-07-10T10:03:43 user             1       {'target': u'machine05', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.110'}, 'zone_name': u'forward_zone'}
19 MakeRecord          2012-07-12T10:53:46 user             1       {'target': u'machine96', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.109'}, 'zone_name': u'forward_zone'}
20 MakeRecord          2012-07-12T10:56:32 user             1       {'target': u'machine88', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.110'}, 'zone_name': u'forward_zone'}
21 MakeRecord          2012-07-13T10:57:54 user             1       {'target': u'machine89', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.111'}, 'zone_name': u'forward_zone'}
22 ExportAllBindTrees  2012-07-13T10:58:08 tree_export_user 1       {'force': False}
23 MakeRecord          2012-07-10T12:38:57 user             1       {'target': u'oops', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.255'}, 'zone_name': u'forward_zone'}
24 MakeRecord          2012-07-10T12:40:23 user             1       {'target': u'oops2', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.0'}, 'zone_name': u'forward_zone'}
25 MakeRecord          2012-07-10T12:40:31 user             1       {'target': u'oops3', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.254'}, 'zone_name': u'forward_zone'}
26 RemoveRecord        2012-07-10T12:50:13 user             1       {'target': u'oops', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.255'}, 'zone_name': u'forward_zone'}
27 RemoveRecord        2012-07-10T12:50:23 user             1       {'target': u'oops3', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.254'}, 'zone_name': u'forward_zone'}
28 RemoveRecord        2012-07-10T12:50:30 user             1       {'target': u'oops2', 'record_type': u'a', 'view_name': u'any', 'ttl': 3600, 'record_args_dict': {u'assignment_ip': u'192.168.56.0'}, 'zone_name': u'forward_zone'}
29 RemoveZone          2012-07-10T13:11:59 user             1       {'zone_name': u'forward_zone', 'view_name': None}
```

> Note on [tree\_export\_user](AccessLevelsAndPermissions#Note_about_tree_export_user.md).
This shows that a backup was made at log ID 22 and a mistake was made by removing a zone after adding several records to it at log ID 29.  So the audit log ID where the mistake was made is **_29_**.

2. Restore and replay Roster up until the mistake was made using the command [dnsrecover](ConfigManagerUsage#dnsrecover.md).  Roster will restore everything in the database, except the audit log, to the most recent backup before the log ID of the mistake.  Then Roster will replay all of the successful commands made from the backup to the command before the given log ID.
```
user@comp:~$ dnsrecover -i 29 -u user --config-file /some/directory/roster_server.conf
Loading database from backup with ID 22
Replaying action with id 23: MakeRecord
with arguments: [u'a', u'oops', u'forward_zone', {u'assignment_ip': u'192.168.56.255'}, u'any', 3600]
Replaying action with id 24: MakeRecord
with arguments: [u'a', u'oops2', u'forward_zone', {u'assignment_ip': u'192.168.56.0'}, u'any', 3600]
Replaying action with id 25: MakeRecord
with arguments: [u'a', u'oops3', u'forward_zone', {u'assignment_ip': u'192.168.56.254'}, u'any', 3600]
Replaying action with id 26: RemoveRecord
with arguments: [u'a', u'oops', u'forward_zone', {u'assignment_ip': u'192.168.56.255'}, u'any', 3600]
Replaying action with id 27: RemoveRecord
with arguments: [u'a', u'oops3', u'forward_zone', {u'assignment_ip': u'192.168.56.254'}, u'any', 3600]
Replaying action with id 28: RemoveRecord
with arguments: [u'a', u'oops2', u'forward_zone', {u'assignment_ip': u'192.168.56.0'}, u'any', 3600]
```

> On [dnsrecover](ConfigManagerUsage#dnsrecover.md):
  * **_29_** is the audit log ID
  * **_user_** is the user in Roster with admin privileges
  * **_/some/directory/roster\_server.conf_** is the path to the [Roster server config file](RosterServerConfigFile.md).
Once this script has been run, Roster will have restored and replayed itself to the point before the mistake.