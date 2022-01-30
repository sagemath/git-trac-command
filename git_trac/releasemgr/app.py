# -*- coding: utf-8 -*-
"""
The Release Management App
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import re
import tempfile
import logging
import fabric.tasks

from ..app import Application

from ..people import RELEASE_MANAGER
from git_trac.logger import logger as log
from git_trac.git_error import GitError
from git_trac.releasemgr.version_string import VersionString
from git_trac.releasemgr.bootstrap import run_bootstrap
from git_trac.releasemgr.fileserver_sagemath_org import \
    upload_temp_confball as upload_temp_confball_fileserver
from git_trac.releasemgr.sagepad_org import \
    upload_temp_confball as upload_temp_confball_sagepad


class ReleaseApplication(Application):

    def print_ticket(self, ticket_number):
        """
        INPUT:

        - ``ticket_number`` -- a trac ticket number.

        EXAMPLES:

        """
        ticket = self.trac.load(ticket_number)
        from .commit_message import format_ticket
        print(format_ticket(ticket))

    def _commit(self, commit_message, **kwds):
        try:
            fd, tmp = tempfile.mkstemp()
            os.close(fd)
            with open(tmp, 'wb') as f:
                f.write(commit_message.encode('utf-8'))
            self.git.echo.commit(file=tmp, author=RELEASE_MANAGER, **kwds)
        finally:
            os.remove(tmp)

    def _are_dependencies_merged(self, ticket):
        """
        Check that all dependencies are merged
        """
        if not ticket.dependencies.strip():    # no dependencies
            return True
        for dep in ticket.dependencies.replace(',', ' ').split():
            try:
                dep_number = int(dep.lstrip(' #').rstrip())
            except ValueError:
                raise ValueError('invalid dependency: {0}'.format(dep))
            try:
                commit = self.repo.find_release_merge_of_ticket(dep_number)
            except ValueError as error:
                log.debug('ticket not merged: {} ({})'.format(dep_number, error))
                return False
            # commit is merged, good
        return True

    MILESTONE_RE = re.compile(r'sage-[0-9]*\.[0-9\.]*')

    def _is_valid_milestone(self, ticket):
        """
        Check that the milestone is valid (not pending/invalid)
        """
        match = self.MILESTONE_RE.search(ticket.milestone)
        return (match is not None)

    def merge(self, ticket_number, close=False, allow_empty=False,
              ignore_dependencies=False, ignore_name=False):
        """
        Create the "release" merge

        INPUT:

        - ``ticket_number`` -- integer or None. The ticket. If
          ``None`` it will be guessed from the ``branch``.

        - ``close`` -- boolean. Whether to close the trac ticket.

        - ``allow_empty`` -- boolean. Whether to allow empty commits.

        - ``ignore_dependencies`` -- boolean. Whether to check that
          the dependencies are merged.

        - ``ignore_name`` -- boolean. Whether to check that the name
          looks right.
        """
        print('Loading ticket...')
        ticket = self.trac.load(ticket_number)
        if not (ignore_dependencies or self._are_dependencies_merged(ticket)):
            raise ValueError(u'ticket dependencies are not all merged: {0}'
                             .format(ticket.dependencies))
        if not self._is_valid_milestone(ticket):
            raise ValueError(u'ticket milestone is not intended to be merged: {0}'
                             .format(ticket.milestone))
        branch = ticket.branch.strip()
        if len(branch) == 0:
            raise ValueError('no branch on ticket')

        print(u'URL: https://trac.sagemath.org/{0}'.format(ticket.number))
        print(u'Trac #{0}: {1}'.format(ticket.number, ticket.title))
        print(u'Branch {0}'.format(branch))
        print(u'Author(s): {0}'.format(ticket.author))
        print(u'Reviewer(s): {0}'.format(ticket.reviewer))

        import string
        if not ignore_name:
            if not all(author[0].strip() in string.ascii_uppercase
                       for author in ticket.author.split(',')):
                raise ValueError(u'author {0} does not look right'.format(repr(ticket.author)))
            if not all(reviewer[0].strip() in string.ascii_uppercase
                       for reviewer in ticket.reviewer.split(',')):
                raise ValueError(u'reviewer {0} does not look right'.format(repr(ticket.reviewer)))

        from .commit_message import format_ticket
        commit_message = format_ticket(ticket)

        print('Fetching remote branch...')
        self.git.echo.fetch('trac', branch)

        print('Merging ticket...')
        try:
            self.git.echo.merge('FETCH_HEAD', '--no-ff', '--no-commit')
        except GitError as err:
            print(err)
            # Merge conflicts are recognized below
            pass

        status = self.git.status()
        print(status)
        if 'nothing to commit' in status or 'nothing added to commit' in status:
            if not allow_empty:
                raise ValueError('already merged')
            print('This is an empty commit')
            self._commit(commit_message, allow_empty=True)
        else:
            if 'All conflicts fixed but you are still merging.' not in status:
                conflicts = self.git.diff('--name-only', '--diff-filter=U')
                conflicts = ','.join(conflicts.splitlines())
                self.git.merge('--abort')
                raise ValueError('merge was not clean: conflicts in {}'.format(conflicts))
            self._commit(commit_message)

        if close:
            self.close_ticket(ticket)

    def test_merge(self, ticket_number):
        """
        Create the "test" merge

        INPUT:

        - ``ticket_number`` -- integer or None. The ticket. If
          ``None`` it will be guessed from the ``branch``.
        """
        print('Loading ticket...')
        ticket = self.trac.load(ticket_number)
        branch = ticket.branch.strip()
        if len(branch) == 0:
            raise ValueError('no branch on ticket')

        print('Fetching remote branch...')
        self.git.echo.fetch('trac', branch)
        print('Merging ticket...')
        self.git.echo.merge('FETCH_HEAD', '--no-ff', '--no-commit')

        commit_message = u'TEST Trac #{ticket.number}: {ticket.title}'.format(ticket=ticket)
        status = self.git.status()
        if 'nothing to commit' in status or 'nothing added to commit' in status:
            raise ValueError('already merged')
        else:
            if 'All conflicts fixed but you are still merging.' not in status:
                self.git.merge('--abort')
                raise ValueError('merge was not clean')
            self._commit(commit_message)

    def merge_multiple(self, ticket_numbers, limit=0, **kwds):
        successful = []
        errors = []
        try:
            for ticket_number in ticket_numbers:
                try:
                    self.merge(ticket_number)
                    successful.append(ticket_number)
                except ValueError as err:
                    errors.append((ticket_number, str(err)))
                    if u'ticket dependencies' not in str(err) and u'already merged' not in str(err):
                        comment = 'Merge failure on top of:\n\n{}\n\n{}'.format(
                            self.describe().replace('\n', '\n\n'), err)
                        self.set_ticket_to_needs_work(ticket_number, comment)
                if limit and (len(successful) >= limit):
                    break
        finally:
            print("\n### Summary ###\n")
            if len(ticket_numbers) != 1:
                if successful:
                    print('Successfully merged: {0}'.format(', '.join(map(str, successful))))
                for ticket_number, error_message in errors:
                    t = self.trac.load(ticket_number)
                    print(u'')
                    print(u'* {ticket.number} {ticket.title} ({ticket.author})'.format(ticket=t))
                    print(u'  URL: https://trac.sagemath.org/{ticket.number}'.format(ticket=t))
                    print(u'  Error: ' + error_message)

    def close_ticket(self, commit, ticket):
        if ticket.commit != commit.sha1:
            raise RuntimeError('ticket #{0} branch changed (merged={1}, current={2})'
                               .format(ticket.number, commit.sha1, ticket.commit))
        comment = ''
        attributes = {
            '_ts': ticket.timestamp,
            'status': 'closed',
            'resolution': 'fixed',
        }
        notify = True
        if len(ticket.commit) > 0:
            attributes['branch'] = ticket.commit
        return self.trac.authenticated_proxy.ticket.update(
            ticket.number, comment, attributes, notify)

    def close_tickets(self, head, exclude):
        ticket_list = self.repo.release_merges(head, exclude)
        for merge_commit, ticket_commit, ticket_number in ticket_list:
            ticket = self.trac.load(ticket_number)
            if ticket.status == 'closed':
                print('Trac #{0} already closed'.format(ticket_number))
            else:
                print('Trac #{0}: {1} -> closed'.format(ticket_number, ticket.status))
                self.close_ticket(ticket_commit, ticket)

    def publish(self):
        self.repo.head_version()
        self.git.push('--tags', 'trac', 'develop')

    def unmerge(self, ticket_number):
        """
        Undo a "release" merge

        INPUT:

        - ``ticket_number`` -- integer. The ticket.
        """
        commit = self.repo.find_release_merge_of_ticket(ticket_number)
        first_parent = commit.get_parents()[0]
        print(u'Removing {0}'.format(commit.get_message('short')))
        print(u'Parent release commit is {0}'.format(first_parent))
        # git rebase --verbose --preserve-merges shatoremove --onto shaoffirstparent
        self.git.rebase('--verbose', '--rebase-merges',
                        commit.sha1, '--onto', first_parent.sha1)

    def _current_milestone(self):
        # The current milestone does not appear to be available via
        # XML-RPC.  We just infer it from the tags to the extent possible.
        for version in self.repo._tag_iter():
            m = re.match('^(([0-9]+)[.]([0-9]+)([.]([0-9])+)?)([.](b|beta|rc))?', version)
            if m:
                if m.group(6):
                    # development version
                    return 'sage-{}'.format(m.group(1))
                if m.group(5):
                    # released version x.y.z
                    return 'sage-{}.{}.{}'.format(m.group(2), m.group(3), int(m.group(5)) + 1)
                # released version x.y
                return 'sage-{}.{}'.format(m.group(2), int(m.group(3)) + 1)
        raise ValueError('current milestone cannot be determined - no release tags')

    def _normalize_milestone(self, milestone):
        if milestone is None:
            return milestone
        if milestone == 'current':
            return self._current_milestone()
        if not milestone.startswith('sage-'):
            return 'sage-' + milestone
        return milestone

    def _get_ready_tickets(self, milestone=None):
        params = ['status=positive_review']
        milestone = self._normalize_milestone(milestone)
        if milestone:
            params.append('milestone={0}'.format(milestone))
        else:
            params.extend(['milestone!=sage-duplicate/invalid/wontfix',
                           'milestone!=sage-feature',
                           'milestone!=sage-pending',
                           'milestone!=sage-wishlist'])
        querystr = '&'.join(params)
        return self.trac.anonymous_proxy.ticket.query(querystr)

    def todo(self, milestone=None):
        """
        Print a list of tickets that are ready to be merged
        """
        milestone = self._normalize_milestone(milestone)
        tickets = self._get_ready_tickets(milestone=milestone)
        if milestone:
            milestone_str = 'for milestone {} '.format(milestone)
        else:
            milestone_str = ''
        if not tickets:
            print(u'No tickets {}are ready to be merged'.format(milestone_str))
            return
        print(u'The following tickets {}are ready to be merged'.format(milestone_str))
        for ticket_number in tickets:
            t = self.trac.load(ticket_number)
            print(u'* {ticket.number} {ticket.title} ({ticket.author})'.format(ticket=t))
        print(u'Merge tickets with:')
        print(u'git releasemgr merge {0}'.format(' '.join(map(str, tickets))))

    def set_ticket_to_needs_work(self, ticket_number, comment):
        attributes = {
            'status': 'needs_work',
        }
        notify = True
        return self.trac.authenticated_proxy.ticket.update(
            ticket_number, comment, attributes, notify)

    def describe(self):
        self.git.fetch('trac', 'develop')
        return self.git.log('--oneline', '--first-parent', 'FETCH_HEAD~..HEAD')

    def merge_all(self, limit=0, milestone=None):
        """
        Merge all tickets that are ready
        """
        milestone = self._normalize_milestone(milestone)
        tickets = self._get_ready_tickets(milestone=milestone)
        if milestone:
            milestone_str = 'for milestone {} '.format(milestone)
        else:
            milestone_str = ''
        if not tickets:
            print(u'No tickets {}are ready to be merged'.format(milestone_str))
            return
        print(u'Merging tickets {}'.format(milestone_str))
        return self.merge_multiple(tickets, limit=limit)

    def upstream(self, url):
        """
        Add tarball to http://sagemath.org/packages/upstream
        """
        import fabric.tasks
        from .fileserver_sagemath_org import upload_tarball
        url = url.strip(' \xe2\x80\x8b')
        fabric.tasks.execute(upload_tarball, url)
        from .sagepad_org import rsync_upstream_packages
        rsync_upstream_packages()

    def upstream_confball(self):
        version = open('build/pkgs/configure/package-version.txt').read().strip()
        configure = 'upstream/configure-{0}.tar.gz'.format(version)
        self.upstream(configure)

    def dist(self, tarball, devel=True):
        """
        Add tarball to http://sage.sagedev.org/home/release/ and mirror
        """
        import fabric.tasks
        from .fileserver_sagemath_org import upload_dist_tarball
        fabric.tasks.execute(upload_dist_tarball, tarball, devel)

    def release(self, version, check=False):
        """
        Make a new release with the given version string
        """
        v = VersionString(version)
        from .make_release import update_version, create_tarball, check_tarball, check_upgrade
        update_version(version)
        assert version == self.repo.head_version()
        create_tarball()
        tarball = 'dist/sage-{0}.tar.gz'.format(version)
        self.upstream_confball()
        self.dist(tarball, v.is_devel())
        if check:
            check_tarball(tarball)
            stable = self.repo.previous_stable_version()
            check_upgrade(self.git, stable, version)

    def confball(self):
        """
        Create and upload new confball

        This is a tarball containing the configure script, that is, the autotools output. So you can
        build sage without autotools.
        """
        sha1 = self.repo.head.sha1
        confball = run_bootstrap(sha1)
        print('New confball is {}'.format(confball))
        fabric.tasks.execute(upload_temp_confball_fileserver, confball)
        fabric.tasks.execute(upload_temp_confball_sagepad, confball)
        print('Adding the confball to the current commit...')
        self.git.echo.add('build/pkgs/configure/')
        self.git.echo.commit('--amend', '--no-edit')
