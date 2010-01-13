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

"""This module contains all of the logic for the zone exporter.

It should be only called by the exporter.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import roster_core

class Error(roster_core.CoreError):
  pass


class ZoneError(Error):
  pass


def FormatRecordsForZone(unsorted_records=None, origin=None):
  """Gets the records from the db and sorts them.

  Inputs:
    unsorted_records: unsorted records dictionary
    origin: string of zone origin

  Outputs:
    dictionary keyed by record type with values of sorted lists of 
      record dictionaries.
  """
  pre_sorted_records = {}
  sorted_records = {}
  if( unsorted_records ):
    sorted_records['bulk'] = []
  for record in unsorted_records:
    if( not record['record_type'] in pre_sorted_records ):
      pre_sorted_records[record['record_type']] = []
    pre_sorted_records[record['record_type']].append(record)
  for record_type in pre_sorted_records.keys():
    if( record_type == 'mx' ):
      sorted_records[record_type] = sorted(pre_sorted_records[record_type],
                                           key=lambda k: k['priority'])

    elif( record_type == 'ns' ):
      sorted_records[record_type] = sorted(pre_sorted_records[record_type],
                                           key=lambda k: k['name_server'])

    elif( record_type in ('soa', 'txt') ):
      sorted_records[record_type] = pre_sorted_records[record_type]

    else:
      # put the rest of the records together and sort them by target
      sorted_records['bulk'].extend(pre_sorted_records[record_type])

  if( unsorted_records ):
    sorted_records['bulk'] = sorted(sorted_records['bulk'],
                                    key=lambda k: k['target'])

  if( 'soa' in sorted_records ):
    if( len(sorted_records['soa']) == 1 ):
      soa_origin = sorted_records['soa'][0]['target']
      if( soa_origin != origin and soa_origin != u'@' ):
        raise Error('SOA origin "%s" and zone origin "%s" do not match.' % (
            soa_origin, origin))
    else:
      raise Error('Multiple SOA records found.')
  else:
    raise Error('No SOA records found for zone with origin "%s"' % origin)

  return sorted_records

def MakeZoneString(records, zone_origin, argument_definitions):
  """Makes zone string that can be written to a file.
  Inputs:
    records: dictionary of sorted records
    zone_origin: string of zone origin
    argument_definitions: dictionary of argument definitions

  Outputs:
    string of exported zone file.
  """
  ### Need to run dupe checks here at some point
  records = FormatRecordsForZone(records, zone_origin)
  if( not records.has_key('soa') ):
    raise ZoneError('SOA not found for zone %s' % zone_origin)
  
  zone_string_list = ['; This zone file is autogenerated. DO NOT EDIT.',
                      '$ORIGIN %s' % zone_origin]
  begining_record_order = ['soa', 'ns', 'mx', 'txt']

  for record_type in begining_record_order: 
    if( record_type not in records ):
      continue
    for current_record in records[record_type]:
      line_list = [current_record['target'], str(current_record['ttl']), 'in',
                   current_record['record_type']]

      for arg_def in argument_definitions[record_type]:
        line_list.append(str(current_record[arg_def['argument_name']]))

      zone_string_list.append(' '.join(line_list))
   
  for current_record in records['bulk']:
    line_list = [current_record['target'], str(current_record['ttl']), 'in', 
                 current_record['record_type']]

    for arg_def in argument_definitions[current_record['record_type']]:
      line_list.append(str(current_record[arg_def['argument_name']]))

    zone_string_list.append(' '.join(line_list))

  return '%s\n' % '\n'.join(zone_string_list)
