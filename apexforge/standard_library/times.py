"""Pure AFP-P10.8 deterministic UTC time utilities."""

from __future__ import annotations

import re

from standard_library.model import BuiltinFunction
from standard_library.result_value import RuntimeResult
from standard_library.time_value import (
    MAX_UNIX_MILLISECONDS,
    MIN_UNIX_MILLISECONDS,
    RuntimeTime,
    UNIX_EPOCH,
)
from type_system.inference import FunctionSignature
from type_system.model import BOOL, INT, RESULT, STRING, TIME


MAX_TIME_TEXT_CODE_POINTS = 64

_ISO_UTC_PATTERN = re.compile(
    r"(?P<year>[0-9]{4})-"
    r"(?P<month>[0-9]{2})-"
    r"(?P<day>[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):"
    r"(?P<minute>[0-9]{2}):"
    r"(?P<second>[0-9]{2})\."
    r"(?P<millisecond>[0-9]{3})Z\Z"
)


def _success(value: RuntimeTime) -> RuntimeResult:
    return RuntimeResult.success(TIME, value)


def _failure(code: str, message: str) -> RuntimeResult:
    return RuntimeResult.failure(
        TIME,
        code=code,
        message=message,
    )


def _time_unix_epoch() -> RuntimeTime:
    return UNIX_EPOCH


def _time_from_unix_milliseconds(value: int) -> RuntimeResult:
    if not MIN_UNIX_MILLISECONDS <= value <= MAX_UNIX_MILLISECONDS:
        return _failure(
            "TIME_OUT_OF_RANGE",
            "Unix milliseconds are outside the supported UTC range.",
        )
    return _success(RuntimeTime(value))


def _time_from_utc(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    millisecond: int,
) -> RuntimeResult:
    try:
        value = RuntimeTime.from_utc_components(
            year,
            month,
            day,
            hour,
            minute,
            second,
            millisecond,
        )
    except (TypeError, ValueError):
        return _failure(
            "INVALID_TIME_COMPONENT",
            "UTC time components are outside the supported ranges.",
        )
    return _success(value)


def _time_parse_iso_utc(value: str) -> RuntimeResult:
    if len(value) > MAX_TIME_TEXT_CODE_POINTS:
        return _failure(
            "TIME_INPUT_TOO_LONG",
            "UTC time text exceeds the 64-code-point limit.",
        )

    match = _ISO_UTC_PATTERN.fullmatch(value)
    if match is None:
        return _failure(
            "INVALID_TIME_FORMAT",
            "UTC time text must use YYYY-MM-DDTHH:MM:SS.mmmZ.",
        )

    components = {
        name: int(raw, 10)
        for name, raw in match.groupdict().items()
    }
    return _time_from_utc(
        components["year"],
        components["month"],
        components["day"],
        components["hour"],
        components["minute"],
        components["second"],
        components["millisecond"],
    )


def _result_time_or(
    value: RuntimeResult,
    fallback: RuntimeTime,
) -> RuntimeTime:
    if value.ok and value.payload_type is TIME:
        return value.value
    return fallback


def _time_to_unix_milliseconds(value: RuntimeTime) -> int:
    return value.unix_milliseconds


def _time_to_iso_utc(value: RuntimeTime) -> str:
    return value.to_iso_utc()


def _time_year(value: RuntimeTime) -> int:
    return value.year


def _time_month(value: RuntimeTime) -> int:
    return value.month


def _time_day(value: RuntimeTime) -> int:
    return value.day


def _time_hour(value: RuntimeTime) -> int:
    return value.hour


def _time_minute(value: RuntimeTime) -> int:
    return value.minute


def _time_second(value: RuntimeTime) -> int:
    return value.second


def _time_millisecond(value: RuntimeTime) -> int:
    return value.millisecond


def _time_add_milliseconds(
    value: RuntimeTime,
    amount: int,
) -> RuntimeResult:
    target = value.unix_milliseconds + amount
    if not MIN_UNIX_MILLISECONDS <= target <= MAX_UNIX_MILLISECONDS:
        return _failure(
            "TIME_OVERFLOW",
            "Adding milliseconds moved outside the supported UTC range.",
        )
    return _success(RuntimeTime(target))


def _time_add_seconds(
    value: RuntimeTime,
    amount: int,
) -> RuntimeResult:
    target = value.unix_milliseconds + amount * 1000
    if not MIN_UNIX_MILLISECONDS <= target <= MAX_UNIX_MILLISECONDS:
        return _failure(
            "TIME_OVERFLOW",
            "Adding seconds moved outside the supported UTC range.",
        )
    return _success(RuntimeTime(target))


def _time_difference_milliseconds(
    left: RuntimeTime,
    right: RuntimeTime,
) -> int:
    return left.unix_milliseconds - right.unix_milliseconds


def _time_compare(
    left: RuntimeTime,
    right: RuntimeTime,
) -> int:
    if left.unix_milliseconds < right.unix_milliseconds:
        return -1
    if left.unix_milliseconds > right.unix_milliseconds:
        return 1
    return 0


def _time_before(
    left: RuntimeTime,
    right: RuntimeTime,
) -> bool:
    return left.unix_milliseconds < right.unix_milliseconds


def _time_after(
    left: RuntimeTime,
    right: RuntimeTime,
) -> bool:
    return left.unix_milliseconds > right.unix_milliseconds


