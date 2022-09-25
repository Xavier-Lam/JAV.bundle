# coding=utf-8


class OrderedSet(list):
    def add(self, item):
        item not in self and self.append(item)

    def union(self, items):
        for item in items:
            self.add(item)
