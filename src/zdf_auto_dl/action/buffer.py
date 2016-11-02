# -*- coding: utf-8 -*-
"""


:authors: - Tobias Grosch
"""


class RingBuffer:
    def __init__(self, size_max):
        self.max = size_max
        self.data = []
        self.cur = 0

    def append(self, x):
        if len(self.data) == self.max:
            self.data[self.cur] = x
            self.cur = (self.cur + 1) % self.max

        else:
            self.data.append(x)

    def get(self):
        if len(self.data) == self.max:
            return self.data[self.cur]

        return self.data[-1]
