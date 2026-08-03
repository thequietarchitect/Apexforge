directive Solo {
    event solo_ready

    cause start {
        path primary @ 10 {
            emit solo_ready
        }
    }
}
