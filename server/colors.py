from logging import Formatter

import gevent

class Colors(object):
    BLUE = '\033[1;94m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    RED = '\033[1;91m'
    END = '\033[0m'

class ColoredFormatter(Formatter):
    def __init__(self):
        self.datefmt = '%Y/%m/%d %H:%M:%S'

    def format(self, record):
        color = Colors.RED

        # WARNING = 30
        if record.levelno < 30:
            color = Colors.GREEN
        elif record.levelno == 30:
            color = Colors.YELLOW

        self._fmt = (color + '%(asctime)s | ' +
            str(id(gevent.getcurrent()))[-4:] + ':%(name)s:%(lineno)d' +
            Colors.END + ' %(message)s'
        )
        return Formatter.format(self, record)
