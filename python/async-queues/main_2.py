"""
Diff 1→2: abstract queue/worker management into ProcessingChain
"""

import asyncio
import functools
import random
from typing import List, Callable, Optional

RANDOM_WAIT_SIGMA = 0.2


class Number:
    def __init__(self, value: int):
        self.value: int = value
        self.out_name: str = ""


def checker(item: Number, divisor: int, replacement: str):
    if item.value % divisor == 0:
        item.out_name += replacement


def finalize(item: Number):
    if item.out_name == "":
        item.out_name = str(item.value)


class ProcessingChain:
    def __init__(
        self, queues: List[asyncio.Queue], processors: List[Callable[[Number], None]]
    ):
        assert len(queues) == len(processors)
        self._queues: List[asyncio.Queue] = queues + [asyncio.Queue()]
        self._processors: List[Callable[[Number], None]] = processors

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
                yield item.out_name
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
        processor: Callable[[Number], None],
    ):
        running = True
        while running:
            item: Optional[Number] = await in_queue.get()
            await asyncio.sleep(abs(random.gauss(0.0, RANDOM_WAIT_SIGMA)))
            if item is None:
                running = False
            else:
                processor(item)

            out_queue.put_nowait(item)
            in_queue.task_done()


async def main():
    limit = 100

    in_queue = asyncio.Queue()
    check_3 = functools.partial(checker, divisor=3, replacement="Fizz")
    after_3_queue = asyncio.Queue()
    check_5 = functools.partial(checker, divisor=5, replacement="Buzz")
    after_5_queue = asyncio.Queue()
    check_7 = functools.partial(checker, divisor=7, replacement="Bazz")
    after_7_queue = asyncio.Queue()

    processing_chain = ProcessingChain(
        [in_queue, after_3_queue, after_5_queue, after_7_queue],
        [check_3, check_5, check_7, finalize],
    )

    for i in range(limit):
        processing_chain.feed(Number(i + 1))
    processing_chain.feed(None)

    async for r in processing_chain.results:
        print(r)

    # await processing_chain.finish()
    # processing_chain.abort()


asyncio.run(main())
