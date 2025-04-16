package main

import (
	nb "./number"
	pc "./processing_chain"
	"strconv"
	"time"
)

func main() {
	chain := pc.New(
		checker(3, "Fizz"),
		checker(5, "Buzz"),
		checker(7, "Bazz"),
		finalizer(),
	)

	// start listening on results
	chain.StartPrintingResults()

	// fill initial channel
	for i := 1; i <= 100; i++ {
		chain.Feed(i)
	}
	chain.Done()

	// wait for worker goroutines to finish
	chain.AwaitCompletion()
}

func checker(divisor int, replacement string) func(<-chan nb.Number, chan<- nb.Number) {
	return func(in <-chan nb.Number, out chan<- nb.Number) {
		check(in, out, divisor, replacement)
	}
}

func finalizer() func(<-chan nb.Number, chan<- nb.Number) {
	return func(in <-chan nb.Number, out chan<- nb.Number) {
		fin(in, out)
	}
}

func check(in <-chan nb.Number, out chan<- nb.Number, divisor int, replacement string) {
	const waitTimeMultiplier = 20
	for {
		n, ok := <-in
		if !ok {
			close(out)
			break
		}

		time.Sleep(time.Duration(waitTimeMultiplier*divisor) * time.Millisecond)

		if n.Value()%divisor == 0 {
			out <- n.AppendToOut(replacement)
		} else {
			out <- n
		}
	}
}

func fin(in <-chan nb.Number, out chan<- nb.Number) {
	for {
		n, ok := <-in
		if !ok {
			close(out)
			break
		}

		time.Sleep(10 * time.Millisecond)
		if n.Out() == "" {
			out <- n.ReplaceOut(strconv.Itoa(n.Value()))
		} else {
			out <- n
		}
	}
}
