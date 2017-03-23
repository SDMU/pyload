# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from ..layer.legacy.collections_ import MutableMapping
from .init import InscDict


__all__ = [
    'DeleteError',
    'Info',
    'InscInfo',
    'ReadError',
    'SyncInfo',
    'WriteError']


class ReadError(KeyError):

    def __str__(self):
        return """<ReadError {0}>""".format(self.message)


class WriteError(KeyError):

    def __str__(self):
        return """<WriteError {0}>""".format(self.message)


class DeleteError(KeyError):

    def __str__(self):
        return """<DeleteError {0}>""".format(self.message)


class Info(MutableMapping):

    __slots__ = [
        '__deleteable__',
        '__dict__',
        '__readable__',
        '__updateable__',
        '__writeable__']

    __readable__ = True
    __writeable__ = True
    __updateable__ = True
    __deleteable__ = True

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __delattr__(self, name):
        try:
            self.__delitem__(name)
        except DeleteError:
            raise
        except KeyError:
            pass

    def __getitem__(self, key):
        if not self.readable:
            raise ReadError
        return self.__dict__[key]

    def __setitem__(self, key, value):
        if not self.writable or not self.updateable and key not in self.__dict__:
            raise WriteError
        self.__dict__[key] = value

    def __delitem__(self, key):
        if not self.deletable:
            raise DeleteError
        del self.__dict__[key]

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def __str__(self):
        return """<Info {0}>""".format(self.__dict__)

    @property
    def readable(self):
        return bool(self.__readable__)

    @property
    def writable(self):
        return bool(self.__writeable__)

    @property
    def updateable(self):
        return bool(self.__updateable__)

    @property
    def deletable(self):
        return bool(self.__deleteable__)

    def lock(self, read=True, write=True, update=False, delete=False):
        self.__readable__ = read
        self.__writeable__ = write
        self.__updateable__ = update
        self.__deleteable__ = delete

    def unlock(self):
        self.__readable__ = True
        self.__writeable__ = True
        self.__updateable__ = True
        self.__deleteable__ = True


class InscInfo(InscDict, Info):

    __slots__ = []

    def __getitem__(self, key):
        if not self.readable:
            raise ReadError
        return InscDict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if not self.writable or not self.updateable and key.lower() not in self.__dict__:
            raise WriteError
        InscDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if not self.deletable:
            raise DeleteError
        InscDict.__delitem__(self, key)

    def __str__(self):
        return """<InscInfo {0}>""".format(self.__dict__)


class SyncInfo(Info):

    __slots__ = ['__local__', '__remote__']

    __local__ = None  # NOTE: Refer to the internal __dict__ used by <Info> class
    __remote__ = None

    def __init__(self, remotedict, *args, **kwargs):
        Info.__init__(self, *args, **kwargs)
        self.__local__ = self.__dict__
        self.__remote__ = remotedict
        self.sync()

    def __setitem__(self, key, value):
        Info.__setitem__(self, key, value)
        self.__remote__[key] = value

    def __delitem__(self, key):
        Info.__delitem__(self, key)
        del self.__remote__[key]

    def sync(self, reverse=False):
        if reverse:
            self.synclocal()
        else:
            self.syncremote()

    def syncremote(self):
        self.__remote__.update(self.copy())

    def synclocal(self):
        d = dict((k, v) for k, v in self.__remote__.items() if k in self)
        self.update(d)
