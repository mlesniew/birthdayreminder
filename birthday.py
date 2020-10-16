#!/usr/bin/env python3
# -- coding: utf-8 --
'''
Notify about birthdays and anniversaries.

Usage:
    bdnotify.py [options] list [--] [<days>...]
    bdnotify.py [options] summary [--] [<year> <month>]

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

TODAY = datetime.date.today()


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

    def get_description_with_years(self, year=None):
        if self.year:
            return f'{self.description} ({year - self.year})'
        else:
            return self.description

    @property
    def reminder_text(self):
        ret = self.get_description_with_years(self.next_date.year)
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


def main():
    args = docopt.docopt(__doc__)

    filename = os.path.expanduser(args['--file'])

    events = list(parse(filename))

    if args['summary']:
        if args['<year>'] and args['<month>']:
            when = datetime.date(int(args['<year>']), int(args['<month>']), 1)
        else:
            when = datetime.date.today()

        events = [event for event in events
                  if event.month == when.month and (not event.year or event.year <= when.year)]

        events.sort(key=lambda e: e.day)

        if events:
            for e in events:
                print(f'{when.year:04}-{when.month:02}-{e.day:02}: {e.get_description_with_years(when.year)}')
        else:
            print(f'No events in {when.year:04}-{when.month:02}')

    else:
        advance_days = [int(a) for a in args['<days>']]
        events = [event for event in events
                  if not advance_days or events.days_remaining in advance_days]
        events.sort(key=lambda e: e.days_remaining)

        for event in events:
            print(event.reminder_text)


if __name__ == '__main__':
    main()
