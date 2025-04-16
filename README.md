# Fancy FizzBuzz

Fancy and over-engineered implementations of the classic FizzBuzz problem

## Kotlin: Coroutines

### Preparation

Build the project, in the `kotlin/coroutines` directory:

```shell
./gradlew build
```

### Content

Implementations based on Kotlin's `couroutines` model with added random delays to make the process visible.

Every coroutine is responsible for the processing of one number.

## Python : Async Queues

### Preparation

Required Python version: >=3.10

Activate `venv` in the `python/async-queues` directory then install dependencies:

```shell
pip install -r requirements.txt
```

### Content

Implementations based on `asyncio.Queue` with added random delays to make the process visible.

Each number is passed from one queue to the next, each queue is responsible for checking one divisor.

Also included: an observer task that regularly prints the size of the queues.

## Go: Goroutines

### Preparation

Make sure Go is installed

### Content

Implementations using Go's goroutines and channels with added delays to make the process visible.

Each number is passed from one channel to the next, each channel is responsible for checking one divisor.

Also included: an observer goroutine that regularly prints the size of the channels.

## Other

TODO...
