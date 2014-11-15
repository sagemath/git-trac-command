"""
Fab file for interaction with the sagemath.org server
"""
import os

try:
    import fabric
    from fabric.api import env, run, sudo, put, settings, cd
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
env.user = 'root'
env.hosts = ['www_sagemath_org']


def upload_tarball(url):
    """
    Add tarball to http://sagemath.org/packages/upstream
    """
    if os.path.exists(url):        # is local file
        put(url, os.path.join('/www-data/tmp/upstream', os.path.basename(url)))
    else:                          # should be a url
        with cd('/www-data/tmp/upstream'):
            run('wget --no-directories -p -N ' + url)
    with cd('/www-data/sagemath-org/scripts'):
        run('./mirror_upstream.py /www-data/tmp/upstream')
        run('./mirror-index.py')
        run('./fix_permissions.sh')
    run('/www-data/sagemath-org/go_live.sh')
