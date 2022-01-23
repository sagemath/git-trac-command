"""
Run bootstrap to create a new confball
"""

import os
from subprocess import Popen, check_call


def run_bootstrap(sha1):
    confball = 'upstream/configure-{}.tar.gz'.format(sha1)
    check_call(['./bootstrap', '-s'])
    if not os.path.exists(confball):
        raise RuntimeError('bootstrap failed to generate {}'.format(confball))
    return confball



