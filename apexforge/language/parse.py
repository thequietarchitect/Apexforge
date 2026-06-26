from language.parser import parse

print(
    parse(
        '''
        directive Sentinel {

            state Awareness = 0

            event SentinelObservation

            cause Observation {

                path Investigate @ 80 {

                    message "Investigation initiated."

                    add Awareness 3

                    emit SentinelObservation
                }
            }
        }
        '''
    )
)