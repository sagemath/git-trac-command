"""
Fab file for interaction sagepad.org
"""
import os

try:
    import fabric
    from fabric.api import env, run, sudo, put, settings, cd, hosts
    from fabric.contrib.files import exists
except ImportError:
    # Fabric shoud be py3-compatible any time now, but not yet
    # Evil hack to make importable in py3 tests
    class AttrDict(dict):
        def __init__(self, *args, **kwargs):
            super(AttrDict, self).__init__(*args, **kwargs)
            self.__dict__ = self
    env = AttrDict()

env.use_ssh_config = True
env.user = 'files'
env.hosts = ['sagepad_org']
env.host_string = 'sagepad_org'


def rsync_upstream_packages():
    """
    pull upstream packages via rsync
    """
    run('rsync --archive --recursive rsync.sagemath.org::spkgs/upstream /home/files-pub')
