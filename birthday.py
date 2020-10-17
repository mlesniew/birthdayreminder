#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import os.path
import re

import requests

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
    def message_id(self):
        desc = f'{self.date} {self.description}'
        hsum = hashlib.sha256(desc.encode('utf-8')).hexdigest()
        return int(hsum, 16) % 0x7fffffff

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


def parse(fileobj):
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
            yield Event(description, date)
        except ValueError as e:
            print(f'{fileobj.name}:{lineno}: {e}')
            errors += 1
    if errors:
        raise ValueError(f'{errors} errors in {fileobj.name}')


def main():
    parser = argparse.ArgumentParser(description='Notify about birthdays and anniversaries.')
    parser.add_argument('--file', '-f',
                        default=os.path.expanduser('~/.birthday'),
                        type=argparse.FileType('r', encoding='utf-8'),
                        help='birthday file path')
    parser.add_argument('--wirepusher', '-w',
                        help='send notifications using Wirepusher to device with the given ID')
    parser.add_argument('days',
                        nargs='*',
                        type=int,
                        help='number of days remaining to generate notification')

    args = parser.parse_args()

    events = list(parse(args.file))

    advance_days = [int(a) for a in args.days]
    events = [event for event in events
              if not advance_days or event.days_remaining in advance_days]
    events.sort(key=lambda e: e.days_remaining)

    for event in events:
        print(event.reminder_text)
        if args.wirepusher:
            requests.post('https://wirepusher.com/send',
                          params={
                              'id': args.wirepusher,
                              'type': 'birthday-reminder',
                              'title': event.description,
                              'message': event.reminder_text,
                              'message_id': event.message_id,
                              })


if __name__ == '__main__':
    main()