TIME_BUILTINS = (
    BuiltinFunction(
        name="time_unix_epoch",
        signature=FunctionSignature(
            name="time_unix_epoch",
            parameter_types=(),
            return_type=TIME,
        ),
        implementation=_time_unix_epoch,
        documentation="Return the immutable Unix epoch UTC instant.",
    ),
    BuiltinFunction(
        name="time_from_unix_milliseconds",
        signature=FunctionSignature(
            name="time_from_unix_milliseconds",
            parameter_types=(INT,),
            return_type=RESULT,
        ),
        implementation=_time_from_unix_milliseconds,
        documentation="Safely construct UTC time from Unix milliseconds.",
    ),
    BuiltinFunction(
        name="time_from_utc",
        signature=FunctionSignature(
            name="time_from_utc",
            parameter_types=(INT, INT, INT, INT, INT, INT, INT),
            return_type=RESULT,
        ),
        implementation=_time_from_utc,
        documentation="Safely construct UTC time from calendar fields.",
    ),
    BuiltinFunction(
        name="time_parse_iso_utc",
        signature=FunctionSignature(
            name="time_parse_iso_utc",
            parameter_types=(STRING,),
            return_type=RESULT,
        ),
        implementation=_time_parse_iso_utc,
        documentation="Parse strict YYYY-MM-DDTHH:MM:SS.mmmZ text.",
    ),
    BuiltinFunction(
        name="result_time_or",
        signature=FunctionSignature(
            name="result_time_or",
            parameter_types=(RESULT, TIME),
            return_type=TIME,
        ),
        implementation=_result_time_or,
        documentation="Extract a successful time or return the fallback.",
    ),
    BuiltinFunction(
        name="time_to_unix_milliseconds",
        signature=FunctionSignature(
            name="time_to_unix_milliseconds",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_to_unix_milliseconds,
        documentation="Return signed Unix milliseconds.",
    ),
    BuiltinFunction(
        name="time_to_iso_utc",
        signature=FunctionSignature(
            name="time_to_iso_utc",
            parameter_types=(TIME,),
            return_type=STRING,
        ),
        implementation=_time_to_iso_utc,
        documentation="Render strict millisecond-precision UTC text.",
    ),
    BuiltinFunction(
        name="time_year",
        signature=FunctionSignature(
            name="time_year",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_year,
        documentation="Return the four-digit UTC year.",
    ),
    BuiltinFunction(
        name="time_month",
        signature=FunctionSignature(
            name="time_month",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_month,
        documentation="Return the UTC month from 1 through 12.",
    ),
    BuiltinFunction(
        name="time_day",
        signature=FunctionSignature(
            name="time_day",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_day,
        documentation="Return the UTC day of month.",
    ),
    BuiltinFunction(
        name="time_hour",
        signature=FunctionSignature(
            name="time_hour",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_hour,
        documentation="Return the UTC hour from 0 through 23.",
    ),
    BuiltinFunction(
        name="time_minute",
        signature=FunctionSignature(
            name="time_minute",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_minute,
        documentation="Return the UTC minute from 0 through 59.",
    ),
    BuiltinFunction(
        name="time_second",
        signature=FunctionSignature(
            name="time_second",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_second,
        documentation="Return the UTC second from 0 through 59.",
    ),
    BuiltinFunction(
        name="time_millisecond",
        signature=FunctionSignature(
            name="time_millisecond",
            parameter_types=(TIME,),
            return_type=INT,
        ),
        implementation=_time_millisecond,
        documentation="Return the UTC millisecond from 0 through 999.",
    ),
    BuiltinFunction(
        name="time_add_milliseconds",
        signature=FunctionSignature(
            name="time_add_milliseconds",
            parameter_types=(TIME, INT),
            return_type=RESULT,
        ),
        implementation=_time_add_milliseconds,
        documentation="Safely add signed milliseconds.",
    ),
    BuiltinFunction(
        name="time_add_seconds",
        signature=FunctionSignature(
            name="time_add_seconds",
            parameter_types=(TIME, INT),
            return_type=RESULT,
        ),
        implementation=_time_add_seconds,
        documentation="Safely add signed whole seconds.",
    ),
    BuiltinFunction(
        name="time_difference_milliseconds",
        signature=FunctionSignature(
            name="time_difference_milliseconds",
            parameter_types=(TIME, TIME),
            return_type=INT,
        ),
        implementation=_time_difference_milliseconds,
        documentation="Return left minus right in milliseconds.",
    ),
    BuiltinFunction(
        name="time_compare",
        signature=FunctionSignature(
            name="time_compare",
            parameter_types=(TIME, TIME),
            return_type=INT,
        ),
        implementation=_time_compare,
        documentation="Return -1, 0, or 1 for UTC instant ordering.",
    ),
    BuiltinFunction(
        name="time_before",
        signature=FunctionSignature(
            name="time_before",
            parameter_types=(TIME, TIME),
            return_type=BOOL,
        ),
        implementation=_time_before,
        documentation="Return whether left is earlier than right.",
    ),
    BuiltinFunction(
        name="time_after",
        signature=FunctionSignature(
            name="time_after",
            parameter_types=(TIME, TIME),
            return_type=BOOL,
        ),
        implementation=_time_after,
        documentation="Return whether left is later than right.",
    ),
)


__all__ = (
    "MAX_TIME_TEXT_CODE_POINTS",
    "TIME_BUILTINS",
)