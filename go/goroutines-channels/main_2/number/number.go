package number

type Number interface {
	Value() int
	Out() string
	AppendToOut(replacement string) Number
	ReplaceOut(replacement string) Number
}

type number struct {
	value int
	out   string
}

func New(num int) Number {
	return &number{num, ""}
}

func (n *number) Value() int {
	return n.value
}

func (n *number) Out() string {
	return n.out
}

func (n *number) AppendToOut(replacement string) Number {
	return &number{
		n.value,
		n.out + replacement,
	}
}

func (n *number) ReplaceOut(replacement string) Number {
	return &number{
		n.value,
		replacement,
	}
}
