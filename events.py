from typing import Any, Set, List, Callable, Generic, TypeVar, cast
import weakref

T = TypeVar("T", bound=Callable[..., None])


class Event(Generic[T]):
    def asTypedCallback(f: Callable) -> T:
        return cast(T, f)

    def __init__(self) -> None:
        self._callbacks: Set[weakref.WeakMethod] = set()

    def add(self, func: T) -> None:
        self._callbacks.add(weakref.WeakMethod(func))

    def remove(self, func: T) -> None:
        self._callbacks.remove(weakref.WeakMethod(func))

    def __iadd__(self, other: T) -> "Event":
        self.add(other)
        return self

    def __isub__(self, other: T) -> "Event":
        self.remove(other)
        return self

    @asTypedCallback
    def __call__(self, *args: Any, **kwds: Any) -> None:
        toRemove: List[weakref.WeakMethod] = []
        for ref in list(self._callbacks):
            r = ref()
            if r is None:
                toRemove.append(ref)
                continue
            if len(args) == 0 and len(kwds) == 0:
                r()
            elif len(kwds) == 0:
                r(*args)
            elif len(args) == 0:
                r(**kwds)
            else:
                r(args, kwds)
        for ref in toRemove:
            self._callbacks.remove(ref)
