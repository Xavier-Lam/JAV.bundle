# coding=utf-8


class Proxy(object):

    class Media(object):
        def __init__(self, data, sort_order=None, ext=None, index=None, **kwargs):
            self.data = data
            self.sort_order = sort_order
            self.ext = ext
            self.index = index

    class Preview(Media):
        pass

    class LocalFile(Media):
        pass

    class Remote(Media):
        pass
