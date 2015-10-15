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
    pass


env_sagepad = dict(
    use_ssh_config=True,
    user='files',
    host_string='sagepad_org'
)


def rsync_upstream_packages():
    """
    pull upstream packages via rsync
    """
    with settings(**env_sagepad):
        run('rsync --archive --recursive rsync.sagemath.org::spkgs/upstream /var/www/sage-upstream')
        
