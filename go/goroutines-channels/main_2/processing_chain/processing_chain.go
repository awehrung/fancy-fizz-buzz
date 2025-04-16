package processing_chain

import (
	nb "../number"
	"fmt"
	"sync"
	"time"
)

type ProcessingChain interface {
	Feed(num int)
	Done()
	AwaitCompletion()
	StartPrintingResults()
}

type processingChain struct {
	processors   []func(<-chan nb.Number, chan<- nb.Number)
	inChannel    chan<- nb.Number
	outChannel   <-chan nb.Number
	workersWg    *sync.WaitGroup
	observerWg   *sync.WaitGroup
	stopObserver chan<- struct{}
}

func New(processors ...func(<-chan nb.Number, chan<- nb.Number)) ProcessingChain {
	const channelBuffer = 50
	var workersWg sync.WaitGroup
	var observerWg sync.WaitGroup

	var channels = make([]chan nb.Number, len(processors)+1)
	for i := 0; i < len(channels); i++ {
		channels[i] = make(chan nb.Number, channelBuffer)
	}

	for i, processor := range processors {
		addTask(&workersWg, func() {
			processor(channels[i], channels[i+1])
		})
	}

	stopObserver := make(chan struct{})

	addTask(&observerWg, func() {
		observeChannels(stopObserver, channels)
	})

	return &processingChain{
		inChannel:    channels[0],
		outChannel:   channels[len(channels)-1],
		processors:   processors,
		stopObserver: stopObserver,
		workersWg:    &workersWg,
		observerWg:   &observerWg,
	}
}

func (pc *processingChain) Feed(num int) {
	pc.inChannel <- nb.New(num)
}

func (pc *processingChain) Done() {
	close(pc.inChannel)
}

func (pc *processingChain) AwaitCompletion() {
	pc.workersWg.Wait()

	// stop observer goroutine
	pc.stopObserver <- struct{}{}
	pc.observerWg.Wait()
}

func (pc *processingChain) StartPrintingResults() {
	addTask(pc.workersWg, func() {
		for n := range pc.outChannel {
			fmt.Println(n.Out())
		}
	})
}

func addTask(wg *sync.WaitGroup, fn func()) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		fn()
	}()
}

func observeChannels(quit chan struct{}, channels []chan nb.Number) {
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
