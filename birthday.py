#!/usr/bin/env python3
# -- coding: utf-8 --
'''
Notify about birthdays and anniversaries.

Usage:
    bdnotify.py [options] list [--] [<days>...]
    bdnotify.py [options] summary [--] [<year> <month>]

Options:
    -f FILE --file=FILE     specify birthday file [default: ~/.birthday]
    -l LIMIT --limit=LIMIT  limit the number of notifications [default: 0]
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

Event = collections.namedtuple('Event', 'days desc when')


def parse(fileobj, reference_date):
    errors = 0
    for lineno, line in enumerate(fileobj, 1):
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

            match_ymd = DATE_YMD.match(date)
            match_md = DATE_MD.match(date)
            if match_ymd:
                year = int(match_ymd.group(1))
                month = int(match_ymd.group(2))
                day = int(match_ymd.group(3))
            elif match_md:
                year = -1
                month = int(match_md.group(1))
                day = int(match_md.group(2))
            else:
                raise ValueError(f'Malformed date: "{date}"')

            when = datetime.date(reference_date.year, month, day)

            if when < reference_date:
                when = datetime.date(reference_date.year + 1, month, day)

            days = (when - reference_date).days

            if year > 0:
                yrs = when.year - year
                dsc = f'{description} ({yrs})'
            else:
                dsc = description

            yield Event(days, dsc, when)

        except ValueError as e:
            errors += 1
            print(f'{lineno}: {e}')
            continue

    if errors:
        raise SystemExit('Error parsing input file.')


def main():
    args = docopt.docopt(__doc__)

    filename = os.path.expanduser(args['--file'])

    if args['summary']:
        if args['<year>'] and args['<month>']:
            year = int(args['<year>'])
            month = int(args['<month>'])
            when = datetime.date(year, month, 1)
        else:
            when = TODAY.replace(day=1)
            year = when.year
            month = when.month

        with open(filename, encoding='utf-8') as f:
            events = [
                event for event in parse(f, when)
                if event.when.month == month and event.when.year == year]
            events.sort(key=lambda e: e.when)

        def iter_lines():
            if events:
                for e in events:
                    yield f'{e.when}: {e.desc}'
            else:
                yield f'No events in {year}-{month:02}'

        for line in iter_lines():
            print(line)

    else:
        advance_days = [int(a) for a in args['<days>']]

        with open(filename, encoding='utf-8') as f:
            events = [
                event for event in parse(f, TODAY)
                if not advance_days or event.days in advance_days]
        events.sort(key=lambda e: e.days)

        limit = int(args['--limit'])
        if limit > 0:
            events = events[:limit]

        if not events:
            # no events
            return

        def describe(days, desc, when):
            if days == 0:
                t = 'today'
            elif days == 1:
                t = 'tomorrow'
            else:
                t = f'in {int(days)} days'
                if days >= 3:
                    t += f' ({when})'

            return f'{desc} {t}'

        for days, desc, when in events:
            print(describe(days, desc, when))


if __name__ == '__main__':
    main()
