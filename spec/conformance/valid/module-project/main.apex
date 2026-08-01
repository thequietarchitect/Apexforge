module corpus.main
import corpus.core

directive ModuleMain {
    state count : int = 2

    cause run {
        path primary @ 10 {
            set count = double(count)
        }
    }
}
