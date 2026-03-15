# coding=utf-8


class _Log(object):
    def __call__(self, fmt, *args):
        pass

    def Debug(self, fmt, *args):
        pass

    def Info(self, fmt, *args):
        pass

    def Warn(self, fmt, *args):
        pass

    def Error(self, fmt, *args):
        pass

    def Critical(self, fmt, *args):
        pass

    def Exception(self, fmt, *args):
        pass

    def Stack(self):
        pass


Log = _Log()
