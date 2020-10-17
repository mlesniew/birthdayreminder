#!/usr/bin/env python3
# -- coding: utf-8 --
'''
Notify about birthdays and anniversaries.

Usage:
    bdnotify.py [options] list [--] [<days>...]

Options:
    -f FILE --file=FILE     specify birthday file [default: ~/.birthday]
'''

import datetime
import json
import os.path
import re
import collections

import docopt

DATE_YMD = re.compile('([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})')
DATE_MD = re.compile('([0-9]{1,2})-([0-9]{1,2})')


class Event:
    today = datetime.date.today()

    def __init__(self, description, datespec):
        self.description = description

        match_ymd = DATE_YMD.match(datespec)
        match_md = DATE_MD.match(datespec)

        if match_ymd:
            self.year = int(match_ymd.group(1))
            self.month = int(match_ymd.group(2))
            self.day = int(match_ymd.group(3))
        elif match_md:
            self.year = None
            self.month = int(match_md.group(1))
            self.day = int(match_md.group(2))
        else:
            raise ValueError(f'Malformed date: "{date}"')

    @property
    def date(self):
        return datetime.date(self.year or datetime.date.min.year, self.month, self.day)

    @property
    def next_date(self):
        ret = self.date.replace(year=self.today.year)
        if ret < self.today:
            ret = ret.replace(year=ret.year + 1)
        return ret

    @property
    def days_remaining(self):
        return (self.next_date - self.today).days

    @property
    def reminder_text(self):
        ret = self.description
        if self.year:
            ret += f' ({self.today.year - self.year})'
        days = self.days_remaining
        if days == 0:
            ret += 'today'
        elif days == 1:
            ret += 'tomorrow'
        else:
            ret += f' in {int(days)} days'
            if days >= 3:
                ret += f' ({self.next_date})'
        return ret


def parse(path):
    errors = 0
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            # remove comments
            if '#' in line:
                line = line[:line.find('#')]

            # trim whitespace
            line = line.strip()

            # skip all empty lines
            if not line:
                continue

            # parse line
            try:
                date, description = line.split(None, 1)
                yield Event(description, date)
            except ValueError as e:
                print(f'{path}:{lineno}: {e}')
                errors += 1
    if errors:
        raise ValueError(f'{errors} errors in {path}')


def main():
    args = docopt.docopt(__doc__)

    filename = os.path.expanduser(args['--file'])

    events = list(parse(filename))

    advance_days = [int(a) for a in args['<days>']]
    events = [event for event in events
              if not advance_days or event.days_remaining in advance_days]
    events.sort(key=lambda e: e.days_remaining)

    for event in events:
        print(event.reminder_text)


if __name__ == '__main__':
    main()
