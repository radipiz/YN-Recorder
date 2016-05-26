import logging
import os

logger = logging.getLogger(__name__)


def ensure_directory(directory):
    logger.debug('Ensuring %s' % (directory))
    if not os.path.exists(directory):
        logger.info('%s does not exist, creating' % (directory))
        os.makedirs(directory)


def human_format(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])
