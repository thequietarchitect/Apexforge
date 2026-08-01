directive Main {
    event ready

    cause start {
        path primary @ 10 {
            message "ready"
            emit ready
        }
    }
}
