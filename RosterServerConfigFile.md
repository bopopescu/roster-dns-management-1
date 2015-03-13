﻿#summary Details Roster Server config file

# Roster Config File #

The Roster Server config file is used by Roster Server on server startup to automatically configure a number of options. Running the roster\_database\_bootstrap user tools script will generate this file, leaving few modifications needed before running the Roster Server.

## Set Up ##

By running the roster\_database\_bootstrap script an auto-generated roster\_server.conf (or whatever name was specified) file is created at the specified location. This file is world-readable and will need its file permissions changed to non-world-readable before Roster Server will start. You will also need to manually modify the **_`'server_killswitch'`_** option under the **_`[server]`_** section to be **_`'off'`_**. This will allow rosterd to start assuming other configuration values are correct.

## Sections & Fields ##

### Outline ###
```
# Fields pertaining to the SQL database
[database]
  # database server address as an IP or hostname
  server = database.university.edu
  # SQL database username
  login = sql_user
  # database user password
  passwd = sql_pass
  # name of the SQL database on the database server
  database = database_01
  # Roster Server big lock timeout for the database
  big_lock_timeout = 90
  # wait time for database big lock
  big_lock_wait = 5
  # use SSL when communicating with database (on/off)
  ssl = off
  # SSL Certificate Authority to use
  ssl_ca = /etc/roster/certs/example_ca.crt
  # Debug flag for all of Roster's MySQL queries to be logged
  db_debug = on
  # Debug log file, if none is provided and debug flag is on,
  # stdout will be used.
  db_debug_log = /tmp/debug_log.txt

# Fields pertaining to Roster Server (Only needed for the Roster XML-RPC server)
[server]
  # time to renew infinite credentials, in seconds
  inf_renew_time = 432000
  # time for core instance to die, in seconds
  core_die_time = 1200
  # time to wait for incorrect password, in seconds
  get_credentials_wait_increment = 1
  # Roster Server will not start while killswitch is 'on', change to 'off' before starting server
  server_killswitch = off
  # location of SSL key file
  ssl_keyfile = /etc/roster/certs/roster_server.key
  # location of SSL cert file
  ssl_certfile = /etc/roster/certs/roster_server.crt
  # location of Roster Server lock file
  lock_file = /var/lock/lockfile
  # username to run server as
  run_as_username = nobody
  # location of Roster Server log file
  server_log_file = /var/log/roster.log
  # hostname of Roster Server
  host = localhost
  # port Roster Server should listen on
  port = 8000

# BIND config exporter configuration (Only needed for Roster Config Manager)
[exporter]
  # root BIND config temporary directory
  root_config_dir = /opt/roster/root_config_dir
  # BIND config backup directory
  backup_dir = /etc/roster/backup_dir
  # If an error should occur, dnsexportconfig will, using smtp_server,
  # send an email from system_email to failure_notification_email 
  # with a log of the errors.
  smtp_server = smtp.university.edu
  failure_notification_email = config_webmaster@university.edu
  system_email = config_export_error@university.edu
  email_subject = [Roster] dnsexportconfig Failure
  # Print run statements during exporter tool execution in dnsexportconfig
  exporter_debug = on
  root_hint_file = /etc/bind/named.ca

# Fields regarding server user credentials (Only needed for Roster XML-RPC server)
[credentials]
  # credential expiration time, in seconds
  exp_time = 3600
  # authentication method, i.e., PAM or LDAP (example below)
  authentication_method = general_ldap

# Section required for LDAP authentication (Only if LDAP authentication chosen)
[general_ldap]
  # LDAP binddn line
  binddn = uid=%%s,ou=People,dc=dc,dc=university,dc=edu
  # LDAP server location
  server = ldaps://ldap.university.edu:636
  # LDAP version
  version = VERSION3
  # TLS enabled/disabled (on/off) for authentication
  tls = on

#Defaults for zone bootstraping (Only gets used if dnsmkzone --bootstrap-zone is used)
[zone_defaults]
  #SOA record default arguments
  refresh_seconds = 3600
  expiry_seconds = 1814400
  minimum_seconds = 86400
  retry_seconds = 600
  soa_ttl = 3600

  #NS record default argument
  ns_ttl = 3600
```

The above list is not necessarilly comprehensive for all setups. There could be extra sections/fields for LDAP, PAM, or others as necessary.