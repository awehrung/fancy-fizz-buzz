"""
Diff 2→3: make Number immutable, improve type hints, use Context-Manager for ProcessingChain
"""

import asyncio
from asyncio import InvalidStateError
from contextlib import asynccontextmanager
from dataclasses import dataclass
import random
from typing import List, Callable, Optional
from typing_extensions import Self

# TODO later: python 3.12 migration → get rid of typing_extensions import

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


class ProcessingChain:
    def __init__(
        self, queues: List[asyncio.Queue], processors: List[Callable[[Number], Number]]
    ):
        assert len(queues) == len(processors)
        self._queues: List[asyncio.Queue] = queues + [asyncio.Queue()]
        self._processors: List[Callable[[Number], Number]] = processors

        self._tasks: List[asyncio.Task] = list()
        for i in range(len(processors)):
            self._tasks.append(
                asyncio.create_task(
                    self._process(
                        self._queues[i], self._queues[i + 1], self._processors[i]
                    )
                )
            )
        self._observer = asyncio.create_task(self._observe())

    def feed(self, i: Optional[Number]):
        self._queues[0].put_nowait(i)

    @property
    async def results(self):
        running = True
        queue = self._queues[-1]
        while running:
            item: Optional[Number] = await queue.get()
            await asyncio.sleep(abs(random.gauss(0.0, RANDOM_WAIT_SIGMA)))
            if item is None:
                running = False
            else:
                yield str(item)
            queue.task_done()

    def abort(self):
        self._observer.cancel()
        for t in self._tasks:
            t.cancel()

    async def finish(self):
        await asyncio.gather(*self._tasks)
        self._observer.cancel()

    async def _observe(self):
        while True:
            print(
                "------ " + " / ".join([str(queue.qsize()) for queue in self._queues])
            )
            await asyncio.sleep(1)

    @staticmethod
    async def _process(
        in_queue: asyncio.Queue,
        out_queue: asyncio.Queue,
        processor: Callable[[Number], Number],
    ):
        running = True
        while running:
            in_item: Optional[Number] = await in_queue.get()
            await asyncio.sleep(abs(random.gauss(0.0, RANDOM_WAIT_SIGMA)))
            out_item: Optional[Number] = None
            if in_item is None:
                running = False
            else:
                out_item = processor(in_item)

            out_queue.put_nowait(out_item)
            in_queue.task_done()


@asynccontextmanager
async def create_processing_chain(
    queues: List[asyncio.Queue], processors: List[Callable[[Number], Number]]
):
    processing_chain = ProcessingChain(queues, processors)
    try:
        yield processing_chain
        await processing_chain.finish()
    except Exception:
        processing_chain.abort()


async def main():
    limit = 100

    in_queue = asyncio.Queue()
    check_3: Callable[[Number], Number] = lambda n: n.check(3, "Fizz")
    after_3_queue = asyncio.Queue()
    check_5: Callable[[Number], Number] = lambda n: n.check(5, "Buzz")
    after_5_queue = asyncio.Queue()
    check_7: Callable[[Number], Number] = lambda n: n.check(7, "Bazz")
    after_7_queue = asyncio.Queue()
    finalize: Callable[[Number], Number] = lambda n: n.finalize()

    async with create_processing_chain(
        [in_queue, after_3_queue, after_5_queue, after_7_queue],
        [check_3, check_5, check_7, finalize],
    ) as processing_chain:
        for i in range(limit):
            processing_chain.feed(Number(i + 1))
        processing_chain.feed(None)

        async for r in processing_chain.results:
            print(r)


asyncio.run(main())
