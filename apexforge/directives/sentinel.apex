directive Sentinel {
    state Awareness = 0
    event SentinelObservation

    cause Observation {
        path Investigate @ 80 {
            invoke AEGIS
            invoke Gravitas

            message "Investigation initiated."

            add Awareness 3
            emit SentinelObservation
        }
    }
}