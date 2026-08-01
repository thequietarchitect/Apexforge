directive Main {
    state count : int = 0
    event ready
    authority Root
    requires run

    cause start {
        path primary @ 10 {
            message "ready"
            emit ready
        }
    }
}
