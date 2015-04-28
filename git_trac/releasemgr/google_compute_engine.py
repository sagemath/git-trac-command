"""
Fab file for interaction with our GCE instance
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
env.user = 'sagemath'
env.hosts = ['google_compute_engine']


def upload_tarball(url):
    """
    Add tarball to http://sagemath.org/packages/upstream
    """
    assert False, 'TODO'
    if os.path.exists(url):        # is local file
        put(url, os.path.join('/home/sagemath/files/devel', os.path.basename(url)))
    else:                          # should be a url
        with cd('/home/sagemath/files/devel/'):
            run('wget --no-directories -p -N ' + url)
    run('/home/sagemath/website/scripts/mirror-index.py')
    run('/home/sagemath/publish-files.sh')


    
def upload_dist_tarball(tarball):
    """
    Add tarball to http://sagemath.org/packages/upstream
    """
    basename = os.path.basename(tarball)
    put(tarball, os.path.join('/home/sagemath/files/devel', basename))
    run('/home/sagemath/website/scripts/mirror-index.py')
    run('/home/sagemath/publish-files.sh')

