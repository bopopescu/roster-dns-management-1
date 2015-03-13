﻿#summary Documentation pertaining to Access Levels and Permissions in Roster

# Access Levels and Permissions #

## Introduction ##

Roster facilitates control of access to Roster functionality and network resources managed by Roster through 2 methods: access levels and permissions. This document explains the difference between these methods and when/how they should be used.

For a description of these functions, refer to the [User Tools Usage: User and Group](UserToolsUsage#User_and_Group.md) section of the wiki.

## Basic Usage ##

In order to allow/disallow a specific Roster user to have access to user tools at a specific level, use access levels outlined below.

To allow a group of users to create record types allowed to them on a particular forward or reverse zone, use permissions outlined below.

## Access Levels ##

Access levels in Roster allow system administrators to specify what subset of all available Roster user tools can be accessed by a given Roster user. For example, a user may be able to add a new record to a zone, but not be allowed to Add/Remove zones.

Access levels can be one of:
  * **_128 dns\_admin_**: Has permission to modify zones and run all functions/create all types of records
  * **_64 unlocked\_user_**: Able to modify any records within zones that are authorized
  * **_32 user_**: Same as unlocked user with extra checks on hostnames and IP Addresses
  * **_0 noop_**: Special access level with no permissions, for testing

To add a user, `a_user`, with unlocked\_user permissions:
```
dnsmkusergroup user -n a_user -a 64
```

String values can also be used to specify access levels. For example, the same user could be added by:
```
dnsmkusergroup user -n a_user -a unlocked_user
```

## Permissions ##

Permissions determine the types of records a group can create for a particular zone. Through the group's group-zone assignment, a group can be allowed different permissions for different zones. For example, a group with permissions to create "a" or "aaaa" in zone a.example.com may have permission to create "a", "aaaa", "cname", and "ns" records on b.example.com.
Note: These permissions apply to the user access level.

The permission **_group-permission_** for a group is assigned through the dnsmkusergroup tool using a comma-separated list of permissions:
```
dnsmkusergroup forward -z example_zone -g group1 --group-permission a,aaaa,cname,ns,soa
```

This can also be done for reverse ranges:
```
dnsmkusergroup reverse -z rev_zone -b 10.10.0.0/24 -g rev_group --group-permission cname,ns,ptr
```

Descriptions of these user tools are outlined in the User and Group section of the wiki mentioned above.

### Note about tree\_export\_user ###
tree\_export\_user is a user with access-level=0 (no access) that is installed with Roster. It is used during the logging of tree exporting. tree\_export\_user should not be deleted.