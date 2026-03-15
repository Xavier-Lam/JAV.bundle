# coding=utf-8


class Set(object):
    _set = None  # type: list
    _template = None  # type: type

    def __init__(self, template):
        self._template = template
        self._set = []

    def add(self, item):
        if item not in self._set:
            self._set.append(item)

    def clear(self):
        self._set = []

    def new(self):
        rv = self._template()
        self._set.append(rv)
        return rv

    def __iter__(self):
        return iter(self._set)

    def __len__(self):
        return len(self._set)

    def __contains__(self, item):
        return item in self._set

    def __getitem__(self, index):
        return self._set[index]

    def __setitem__(self, index, value):
        self._set[index] = value


class Map(object):
    _map = None  # type: dict

    def __init__(self):
        self._map = {}
        
    def keys(self):
        return self._map.keys()

    def validate_keys(self, valid_keys):
        for key in set(self._map.keys()) - set(valid_keys):
            del self._map[key]

    def __iter__(self):
        return iter(self._map)

    def __len__(self):
        return len(self._map)

    def __contains__(self, key):
        return key in self._map

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._map[key] = value

    def __delitem__(self, key):
        del self._map[key]


class ObjectContainer(object):
    _objects = None  # type: list

    def __init__(self):
        self._objects = []

    def add(self, obj):
        self._objects.append(obj)

    def extend(self, objs):
        self._objects.extend(objs)


class MediaContainer(object):
    _media = None  # type: list

    def __init__(self):
        self._media = []

    def Append(self, obj):
        self._media.append(obj)

    def Count(self, x):
        return self._media.count(x)

    def Index(self, x):
        return self._media.index(x)

    def Extend(self, objs):
        self._media.extend(objs)

    def Insert(self, index, obj):
        self._media.insert(index, obj)

    def Pop(self, index):
        return self._media.pop(index)

    def Remove(self, obj):
        self._media.remove(obj)

    def Sort(self, attr, descending=False):
        self._media.sort(key=lambda x: getattr(x, attr), reverse=descending)

    def Clear(self):
        self._media.clear()


class MessageContainer(object):
    def __init__(self, header, message, title1=None, title2=None):
        self.header = header
        self.message = message
        self.title1 = title1
        self.title2 = title2
