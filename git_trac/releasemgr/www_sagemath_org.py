"""
Fab file for interaction with the sagemath.org server
"""

try:
    import fabric
    from fabric.api import env, run, sudo, put, settings, cd
    from fabric.contrib.files import exists
except ImportError:
    # Fabric shoud be py3-compatible any time not, but not yet
    # Evil hack
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
    with cd('/home/sagemath/upstream'):
        run('ls -al')
        run('wget ' + url)
    with cd('/www-data/sagemath-org/scripts'):
        run('./mirror_upstream.py /home/sagemath/upstream')
        run('./mirror-index.py')
        run('./fix_permissions.sh')
    run('/www-data/sagemath-org/go_live.sh')
