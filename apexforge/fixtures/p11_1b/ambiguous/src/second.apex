directive Second {
    event second_ready

    cause SecondFlow {
        path primary @ 10 {
            emit second_ready
        }
    }
}
