#!/usr/bin/env python

# Commit tracker


import argparse
from ConfigParser import SafeConfigParser
import math
import os
import re
from subprocess import Popen,PIPE,check_call
import sys
import time
import json
from datetime import datetime, timedelta

import pdb
def convert_to_builtin_type(obj):
    #print 'default(', repr(obj), ')'
    # Convert objects to a dictionary of their representation
    d = {}
    try:
        if obj.__class__ and obj.__class__.__name__:
            d['__class__'] = obj.__class__.__name__
    except AttributeError, err:
#        print 'ERROR:', err, " obj = ", obj
        False
    try:
        if obj.__module__:
            d['__module__'] = obj.__module__
    except AttributeError, err:
#        print 'ERROR:', err, " obj = ", obj
        False
    try:
        d.update(obj.__dict__)
    except AttributeError, err:
#        print 'ERROR:', err, " obj = ", obj
        False
    return d

def handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
#    elif isinstance(obj, ...):
#        return ...
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

class Config(object):
    def __init__(self):
        self.set_defaults()
        self.parse_args()
        self.read_config()
        self.set_config()

    def set_defaults(self):
        home = os.getenv('HOME')
        now = time.localtime()
        if home:
            # configuration file
            self.config_file = home + os.sep + '.committrackerrc'
            # repository
            self.repository_root = home + os.sep + 'WebKit'
        else:
            self.config_file = None
            self.repository_root = None
        self.verbose = False
        # should we fetch the latest?
        self.do_fetch = True
        # Date to start grabbing commits at.
        self.since = '01/01/{0}'.format(now.tm_year)
        # Date to stop grabbing commits at.
        self.until = None
        self.until = '{0}/{1}/{2}'.format(now.tm_mon, now.tm_mday, now.tm_year)

        self.weekly = False
        # This should be set in the config file in the "People" section!
        # dictionary of people who's contributions we are looking for
        # name -> email address
        self.people = { }

        self.format = 'Normal'
        self.json_file = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Count commits by the Adobe Web Platform Team')
        parser.add_argument('--config', default=None, help='Path to config file, default is {0}'.format(self.config_file))
        parser.add_argument('--verbose', action='store_true', help='Turn on verbose mode')
        parser.add_argument('--no-fetch', dest='no_fetch', action='store_true', help="Don't fetch from origin before counting")
        parser.add_argument('--since', default=None, help='Start date for counting. Defaults to Jan 1st of the current year.')
        parser.add_argument('--until', default=None, help='End date for counting.')
        parser.add_argument('--repo', dest='repository_root', default=None, help='Path to WebKit git repository')
        parser.add_argument('--show-total', dest='show_total', action='store_true', default=None, help='Output only the total')
        parser.add_argument('--weekly', dest='weekly', action='store_true', default=None, help='Query for every week between since and until, inclusive')
        parser.add_argument('--json-file', dest='json_file', default=None, help='File for writing JSON output')
        self.args = parser.parse_args()

    def read_config(self):
        self.file = SafeConfigParser(allow_no_value=True)
        if self.args.config:
            self.config_file = self.args.config
            with open(self.config_file) as fp:
                self.file.readfp(fp, self.config_file)
        else:
            self.file.read(self.config_file)

    def set_config(self):
        if self.args.verbose:
            self.format = 'Verbose'
        elif self.file.has_option('Options', 'verbose'):
            self.format = 'Verbose' if self.file.get_boolean('Options', 'verbose') else self.format

        if self.args.no_fetch:
            self.do_fetch = False
        elif self.file.has_option('Options', 'do_fetch'):
            self.do_fetch = self.file.get_boolean('Options', 'do_fetch')

        if self.args.since:
            self.since = self.args.since
        elif self.file.has_option('Options', 'since'):
            self.since = self.file.get('Options', 'since')

        if self.args.until:
            self.until = self.args.until
        elif self.file.has_option('Options', 'until'):
            self.until = self.file.get('Options', 'until')

        if self.args.repository_root:
            self.repository_root = self.args.repostitory_root
        elif self.file.has_option('Options', 'repository_root'):
            self.repository_root = self.file.get('Options', 'repository_root')

        if self.args.json_file:
            self.json_file = self.args.json_file
        elif self.file.has_option('Options', 'json_file'):
            self.json_file = self.file.get('Options', 'json_file')

        if self.args.weekly:
            self.weekly = self.args.weekly
        elif self.file.has_option('Options', 'weekly'):
            self.weekly = self.file.get('Options', 'weekly')

        if self.args.show_total:
            self.format = 'Total'
        elif self.file.has_option('Options','show_total'):
            self.format = self.file.get('Options', 'show_total')

        self.print_total = False
        if (self.format == 'Verbose' or self.format == 'Total' or self.format == 'Normal'): self.print_total = True

        self.print_normal = True;
        if self.format == 'Total': self.print_normal = False

        self.print_verbose = False;
        if self.format == 'Verbose': self.print_verbose = True

        if self.file.has_section('People'):
            self.people = { person[0] : person[1] for person in self.file.items('People') }

        # This is case insensitive because ConfigParser throws away the case of all of it's keys.
        self.people_matcher = re.compile(self.people_regexp(), re.IGNORECASE)

    def people_regexp(self):
        def helper(l):
            return '|'.join([ re.escape(i) for i in l if len(i) > 0 ])
        return helper(self.people.iterkeys()) + '|' + helper(self.people.itervalues())

    def print_verbose(self):
        if self.format == 'Verbose':
            return True
        return False

    # Normal text
    def print_normal(self):
        if self.format == 'Verbose' or self.format == 'Normal':
            return True
        return False   


    def print_total(self):
        if self.format == 'Verbose' or self.format == 'Total' or self.format == 'Normal':
            return True
        return False   


