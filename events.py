from typing import Any, Set, List, Callable, cast
import weakref


class Event:
    def __init__(self) -> None:
        self._callbacks: Set[weakref.WeakMethod] = set()

    def add(self, func: Callable) -> None:
        self._callbacks.add(weakref.WeakMethod(func))

    def remove(self, func: Callable) -> None:
        self._callbacks.remove(cast(weakref.WeakMethod, func))

    def __iadd__(self, other: Callable) -> "Event":
        self.add(other)
        return self

    def __isub__(self, other: Callable) -> "Event":
        self.remove(other)
        return self

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        toRemove: List[weakref.WeakMethod] = []
        for ref in self._callbacks:
            r = ref()
            if r is None:
                toRemove.append(ref)
                continue
            if len(args) == 0 and len(kwds) == 0:
                r()
            elif len(kwds) == 0:
                r(args)
            elif len(args) == 0:
                r(kwds)
            else:
                r(args, kwds)
        for ref in toRemove:
            self._callbacks.remove(ref)
