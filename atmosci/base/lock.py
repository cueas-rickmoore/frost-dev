""" Basic file lock implementation
"""

import os
import commands
import errno
import fnmatch
import time

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

LOCK_KEY = '.LOCK'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class LockTimeoutException(Exception):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SimpleFileLock(object):
    """ A file locking agent with context-manager support in order to be able
    use it in a `with` statement.
    """
 
    def __init__(self, protected_filepath, timeout=10, wait_time=.05,
                       lock_key=LOCK_KEY, debug=False):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the time to wait between each lock attempt
        """
        self.debug = debug
        self.lock_fd = None
        self.lock_filepath = self._lockFilepath(protected_filepath)
        self.lock_filename = os.path.split(self.lock_filepath)[1]
        self.lock_key = self.lock_key
        self.protected_filepath = protected_filepath
        self.protected_filename = os.path.split(protected_filepath)[1]
        self.wait_time = wait_time
        self.timeout = timeout
 
    def __del__(self):
        """ Make sure that each instance of FileLock closes it's lockfile.
        """
        self.release()
 
    def __enter__(self):
        """ Context method for the `with` statement that will automatically
        acquire a lock. 
        """
        if not self.isLocked():
            self.acquire()
        return self
 
    def __exit__(self, type, value, traceback):
        """ Context method for the end of the `with` statement that
            automatically releases a lock.
        """
        self.release()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, check again
            every `wait` seconds. Continue until it either gets the lock
            or exceeds `timeout` seconds
            throws `LockTimeoutException` when it fails to get a lock
        """
        start_time = time.time()
        while True:
            try:
                self.lock_fd = os.open(self.lock_filepath,
                                       os.O_CREAT|os.O_EXCL|os.O_RDWR)
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise 
                if (time.time() - start_time) >= self.timeout:
                    self.lock_fd = None
                    msg = "Timeout occured before lock could be secured for %s"
                    raise LockTimeoutException(msg % self.protected_filepath)

                time.sleep(self.wait_time)

        if self.debug:
            print 'created file lock', self.lock_filepath
 
    def release(self):
        """ Release the lock by closing and deleting the lockfile. 
        """
        if self.lock_fd is not None:
            if self.debug:
                print 'removing file lock', self.lock_filepath
            os.close(self.lock_fd)
            self.lock_fd = None
            if self.isLocked():
                os.unlink(self.lock_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def isLocked(self):
        return os.path.exists(self.lock_filepath) and self.lock_fd is not None

    def lockFileKey(self):
        return self.lock_key

    def lockFilename(self):
        return self.lock_filename

    def lockFilepath(self):
        return self.lock_filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _lockFilename(self, protected_filename):
        return protected_filename + self.lockFileKey

    def _lockFilepath(self, protected_filepath):
        dirpath, filename = os.path.split(protected_filepath)
        return os.path.join(dirpath, self.lockFilename(filename))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
 
class TraceableFileLock(SimpleFileLock):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. Also allows discovery of
        process holding the lock via it's PID
    """
    def __init__(self, protected_filepath, timeout=10, wait_time=.05,
                       lock_key=LOCK_KEY, ps_cmd='ps -ef | grep %s',
                       debug=False):
        SimpleFileLock.__init__(self, protected_filepath, timeout, wait_time,
                                      lock_key, debug)
        self.ps_cmd = ps_cmd
        self.search_pattern = self.protected_filename + '.*' + self.lock_key
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def acquire(self):
        """ Attempt to acquire a lock. While the file is locked by another
            process, loop every `wait` seconds until it either the lock
            succeeds or the elapsed wait time exceeds `timeout` seconds.

            Throws FileLockException exception when it fails to get a lock
            within the alotted time.
        """
        start_time = time.time()
        locked = self._removeStaleLocks()
        while locked:
            if self.isMyLock():
                locked = False
            elif (time.time() - start_time) > self.timeout:
                msg = "Timeout occured before lock could be secured for %s"
                raise FileLockException(msg % self.protected_filepath)
            else:
                time.sleep(self.wait_time)
                locked = self._removeStaleLocks()
                if not locked:
                    os.symlink(self.protected_filepath, self.lock_filepath)
                    if self.debug:
                        print 'created file lock', self.lock_filepath

    def isLocked(self):
        dirpath, filename = os.path.split(self.protected_filepath)
        matches = fnmatch.filter(os.listdir(dirpath), self.search_pattern)
        return len(matches) > 0

    def isMyLock(self):
        if self.lock_fd is not None:
            return os.path.exists(self.lock_filepath)
        return False

    def lockFileKey(self):
        pid_part = '.%d' % os.getpid()
        return pid_part + self.lock_key
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _removeLock(self):
        if os.path.exists(self.lock_filepath):
            if debug:
                print 'removing file lock', self.lock_filepath
            os.remove(self.lock_filepath)
        self.lock_fd = None

    def _removeStaleLocks(self):
        dirpath, filename = os.path.split(self.protected_filepath)
        matches = fnmatch.filter(os.listdir(dirpath), self.search_pattern)
        if debug:
            print len(matches), 'stale locks for', self.protected_filepath

        num_locks = 0
        for lock_filename in matches:
            pid = lock_filename.split('.')[-2]
            result = commands.getoutput(self.ps_cmd % pid)
            if pid in result and result.split()[1] == pid:
                num_locks += 1
                if debug:
                    print 'lock for process %s is active'
            else:
                if debug:
                    print 'removing stale lock set by process', pid
                lock_filepath = os.path.join(dirpath, lock_filename)
                os.remove(lock_filepath)

        return num_locks < 1

