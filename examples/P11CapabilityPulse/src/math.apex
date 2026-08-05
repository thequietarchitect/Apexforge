module continuity.math

function strengthen(value : int) : int {
    let doubled = value * 2

    when doubled >= 6 {
        return doubled + 1
    }
    otherwise {
        return doubled
    }
}
