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
env.user = 'vbraun'
env.hosts = ['sagedev_org']


    
def upload_dist_tarball(tarball):
    """
    Add tarball to http://sage.sagedev.org/home/release/
    """
    basename = os.path.basename(tarball)
    put(tarball, os.path.join('~/release', basename))
    run('ln -f ~/release/{0} ~/release/pub/{0}'.format(basename))
    run('sudo -H -u  sagemath /home/sagemath/mirror')
