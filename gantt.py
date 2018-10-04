from datetime import *

DEFAULT_ERROR = 0.5
ME_TIME_HOURS = 10
WORK_TIME_START = time(9)
WORK_TIME_END = time(22)
WORK_TIME_DURATION = timedelta(hours=WORK_TIME_END.hour-WORK_TIME_START.hour)
REST_TIME_DURATION = timedelta(hours=24) - WORK_TIME_DURATION


def in_work(when):
    if WORK_TIME_START <= when.time() <= WORK_TIME_END:
        return True
    return False


def in_rest(when):
    return not in_work(when)


def next_work(to):
    day = to.day + 1
    if to.time() <= WORK_TIME_START: # we're in the morning
        day -= 1
    return datetime.combine(to.date(), WORK_TIME_START, tzinfo=to.tzinfo)


def next_rest(to):
    return datetime.combine(to.date(), WORK_TIME_END, tzinfo=to.tzinfo)


class TimeBlock:

    colour_map = {
        'start_buff': 'bg-info',
        'task': 'bg-warning',
        'error': 'bg-danger',
        'end_buff': 'bg-success',
        'blank': 'bg-secondary'
    }

    @classmethod
    def rest(cls, offset=None):
        dt = REST_TIME_DURATION
        if offset:
            dt = offset
        obj = cls(dt, 'bed')
        return obj

    def __init__(self, duration, cat=None):
        self.duration = duration
        self.cat = cat
        self.start = None
        self.end = None

    def as_p(self, start, end):
        return self.duration.total_seconds() / (end.timestamp() - start.timestamp()) * 100

    def cut(self, *, to=None, off=None, new_cat=None):
        if to is not None:
            remaining = self.duration - to
            self.duration = to
        elif off is not None:
            remaining = off
            self.duration = self.duration - off
        else:
            raise Exception("hehe")

        if new_cat is None:
            new_cat = self.cat

        if remaining.total_seconds() < 0:
            raise IndexError("erm")

        return TimeBlock(remaining, new_cat)

    def __repr__(self):
        return "<TimeBlock duration: {} cat: {}>".format(self.duration, self.cat)

    @property
    def colour(self):
        return self.colour_map.get(self.cat, 'bg-danger')


class Bar:

    def __init__(self, start):
        self.start = start
        self.q = []

    @property
    def end(self):
        end = self.start
        for block in self.q:
            end += block.duration
        return end

    def __iter__(self):
        d = timedelta()
        for block in self.q:
            block.start = self.start + d
            d += block.duration
            block.end = self.start + d
            yield block

    def __len__(self):
        return len(self.q)

    def __repr__(self):
        bits = []
        for block in self:
            bits.append("{} to {} - {}".format(block.start, block.end, block.cat))
        return "<DateQue: " + "\n".join(bits) + ">"

    def serialise(self, min, max):
        return [{'start': block.start.timestamp(),
                 'duration': block.as_p(min, max),
                 'colour': block.colour } for block in self]


class TaskBar(Bar):

    def __init__(self, start, task):
        self.task = task
        self.start = start
        self._end = task.due
        self.name = task.name

        self.remaining = TimeBlock(task.remaining, 'task')
        self.error = TimeBlock(task.error, 'error')
        self.end_buffer = timedelta()

        self._q = []

        self._insert_block(self.remaining)
        self._insert_block(self.error)

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, val):
        self._end = val

    def _insert_block(self, block):
        self._q.append(block)

    @property
    def q(self):
        q = self._q.copy()
        q.append(self.buff)
        return q

    def _q_length(self):
        return sum((block.duration for block in self._q), timedelta())

    @property
    def buff(self):
        return TimeBlock((self.end - self.start) - self._q_length(), 'end_buff')

    def __iter__(self):
        d = timedelta()
        for block in self.q:
            block.start = self.start + d
            d += block.duration
            block.end = self.start + d
            yield block

    def __len__(self):
        return len(self.q)

    def __repr__(self):
        bits = []
        for block in self:
            bits.append("{} to {} - {}".format(block.start, block.end, block.cat))
        return "<DateQue: " + "\n".join(bits) + ">"


class Gantt:

    def __init__(self, start, tasks):
        self.start = start
        self.bars = [task.to_bar(start) for task in tasks]
        self.optimize()

    def optimize(self):
        self.bars.sort(key=lambda bar: bar.buff.duration)#, reverse=True)
        offset = timedelta()
        for bar in self.bars:
            start_buff = bar.buff.cut(off=offset, new_cat='start_buff')
            bar._q.insert(0, start_buff)
            bar.start_buffer = start_buff
            offset = bar._q_length()

    def __iter__(self):
        for bar in self.bars:
            yield bar

    @property
    def longest(self):
        return max(self.bars, key=lambda bar: bar.end).end

    def names(self):
        return (bar.task.name for bar in self.bars)

    def make_day_bar(self):
        bar = Bar(self.start)
        bit = next_rest(self.start) - self.start
        bar.q.append(TimeBlock(bit, 'start_buff'))
        while bar.end < self.longest:
            bar.q.append(TimeBlock(REST_TIME_DURATION, 'blank'))
            bar.q.append(TimeBlock(WORK_TIME_DURATION, 'start_buff'))
        return bar

    def serialise(self):
        return {'min': self.start.timestamp(),
                'max': self.longest.timestamp(),
                'tasks': [{'name': task.name, 'blocks': task.serialise(self.start, self.longest)} for task in self],
                'dayBar': self.make_day_bar().serialise(self.start, self.longest)}
