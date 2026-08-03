directive Callee {
    state count = 0

    cause update {
        path primary @ 10 {
            add count 1
        }
    }
}
