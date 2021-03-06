import optparse
import sys
import os
from os.path import exists

import config
from jarn.mkrelease.tee import popen
from utils import basename
from utils import is_git
from utils import is_svn
from utils import svn_type
from utils import svn_branch
from utils import clone
from commands import Command
from commands import CmdPush
from commands import CmdFetch
from commands import CmdUpdate


class CmdGitify(Command):

    def __init__(self, gitify):
        Command.__init__(self, gitify)
        self.parser = optparse.OptionParser(
            usage = "%prog",
            description = """
            """,
            add_help_option=False)
        self.parser.add_option("-v", "--verbose", dest="verbose",
            action="store_true", default=False,
            help="""Show git-svn output.""")

    def __call__(self):
        options, args = self.parser.parse_args(self.gitify.args[2:])

        package_name = basename()
        svntype = svn_type()

        if svntype == 'tags':
            print "Can't work on tags!"
            sys.exit(1)
        elif svntype == 'unrecognized':
            print "Unrecognized svn structure!"
            sys.exit(1)

        if not exists(config.GIT_CACHE + package_name):
            print "No git repository found in %s." % config.GIT_CACHE
            print "Initiating cloning into cache."
            clone()

        # get the branch svn is on
        remote_branch = svn_branch()
        # the following is just convention:
        local_branch = "local/%s" % remote_branch

        cwd = os.getcwd()
        # perform all index updates in the cache to avoid conflicts
        os.chdir(config.GIT_CACHE + package_name)

        dummy, existing_branches = popen('git b', False, False)
        existing_branches = [b.strip() for b in existing_branches]
        if local_branch in existing_branches:
            popen('git checkout -f %s' % local_branch, False, False)
        else:
            popen('git checkout -f -b %s %s' % (local_branch, remote_branch),
                False, False)

        os.chdir(cwd)
        if not exists('.git'):
            popen('ln -s %s%s/.git' % (config.GIT_CACHE, package_name), False, False)

        print "Git branch '%s' is now following svn branch '%s':" % (
            local_branch, remote_branch)
        popen('svn status')
        popen('git status')


class CmdHelp(Command):

    def __init__(self, gitify):
        Command.__init__(self, gitify)
        self.parser = optparse.OptionParser(
            usage="%prog help [<command>]",
            description="Show help on the given command or about the whole "
                "script if none given.",
            add_help_option=False)

    def __call__(self):
        gitify = self.gitify
        if len(gitify.args) != 3 or gitify.args[2] not in gitify.commands:
            print("usage: %s <command> [options] [args]"
                % os.path.basename(gitify.args[0]))
            print("\nType '%s help <command>' for help on a specific command."
                % os.path.basename(gitify.args[0]))
            print("\nAvailable commands:")
            f_to_name = {}
            for name, f in gitify.commands.iteritems():
                f_to_name.setdefault(f, []).append(name)
            for cmd in sorted(x for x in dir(gitify) if x.startswith('cmd_')):
                name = cmd[4:]
                if name == 'pony':
                    continue
                f = getattr(gitify, cmd)
                aliases = [x for x in f_to_name[f] if x != name]
                if len(aliases):
                    print("    %s (%s)" % (name, ", ".join(aliases)))
                else:
                    print("    %s" % name)
        else:
            print gitify.commands[gitify.args[2]].parser.format_help()


class Gitify(object):

    def __call__(self, **kwargs):

        if len(kwargs) == 0:
            if is_git():
                print "This seems to be a local git repository!"
                return

            if not is_svn():
                print "This only works on svn checkouts!"
                return

        self.cmd_push = CmdPush(self)
        self.cmd_fetch = CmdFetch(self)
        self.cmd_update = CmdUpdate(self)
        self.cmd_gitify = CmdGitify(self)
        self.cmd_help = CmdHelp(self)

        self.commands = dict(
            help=self.cmd_help,
            update=self.cmd_update,
            up=self.cmd_update,
            h=self.cmd_help,
            fetch = self.cmd_fetch,
            push = self.cmd_push,
            gitify = self.cmd_gitify,
        )

        # allow sys.argv to be overridden (used for testing)
        if 'args' in kwargs:
            self.args = ['gitify'] + kwargs['args']
        else:
            self.args = sys.argv

        try:
            command = self.args[1]
        except IndexError:
            command = 'gitify'

        self.commands.get(command, self.unknown)()

    def unknown(self):
        print "Unknown command '%s'." % self.args[1]
        print "Type '%s help' for usage." % \
            os.path.basename(self.args[0])
        sys.exit(1)


gitify = Gitify()
