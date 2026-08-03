directive Minimal {
    state count = 0

    cause start {
        path primary @ 10 {
            add count 1
        }
    }
}
