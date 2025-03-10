"""
Diff 3→4: make ProcessingChain generic, improve creation
"""

import asyncio
import random
from asyncio import InvalidStateError
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import (
    List,
    Callable,
    Optional,
    Tuple,
    TypeVar,
    Generic,
    AsyncGenerator,
)
from typing_extensions import Self

# TODO later: python 3.12 migration → get rid of typing_extensions import, better generics

RANDOM_WAIT_SIGMA = 0.2


@dataclass(frozen=True)
class Number:
    value: int
    _out_name: str = ""
    _finalized: bool = False

    def check(self, divisor: int, replacement: str) -> Self:
        if self.value % divisor == 0:
            return Number(self.value, self._out_name + replacement)
        return self

    def finalize(self) -> Self:
        if self._out_name == "":
            return Number(self.value, str(self.value), True)
        return Number(self.value, self._out_name, True)

    def __repr__(self):
        return f"{self.value} (→{self._out_name}, F:{self._finalized})"

    def __str__(self):
        if not self._finalized:
            raise InvalidStateError("Item is not finalized")
        return self._out_name


T = TypeVar("T")


class ProcessingChain(Generic[T]):
    def __init__(self, *processors: Callable[[T], T]):
        self._queues: Tuple[asyncio.Queue, ...] = tuple(
            asyncio.Queue() for _ in range(len(processors) + 1)
        )
        self._processors: Tuple[Callable[[T], T], ...] = processors

        self._tasks: List[asyncio.Task] = list()
        for i, processor in enumerate(self._processors):
            self._tasks.append(
                asyncio.create_task(
                    self._process(self._queues[i], self._queues[i + 1], processor)
                )
            )
        self._observer = asyncio.create_task(self._observe())

    def feed(self, i: Optional[T]):
        self._queues[0].put_nowait(i)

    @property
    async def results(self) -> AsyncGenerator[str, None]:
        running = True
        queue = self._queues[-1]
        while running:
            item: Optional[T] = await queue.get()
            await asyncio.sleep(abs(random.gauss(0.0, RANDOM_WAIT_SIGMA)))
            if item is None:
                running = False
            else:
                yield str(item)
            queue.task_done()

    def abort(self) -> None:
        self._observer.cancel()
        for t in self._tasks:
            t.cancel()

    async def finish(self) -> None:
        await asyncio.gather(*self._tasks)
        self._observer.cancel()

    async def _observe(self) -> None:
        while True:
            print(
                "------ " + " / ".join([str(queue.qsize()) for queue in self._queues])
            )
            await asyncio.sleep(1)

    @staticmethod
    async def _process(
        in_queue: asyncio.Queue,
        out_queue: asyncio.Queue,
        processor: Callable[[T], T],
    ) -> None:
        running = True
        while running:
            in_item: Optional[T] = await in_queue.get()
            await asyncio.sleep(abs(random.gauss(0.0, RANDOM_WAIT_SIGMA)))
            out_item: Optional[T] = None
            if in_item is None:
                running = False
            else:
                out_item = processor(in_item)

            out_queue.put_nowait(out_item)
            in_queue.task_done()


@asynccontextmanager
async def create_processing_chain(
    *processors: Callable[[T], T]
) -> AsyncGenerator[ProcessingChain[T], None]:
    processing_chain = ProcessingChain(*processors)
    try:
        yield processing_chain
        await processing_chain.finish()
    except Exception as e:
        processing_chain.abort()
        raise e


async def main():
    limit = 100

    async with create_processing_chain(
        lambda n: n.check(3, "Fizz"),
        lambda n: n.check(5, "Buzz"),
        lambda n: n.check(7, "Bazz"),
        lambda n: n.finalize(),
    ) as fizz_buzz_processing_chain:
        for i in range(limit):
            fizz_buzz_processing_chain.feed(Number(i + 1))
        fizz_buzz_processing_chain.feed(None)

        async for r in fizz_buzz_processing_chain.results:
            print(r)


asyncio.run(main())
