

# Introduction #

Init takes either the argument:
  * **_'stop'_**
  * **_'start'_**
  * **_'restart'_**

Roster\_database\_bootstrap creates an init script, but it needs additional configuration to make it automatically start.

# Installation #

The init.d script will be installed by [roster\_database\_bootstrap](Installation#Installing_Roster_Components.md) to `/etc/init.d/rosterd` by default.

# Configuring #

Making the init script auto start on machine start will depend on each OS installation and your specific configurations.

> For example, if you chose a non-default config-file location, you would change the init command to include that.

> Original init:
```
50 start_roster()
51 {
52   echo "Starting Roster Server..."
53   rosterd &
54 }
```
> Modified init for a non-default location of the config-file:
```
50 start_roster()
51 {
52   echo "Starting Roster Server..."
53   rosterd --config-file ./config.conf &
54 }
```

## Solaris ##

Modern Solaris systems use the Service Management Facility (SMF) to manage startup scripts. The legacy **_/etc/init.d_** startup scripts can still be used and since Linux uses this as well Roster defaults to it. This can be changed with your specific installation if desired. The instructions below pertain to the legacy **_/etc/init.d_** method.

### Auto Start Script ###

To auto start the init script, a symbolic link must be placed in the /etc/rc3.d directory. This can be accomplished as follows:
```
# ln -s /etc/init.d/rosterd /etc/rc3.d/S99rosterd
```

> Where 'S' represents 'Start' and 99 is the start order. Roster should be started last or nearly last in the boot process.

### Auto Stop Script ###

To auto stop the init script on shutdown, a symbolic link must be placed in the **_/etc/rc3.d directory_**. This can be accomplished as follows:
```
# ln -s /etc/init.d/rosterd /etc/rc3.d/K10rosterd
```

  * Where 'K' represents 'Kill'
  * 10 is the kill order.

Roster should be stopped first or nearly first in the boot process.

## Linux ##

Different distributions of Linux vary greatly how init scripts are installed. There are at least 2 types of common init.d script styles (SystemV and BSD). The **_/etc/init.d/rosterd_** file may need modified according to the script style and your particular configuration. Due to the vast differentiation of script configurations, we ask that you consult the manual of your particular distribution for configuration. However, some particular system configurations require modification of the init script.