from collections import deque
from dataclasses import dataclass, field
from typing import TypeVar, Generic

StackType = TypeVar('StackType')


@dataclass
class Stack(Generic[StackType]):
    _items: deque[StackType] = field(default_factory=deque)

    def push(self, item: StackType) -> None:
        self._items.appendleft(item)

    def pop(self) -> StackType:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> StackType | None:
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __str__(self) -> str:
        return f'Stack({StackType}): {self._items}'
