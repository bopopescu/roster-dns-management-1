﻿#summary Details Roster.



# Roster #
Roster is DNS Management software suite for modifying, creating, and managing BIND9 files. Its purpose is to make BIND9 configuration files easier to manage.

## Features ##
  * MySQL database to host the entire DNS configuration.
  * XML-RPC server to enable remote access to the database.
  * Interchangeable authentication module.
  * Set of about 30 tools to create, modify, view, and assign to each other records, zones, views, dns servers, dns server sets, groups, users, etc.
  * Set of tools to export and sync BIND9 configuration files to their appropriate servers.
> <a href='Hidden comment: * A web interface to manage the DNS configuration.'></a>

## Roster Components ##
![http://roster-dns-management.googlecode.com/svn/wiki/img/Roster_pieces.png](http://roster-dns-management.googlecode.com/svn/wiki/img/Roster_pieces.png)

Roster has four main components:
  * Roster Core
  * Roster Server
  * Roster User Tools
  * Roster Config Manager
> <a href='Hidden comment: * Roster Web.'></a>

### Roster Core ###
Roster Core is a collection of functions to access the core API of Roster and is used heavily by Roster Server. Roster Server contains the MySQL database layer that accesses all data used by Roster. All records, zones, views, etc. are contained in the database and is the authority on any DNS data.

### Roster Server ###
Roster Server is a threaded SSL enabled XML-RPC server that connects directly to Roster Core. This allows clients to run core functions remotely and securely. Users authenticate to Roster Server using LDAP or [a user supplied authentication method](Authentication.md). The user need not enter a password multiple times for multiple records as credentials are stored for short periods of time (See [Credentials](UserToolsUsage#Credential.md) documentation).

### Roster User Tools ###
[Roster User Tools](UserToolsUsage.md) communicates to Roster Server. Roster User Tools contains command line tools to contact Roster Server through an SSL enabled XML-RPC client, to perform the majority of Roster tasks.

### Roster Config Manager ###
[Roster Config Manager](ConfigManagerUsage.md) is the component of Roster responsible for creating, exporting, and error checking files that will be used by BIND. Roster Config Manager contains command line tools to export all contents from the database to BIND files.

<a href='Hidden comment: ===Roster Web==='></a>