﻿#summary How to use an authentication method other than LDAP.
#labels Phase-Deploy,Phase-Implementation

# Introduction #

You may want to use an authentication method other than the supplied LDAP. This can be done by making a wrapper class in Python that accesses this authentication method. This tutorial will explain how to create a dummy "Dummy Access Protocol" (DAP) wrapper.


# Making the Wrapper Class #

To use DAP we first need to import the "dap" module. You can use any module installed on the system. For example, if you download the PAM module, you can create a PAM authentication method. **Note: the DAP module does not actually exist, it is merely an example.**

```
import dap
```

Now a class is made. This class **MUST** be titled **_AuthenticationMethod_**. There **MUST** be an instance dictionary called **_self.requires_** of the variables to be placed in a config file in the **_init_** section of the **_AuthenticationMethod_** class as shown below. Valid types are:
  * str
  * int
  * float
A default can be provided, but if no default is specified (**None**), then the user will be prompted to enter this information upon bootstrapping the database.


```
import dap

class AuthenticationMethod:
  """General DAP authentication method,
  should work for most DAP applications.
  """ 
  self.requires = {'binddn': {'type': 'str', 'default': None},
                   'server': {'type': 'str', 'default': None}}
```


There **MUST** be a method called **_Authenticate_**. This method will return boolean **_True_** or **_False_** whether or not the authentication was successful.
This method can take any number of keyword arguments, but it **MUST** contain:
  * **_user\_name_**
  * **_password_**

keyword arguments.

```
import dap

class AuthenticationMethod:
  """General DAP authentication method,
  should work for most DAP applications.
  """
  self.requires = {'binddn': {'type': 'str', 'default': None},
                   'server': {'type': 'str', 'default': None}}

  def Authenticate(self, user_name=None, password=None, binddn=None, cert_file=None,
                   server=None, version=None, tls=None):
    """Authenticate method for DAP

    Inputs:
      user_name: string of user name
      password: string of password
      binddn: string of binddn line
      cert_file: string of cert file location
      server: string of server url
      version: string of version constant from ldap module
      tls: string of tls enabled or not

    Outputs:
      boolean: authenticated or not
    """
```

The "dap" module can optionally contain a **_"user\_auth"_** method that raises a UserErrorException if the user cannot be authenticated, and nothing if the user can be authenticated.

The code would proceed as follows:

```
import dap

class AuthenticationMethod:
  """General DAP authentication method,
  should work for most DAP applications.
  """
  self.requires = {'binddn': {'type': 'str', 'default': None},
                   'server': {'type': 'str', 'default': None}}

  def user_auth(self, binddn, password, server):
    if( binddn in self.bad_binddn_list ):
	  raise UserErrorException('binddn %s is not allowed' % binddn)
	  
  def Authenticate(self, user_name=None, password=None, binddn=None, server=None):
    """Authenticate method for DAP

    Inputs:
      user_name: string of user name
      password: string of password
      binddn: string of binddn line
      server: string of server url

    Outputs:
      boolean: authenticated or not
    """

    binddn = binddn % user_name

    try:
      dap.user_auth(binddn, password, server)
      return True
    except UserAuthException:
      return False
```

All of the keyword arguments (except **_user\_name_** and **_password_**) can be specified in the config file. The config file would look like this:

```
...

[credentials]
exp_time = 3600
authentication_method = dap

[dap]
binddn = user=%%s,group=Roster
server = dap://example.edu:1337

...
```

The binddn contains a double %, using this %%s with the **_binddn % user\_name_** will insert the username into the binddn line.

The created dap.py file must be placed into the roster\_server directory and added to the roster\_server/init.py as shown below.
```
...

# Abbreviated __init__.py

from server import Server
import dap

__all__ = ['Server, 'dap']

...
```