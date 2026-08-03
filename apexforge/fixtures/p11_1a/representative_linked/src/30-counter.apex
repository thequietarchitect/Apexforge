module perf.counter
import perf.adjust

directive Representative {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = increase(count)
        }
    }
}