class Counter(object):
    def __init__(self, data, config, since, until):
        self.data = data
        self._config = config
        self.since = since
        self.until = until
        self.count = 0
        self.count_by_person = { k: 0 for k in self._config.people.iterkeys() }
#        pdb.set_trace()

    def __repr__(self):
        r = { 'total':self.count, 'people':self.count_by_person }
        print '<MyObj(%s)>' % self.count
        return '<MyObj(%s)>' % self.count

    def start(self):
        self._next_commit()
        for line in self.data:
            if line.startswith('Author'):
                if self._count_line_if_match(line):
                    self._next_commit()
            elif line.strip().startswith('Patch by'):
                if self._count_line_if_match(line):
                    self._next_commit()
            elif line.startswith('commit'):
                if self._config.print_verbose: print line

    def _next_commit(self):
        for line in self.data:
            if line.startswith('commit'):
                if self._config.print_verbose: print line
                return

    def _count_line_if_match(self, line):
        person = self._line_has_person(line)
        if person:
            if self._config.print_verbose: print line
            self.count += 1
            self.count_by_person[person] += 1
            return True
        else:
            return False

    def _line_has_person(self, line):
        match = self._config.people_matcher.search(line)
        if match:
            matched = match.group(0)
            selector = matched.lower()
            if self._config.people.has_key(selector):
                return selector
            else:
                for (k,v) in self._config.people.iteritems():
                    if v == matched:
                        return k
                raise StandardError, "Unexpected match of unknown value: {0}".format(matched)
        else:
            return None

    def _json_struct(self):
        json_struct = {}
        now = time.localtime()
        json_struct['since'] = self.since
        json_struct['until'] = self.until
#        json_struct['end'] = self._config.until or '{0}/{1}/{2}'.format(now.tm_mon,now.tm_mday,now.tm_year)
        json_struct['people'] = self.count_by_person
        json_struct['total'] = self.count
        return json_struct
#        print json.dumps( self, default=convert_to_builtin_type )       

def _build_json_struct(config, counters):
    json_struct = {}
    json_struct['since'] = config.since
    json_struct['until'] = config.until
    json_struct['weekly'] = config.weekly
    json_struct['results'] = [ x._json_struct() for x in counters]
    pdb.set_trace()
    return json_struct

config = Config()
try:
    sincedate = datetime.strptime( config.since, '%m/%d/%y')
except ValueError:
    sincedate = datetime.strptime( config.since, '%m/%d/%Y')   
print "until = ", config.until
try:
    untildate = datetime.strptime( config.until, '%m/%d/%y')
except ValueError:
    untildate = datetime.strptime( config.until, '%m/%d/%Y')
counters = []
currentuntildate = sincedate
weekcount = 0

print "dates = ", sincedate, " => ",untildate
os.chdir(config.repository_root)
if config.do_fetch:
    if config.print_normal: print 'Fetching updates'
    check_call(['git', 'fetch', 'origin'])

while True:

    git_log_command = ['git', 'log', 'origin/master']
    if config.since:
        git_log_command.append('--since="{0}"'.format(config.since))
    if config.until:
        if config.weekly:
            weekcount = weekcount + 1
            currentuntildate = sincedate + timedelta( weeks=weekcount )
            if currentuntildate > untildate:
                currentuntildate = untildate
        else:
            currentuntildate = untildate
        git_log_command.append('--until="{0}/{1}/{2}"'.format(currentuntildate.month, currentuntildate.day,currentuntildate.year))

    log = Popen(git_log_command, stdout=PIPE)
    counter = Counter(log.stdout, config, sincedate, currentuntildate)
    counter.start()

    #pdb.set_trace()
    if config.print_normal:
        max_digits = 1
        if counter.count > 0:
            max_digits = int(math.log10(counter.count))+1
        print('Commits')
        if config.since:
            print( 'since {0}'.format(sincedate)),
        if currentuntildate:
            print( 'until {0}'.format(currentuntildate)),
        if config.weekly:
            print( ', weekly'),
        print ':'
        breakdown = counter.count_by_person.items()
        breakdown.sort(key=lambda x: -x[1])
        for value in breakdown:
            print( '{0} {1}'.format(str(value[1]).rjust(max_digits), value[0]) )

    if config.print_total:
        print counter.count
    elif config.print_normal or config.print_verbose:
        print( '{0} total'.format(counter.count))

    counters.append( counter )

    if config.weekly == False or untildate == currentuntildate:
        break

if False or config.json_file:
    json_struct = _build_json_struct(config, counters)
    json_string = 'commits = '+ json.dumps(json_struct, default=handler)
    print json_string
