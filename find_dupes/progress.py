"""
Progress bar module
"""

from __future__ import print_function

import sys
import re


class ProgressBar(object):
    DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
    FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(remaining)d remaining'
    FULL_END = {'running': '%(remaining)d remaining', 'done:': '%(done)s'}
    FULL_DONE = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(done)s'

    def __init__(self, total, width=40, fmt=DEFAULT, symbol='=',
                 output=sys.stderr, reverse=False):
        assert len(symbol) == 1

        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.reverse = reverse
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d',
                          r'\g<name>%dd' % len(str(total)), fmt)

        self.current = 0

    def __call__(self, done=''):
        try:
            percent = self.current / float(self.total)
        except ZeroDivisionError:
            percent = 1

        size = int(self.width * percent)
        remaining = self.total - self.current
        prog_bar = '[' + self.symbol * size + ' ' * (self.width - size) + ']'

        args = {
            'total': self.total,
            'bar': prog_bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining,
            'done': done
        }
        print('\r' + self.fmt % args, file=self.output, end='')

    def done(self):
        self()
        self.current = self.total
        self.fmt = ProgressBar.FULL_DONE
        self('DONE' + ' ' * 100)
        print('', file=self.output)

    def print_progress(self, remaining_value):

        max_value = int(self.total)
        remaining_value = int(remaining_value)
        if self.reverse:
            current_value = max_value - remaining_value
        else:
            current_value = remaining_value
        if current_value == 0:
            self.current = 0
            self()
        elif current_value < max_value:
            self.current = current_value
            self()
        elif current_value == max_value:
            self.current = max_value
            self.done()
