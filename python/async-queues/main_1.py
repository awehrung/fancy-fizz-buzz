import asyncio
import random
from typing import Dict


class Number:
    def __init__(self, value: int):
        self.value: int = value
        self.out_name: str = ""


async def checker(
    divisor: int,
    replacement: str,
    in_queue: asyncio.Queue,
    out_queue: asyncio.Queue,
):
    running = True
    while running:
        item: Number = await in_queue.get()
        await asyncio.sleep(abs(random.gauss(0.00, 0.2)))
        if item is None:
            running = False
        elif item.value % divisor == 0:
            item.out_name += replacement
        out_queue.put_nowait(item)
        in_queue.task_done()


async def printer(in_queue: asyncio.Queue):
    running = True
    while running:
        item: Number = await in_queue.get()
        await asyncio.sleep(abs(random.gauss(0.00, 0.2)))
        if item is None:
            running = False
        else:
            if item.out_name == "":
                item.out_name = str(item.value)
            print(item.out_name)


async def queue_observer(queues: Dict[str, asyncio.Queue]):
    queue_sizes = dict()
    while True:
        for queue_name, queue in queues.items():
            queue_sizes[queue_name] = queue.qsize()
        print(
            "------ "
            + ", ".join(
                [
                    f"{queue_name}: {queue_size}"
                    for queue_name, queue_size in queue_sizes.items()
                ]
            )
        )
        await asyncio.sleep(1)


async def main():
    limit = 100

    check_3_queue = asyncio.Queue()
    check_5_queue = asyncio.Queue()
    check_7_queue = asyncio.Queue()
    print_queue = asyncio.Queue()

    tasks = list()
    tasks.append(asyncio.create_task(checker(3, "Fizz", check_3_queue, check_5_queue)))
    tasks.append(asyncio.create_task(checker(5, "Buzz", check_5_queue, check_7_queue)))
    tasks.append(asyncio.create_task(checker(7, "Bazz", check_7_queue, print_queue)))
    tasks.append(asyncio.create_task(printer(print_queue)))

    observer = asyncio.create_task(
        queue_observer(
            {
                "Q3": check_3_queue,
                "Q5": check_5_queue,
                "Q7": check_7_queue,
                "QP": print_queue,
            }
        )
    )

    for i in range(1, limit + 1):
        check_3_queue.put_nowait(Number(i))
    check_3_queue.put_nowait(None)

    await asyncio.gather(*tasks)
    observer.cancel()


asyncio.run(main())
