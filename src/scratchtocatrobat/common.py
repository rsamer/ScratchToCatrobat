#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
import copy
import hashlib
import os
import socket
import sys
import tempfile
import time
import urllib2
import zipfile
import shutil
from functools import wraps
from itertools import chain
from itertools import repeat
from itertools import islice
import java
from javax.sound.sampled import AudioSystem
from org.python.core import PyReflectedField  # pydev: @UnresolvedImport
from scratchtocatrobat import logger

log = logger.log

# TODO: move into common_testing
def get_project_base_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def is_unix_platform():
    return java.io.File.separatorChar == '/'


JYTHON_BINARY = "jython" if is_unix_platform() else "jython.bat"


def isList(obj):
    return isinstance(obj, list)


class ScratchtobatError(Exception):
    pass

def md5_hash(input_path):
    with open(input_path, "rb") as fp:
        return hashlib.md5(fp.read()).hexdigest()

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def copy_dir(source_dir, destination_dir, overwrite=False):
    if overwrite:
        rm_dir(destination_dir)
    shutil.copytree(source_dir, destination_dir)

def rm_dir(dir_path):
    if not os.path.isdir(dir_path):
        return
    shutil.rmtree(dir_path)

# source for pad methods: http://stackoverflow.com/a/3438986
def pad_infinite(iterable, padding=None):
    return chain(iterable, repeat(padding))

def pad(iterable, size, padding=None):
    return islice(pad_infinite(iterable, padding), size)

class DictAccessWrapper(object):
    def __init__(self, dict_object):
        if isinstance(dict_object, set):
            dict_object = dict.fromkeys(dict_object, None)
        assert isinstance(dict_object, dict)
        self.__dict_object = copy.deepcopy(dict_object)

    def _checked_dict_access(self):
        dict_ = self._dict_access_object()
        assert isinstance(dict_, dict)
        return dict_

    def __getattr__(self, name):
        def get():
            return self.__dict_object.get(key)

        def contains():
            return key in self.__dict_object

        key = list(pad(name.split("_", 2), 2))[1]
        if name.startswith("get_"):
            return get
        elif name.startswith("contains_"):
            return contains
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    def __try_wrapped_access(self, key):
        try:
            return self.__dict_object[key]
        except KeyError:
            raise KeyError("Key '{}' is not available for '{}'. Available keys: {}".format(key, self, self.__dict_object.keys()))

    def __getitem__(self, key):
        return self.__try_wrapped_access(key)


# from Python 3 based on: http://stackoverflow.com/a/19299884
class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    import warnings as _warnings
    import os as _os

    def __init__(self, suffix="", prefix="tmp", dir_=None, remove_on_exit=True):
        self._closed = False
        self.name = None  # Handle mkdtemp raising an exception
        self.name = tempfile.mkdtemp(suffix, prefix, dir_)
        self.remove_on_exit = remove_on_exit

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def cleanup(self, _warn=False):
        if self.name and not self._closed and self.remove_on_exit:
            try:
                self._rmtree(self.name)
            except (TypeError, AttributeError) as ex:
                # Issue #10188: Emit a warning on stderr
                # if the directory could not be cleaned
                # up due to missing globals
                if "None" not in str(ex):
                    raise
                sys.stderr.write("ERROR: {!r} while cleaning up {!r}".format(ex, self,))
                return
            self._closed = True
            if _warn:
                self._warn("Implicitly cleaning up {!r}".format(self), _warn.ResourceWarning)

    def __exit__(self, _exc, _value, _tb):
        self.cleanup()

    def __del__(self):
        # Issue a ResourceWarning if implicit cleanup needed
        self.cleanup(_warn=True)

    # XXX (ncoghlan): The following code attempts to make
    # this class tolerant of the module nulling out process
    # that happens during CPython interpreter shutdown
    # Alas, it doesn't actually manage it. See issue #10188
    _listdir = staticmethod(_os.listdir)
    _path_exists = staticmethod(_os.path.exists)
    _isdir = staticmethod(_os.path.isdir)
    _islink = staticmethod(_os.path.islink)
    _path_join = staticmethod(_os.path.join)
    _remove = staticmethod(_os.remove)
    _rmdir = staticmethod(_os.rmdir)
    _warn = _warnings.warn

    def _rmtree(self, path):
        # Essentially a stripped down version of shutil.rmtree.  We can't
        # use globals because they may be None'ed out at shutdown.
        for name in self._listdir(path):
            fullname = self._path_join(path, name)
            try:
                isdir = self._isdir(fullname) and not self._islink(fullname)
            except OSError:
                isdir = False
            if isdir:
                self._rmtree(fullname)
            else:
                try:
                    self._remove(fullname)
                except OSError:
                    pass
        try:
            self._rmdir(path)
        except OSError:
            pass
        if self._path_exists(path):
            log.warning("could not be deleted from temporary directory: %s", path)


# based on: http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
def retry(ExceptionToCheck, tries=4, delay=1, backoff=1, hook=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while True:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    if mtries > 0:
                        if hook:
                            hook(e, mtries, mdelay)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
                        raise e

        return f_retry  # true decorator

    return deco_retry

def fields_of(java_class):
    assert isinstance(java_class, java.lang.Class)
    return [name for name, type_ in vars(java_class).iteritems() if isinstance(type_, PyReflectedField)]

def url_response_data(url, retries=4, hook=None, timeout=4, log=log):
    def retry_hook(exc, tries, delay):
        log.warning("  retrying after %s:'%s' in %f secs (remaining trys: %d)", type(exc).__name__, exc, delay, tries)
    if hook is None:
        hook = retry_hook
    log.info("Requesting web api url: {}".format(url))

#     @retry((urllib2.URLError, socket.timeout), tries=retries, hook=hook)
    @retry((socket.timeout), tries=retries, hook=hook)
    def request():
        return urllib2.urlopen(url, timeout=timeout).read()

    try:
        return request()
    except socket.timeout:
        # WORKAROUND: little more descriptive
        raise IOError("socket.timeout")

def content_of(path):
    with open(path) as f:
        return f.read()

def length_of_audio_file_in_secs(file_path):
    audioInputStream = AudioSystem.getAudioInputStream(java.io.File(file_path))
    format_ = audioInputStream.getFormat()
    frames = audioInputStream.getFrameLength()
    return float(frames) / format_.getFrameRate()

def get_os_platform():
    """return platform name, but for Jython it uses os.name Java property"""
    ver = sys.platform.lower()
    if ver.startswith('java'):
        ver = java.lang.System.getProperty("os.name").lower()
    return ver

def int_or_float(str_value):
    assert isinstance(str_value, (str, unicode))
    try:
        value = int(str_value)
    except ValueError:
        try:
            value = float(str_value)
        except ValueError:
            value = None
    return value

def extract(zip_path, extraction_path):
    with zipfile.ZipFile(zip_path, 'r') as myzip:
        myzip.extractall(extraction_path)
