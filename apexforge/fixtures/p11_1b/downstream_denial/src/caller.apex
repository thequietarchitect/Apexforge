directive Caller {
    state caller_count = 0

    cause start {
        path primary @ 10 {
            add caller_count 1
            invoke Callee
        }
    }
}
