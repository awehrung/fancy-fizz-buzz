package main

import (
	"fmt"
	"strconv"
	"sync"
	"time"
)

type number struct {
	value int
	out   string
}

func main() {
	var workerWg sync.WaitGroup
	const channelBuffer = 50

	inputNumbers := make(chan number, channelBuffer)
	after3 := make(chan number, channelBuffer)
	after5 := make(chan number, channelBuffer)
	after7 := make(chan number, channelBuffer)
	final := make(chan number, channelBuffer)

	addTask(&workerWg, func() {
		check(inputNumbers, after3, 3, "Fizz")
	})
	addTask(&workerWg, func() {
		check(after3, after5, 5, "Buzz")
	})
	addTask(&workerWg, func() {
		check(after5, after7, 7, "Bazz")
	})
	addTask(&workerWg, func() {
		fin(after7, final)
	})
	addTask(&workerWg, func() {
		printResults(final)
	})

	var observerWg sync.WaitGroup
	stopObserver := make(chan struct{})

	addTask(&observerWg, func() {
		observeChannels(stopObserver, inputNumbers, after3, after5, after7, final)
	})

	// fill initial channel
	for i := 1; i <= 100; i++ {
		inputNumbers <- wrap(i)
	}

	// wait for worker goroutines to finish
	close(inputNumbers)
	workerWg.Wait()

	// stop observer goroutine
	stopObserver <- struct{}{}
	observerWg.Wait()
}

func addTask(wg *sync.WaitGroup, fn func()) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		fn()
	}()
}

func wrap(i int) number {
	return number{i, ""}
}

func check(in <-chan number, out chan<- number, divisor int, replacement string) {
	const waitTimeMultiplier = 20
	for {
		n, ok := <-in
		if !ok {
			close(out)
			break
		}

		time.Sleep(time.Duration(waitTimeMultiplier*divisor) * time.Millisecond)

		if n.value%divisor == 0 {
			out <- number{
				value: n.value,
				out:   n.out + replacement,
			}
		} else {
			out <- n
		}
	}
}

func fin(in <-chan number, out chan<- number) {
	for {
		n, ok := <-in
		if !ok {
			close(out)
			break
		}

		time.Sleep(10 * time.Millisecond)
		if n.out == "" {
			out <- number{
				value: n.value,
				out:   strconv.Itoa(n.value),
			}
		} else {
			out <- n
		}
	}
}

func printResults(in <-chan number) {
	for n := range in {
		fmt.Println(n.out)
	}
}

func observeChannels(quit chan struct{}, channels ...chan number) {
	for {
		select {
		case <-quit:
			return
		case <-time.After(500 * time.Millisecond):
			fmt.Print("------")
			for _, channel := range channels {
				fmt.Printf(" %d", len(channel))
			}
			fmt.Print("\n")
		}
	}
}
