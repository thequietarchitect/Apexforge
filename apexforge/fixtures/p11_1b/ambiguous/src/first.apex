directive First {
    event first_ready

    cause FirstFlow {
        path primary @ 10 {
            emit first_ready
        }
    }
}
