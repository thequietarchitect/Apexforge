"""Passive AFP-P10.9 deterministic random-stream runtime value.

RuntimeRandom is an immutable SplitMix64 stream state. It never reads host
entropy, wall-clock time, process state, or Python's ``random`` module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


UINT64_MODULUS: Final[int] = 1 << 64
UINT64_MASK: Final[int] = UINT64_MODULUS - 1

SPLITMIX64_GAMMA: Final[int] = 0x9E3779B97F4A7C15
_SPLITMIX64_MULTIPLIER_1: Final[int] = 0xBF58476D1CE4E5B9
_SPLITMIX64_MULTIPLIER_2: Final[int] = 0x94D049BB133111EB
_FORK_DOMAIN: Final[int] = 0xD2B74407B1CE6E93


def _require_exact_int(value: object, *, owner: str) -> int:
    if type(value) is not int:
        raise TypeError(
            f"{owner} must be an int; received {type(value).__name__}."
        )
    return value


def normalize_u64(value: int) -> int:
    """Normalize one exact integer into the unsigned 64-bit domain."""

    return _require_exact_int(value, owner="random value") & UINT64_MASK


def mix_u64(value: int) -> int:
    """Apply the fixed SplitMix64 output permutation."""

    mixed = normalize_u64(value)
    mixed = (
        (mixed ^ (mixed >> 30))
        * _SPLITMIX64_MULTIPLIER_1
    ) & UINT64_MASK
    mixed = (
        (mixed ^ (mixed >> 27))
        * _SPLITMIX64_MULTIPLIER_2
    ) & UINT64_MASK
    return (mixed ^ (mixed >> 31)) & UINT64_MASK


@dataclass(frozen=True, order=True)
class RuntimeRandom:
    """One immutable deterministic SplitMix64 stream position."""

    state: int

    def __post_init__(self) -> None:
        value = _require_exact_int(
            self.state,
            owner="RuntimeRandom.state",
        )
        if not 0 <= value <= UINT64_MASK:
            raise ValueError(
                "RuntimeRandom.state must be within the unsigned "
                "64-bit range."
            )

    @classmethod
    def from_seed(cls, seed: int) -> "RuntimeRandom":
        """Normalize any exact integer seed into one stream state."""

        return cls(normalize_u64(seed))

    def advanced(self, steps: int = 1) -> "RuntimeRandom":
        """Return the state after ``steps`` deterministic stream advances."""

        amount = _require_exact_int(
            steps,
            owner="RuntimeRandom.steps",
        )
        if amount < 0:
            raise ValueError("RuntimeRandom.steps cannot be negative.")
        return RuntimeRandom(
            (
                self.state
                + SPLITMIX64_GAMMA * amount
            ) & UINT64_MASK
        )

    def sample_u64(self) -> int:
        """Return the sample at this stream position without mutation."""

        return mix_u64(
            (self.state + SPLITMIX64_GAMMA) & UINT64_MASK
        )

    def fork(self, stream: int) -> "RuntimeRandom":
        """Derive a deterministic independent-looking child stream."""

        stream_id = normalize_u64(stream)
        return RuntimeRandom(
            mix_u64(
                self.state
                ^ stream_id
                ^ _FORK_DOMAIN
            )
        )


__all__ = (
    "RuntimeRandom",
    "SPLITMIX64_GAMMA",
    "UINT64_MASK",
    "UINT64_MODULUS",
    "mix_u64",
    "normalize_u64",
)