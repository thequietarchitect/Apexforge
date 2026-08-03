directive Main {
    event main_ready

    cause MainFlow {
        path primary @ 10 {
            emit main_ready
        }
    }
}
