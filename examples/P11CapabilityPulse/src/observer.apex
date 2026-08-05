module continuity.observer

directive Observer {
    state observer_count : int = 1
    event ObservationRecorded

    cause Observe {
        path Stable @ 10 {
            add observer_count 2
            message "Observer continuity confirmed"
            emit ObservationRecorded
        }
    }
}
