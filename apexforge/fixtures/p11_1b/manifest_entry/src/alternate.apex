directive Alternate {
    event alternate_ready

    cause AlternateFlow {
        path primary @ 10 {
            emit alternate_ready
        }
    }
}
