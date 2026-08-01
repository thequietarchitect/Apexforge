"""Passive AFP-P10.8 deterministic UTC time runtime value.

A RuntimeTime stores a signed Unix-epoch millisecond count. It has no local
timezone, daylight-saving, locale, wall-clock, or host-clock dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final


MILLISECONDS_PER_SECOND: Final[int] = 1000
MILLISECONDS_PER_MINUTE: Final[int] = 60 * MILLISECONDS_PER_SECOND
MILLISECONDS_PER_HOUR: Final[int] = 60 * MILLISECONDS_PER_MINUTE
MILLISECONDS_PER_DAY: Final[int] = 24 * MILLISECONDS_PER_HOUR

MIN_UNIX_MILLISECONDS: Final[int] = -62135596800000
MAX_UNIX_MILLISECONDS: Final[int] = 253402300799999

_EPOCH = datetime(1970, 1, 1)


def _require_exact_int(value: object, *, owner: str) -> int:
    if type(value) is not int:
        raise TypeError(
            f"{owner} must be an int; received {type(value).__name__}."
        )
    return value


def _unix_milliseconds(value: datetime) -> int:
    delta = value - _EPOCH
    return (
        delta.days * MILLISECONDS_PER_DAY
        + delta.seconds * MILLISECONDS_PER_SECOND
        + delta.microseconds // 1000
    )


@dataclass(frozen=True, order=True)
class RuntimeTime:
    """One immutable UTC instant with millisecond precision."""

    unix_milliseconds: int

    def __post_init__(self) -> None:
        value = _require_exact_int(
            self.unix_milliseconds,
            owner="RuntimeTime.unix_milliseconds",
        )
        if not MIN_UNIX_MILLISECONDS <= value <= MAX_UNIX_MILLISECONDS:
            raise ValueError(
                "RuntimeTime.unix_milliseconds is outside the supported "
                "0001-01-01 through 9999-12-31 UTC range."
            )

    @classmethod
    def from_utc_components(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
        millisecond: int,
    ) -> "RuntimeTime":
        """Construct one validated UTC instant from exact integer fields."""

        fields = {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": second,
            "millisecond": millisecond,
        }
        for name, value in fields.items():
            _require_exact_int(value, owner=f"RuntimeTime.{name}")

        if not 0 <= millisecond <= 999:
            raise ValueError(
                "RuntimeTime.millisecond must be between 0 and 999."
            )

        value = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            millisecond * 1000,
        )
        return cls(_unix_milliseconds(value))

    def to_utc_datetime(self) -> datetime:
        """Return a naive datetime whose fields are explicitly UTC."""

        return _EPOCH + timedelta(milliseconds=self.unix_milliseconds)

    @property
    def year(self) -> int:
        return self.to_utc_datetime().year

    @property
    def month(self) -> int:
        return self.to_utc_datetime().month

    @property
    def day(self) -> int:
        return self.to_utc_datetime().day

    @property
    def hour(self) -> int:
        return self.to_utc_datetime().hour

    @property
    def minute(self) -> int:
        return self.to_utc_datetime().minute

    @property
    def second(self) -> int:
        return self.to_utc_datetime().second

    @property
    def millisecond(self) -> int:
        return self.to_utc_datetime().microsecond // 1000

    def to_iso_utc(self) -> str:
        """Render exactly ``YYYY-MM-DDTHH:MM:SS.mmmZ``."""

        value = self.to_utc_datetime()
        return (
            f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
            f"T{value.hour:02d}:{value.minute:02d}:{value.second:02d}"
            f".{value.microsecond // 1000:03d}Z"
        )


UNIX_EPOCH: Final[RuntimeTime] = RuntimeTime(0)


__all__ = (
    "MAX_UNIX_MILLISECONDS",
    "MILLISECONDS_PER_DAY",
    "MILLISECONDS_PER_HOUR",
    "MILLISECONDS_PER_MINUTE",
    "MILLISECONDS_PER_SECOND",
    "MIN_UNIX_MILLISECONDS",
    "RuntimeTime",
    "UNIX_EPOCH",
)