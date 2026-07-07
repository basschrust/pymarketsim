from itertools import count

class IdGenerator:
    def __init__(self):
        self._counter = count(1)

    def __next__(self) -> int:
        return next(self._counter)

id_generator = IdGenerator()
