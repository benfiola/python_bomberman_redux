import pytest


class TmpDirCleanup(object):
    """
    The tmpdir pytest fixture doesn't clean up after itself.
    
    This 'plugin' tries to clean up after the tmpdir fixture.
    """
    def pytest_runtest_teardown(self, item, nextitem):
        tmpdir = item.funcargs.get("tmpdir", None)

        # each item is a test method result, and each test method result contains funcargs, which include
        # all arguments that were passed to the method.  in the event of test fixtures, even ones that rely on other
        # test fixtures, ALL involved test fixtures are present in the funcargs object, which means we just have to see
        # if there's a tmpdir object.
        # the tmpdir object is simply a py.path.LocalPath object.
        if tmpdir and tmpdir.check():
            tmpdir.remove()
            # the parent directory holding all of these test run's tmpdirs still remains.  according to the docs,
            # there's some sort of cleanup, so I'm not going to do anything risky like try to delete a parent directory
            # (since tmpdir's behavior is configurable and there's no guarantee as to whether the parent directory
            # isn't some huge directory that shouldn't be deleted).


pytest.main(['tests'], plugins=[TmpDirCleanup()])
