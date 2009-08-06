import shutil
import sys
import StringIO
from os.path import join, dirname
from jarn.mkrelease.testing import SubversionSetup, JailSetup
from jarn.mkrelease.process import Process
from gitsvnhelpers import config

class BaseTestCase(SubversionSetup):

    name = 'svn'
    source = 'testrepo.svn'
    packagename = 'testpackage'

    def setUp(self):
        JailSetup.setUp(self)
        # copy the test repo to temp, we perform all checkouts from there:
        try:
            original_repo = join(dirname(__file__), 'tests', self.source)
            # the target folder needs to be the packagename, so that the
            # file:/// urls used throughout testing match the pacakge name
            # normally, the filesystem name doesn't matter, when it's being
            # served via http
            self.repo = join(self.tempdir, self.packagename)
            shutil.copytree(original_repo, self.repo)
        except:
            self.cleanUp()
            raise

    def checkout(self, path='trunk'):
        process = Process(quiet=True)
        self.checkoutdir = join(self.tempdir, self.packagename)
        process.system('svn checkout file://%s/%s %s' % (self.repo,
            path, self.checkoutdir))


class StdOut(StringIO.StringIO):
    """ A StringIO based stdout replacement that optionally mirrors all
        output to stdout in addition to capturing it.
    """

    def __init__(self, stdout):
        self.__stdout = stdout
        StringIO.StringIO.__init__(self)

    def write(self, s):
        # uncomment the following for debugging tests!
        #self.__stdout.write(s)
        StringIO.StringIO.write(self, s)

    def read(self):
        self.seek(0)
        self.__stdout.write(StringIO.StringIO.read(self))


class CommandTestCase(BaseTestCase):
    """ a test class that captures stdout and stderr and points GIT_CACHE
        to a temporary directory
    """

    def setUp(self):
        BaseTestCase.setUp(self)
        config.GIT_CACHE = join(self.tempdir, '.gitcache/')
        self.out = StdOut(sys.stdout)
        self.err = StdOut(sys.stdout)
        sys.stdout = self.out
        sys.stderr = self.err

    def cleanUp(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
