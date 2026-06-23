directive Sentinel {
    state Awareness = 0
    event SentinelObservation

    cause Observation {
        path Investigate @ 80 {
            add Awareness 3
            emit SentinelObservation
        }
    }
}