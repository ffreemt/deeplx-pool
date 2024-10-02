"""From about_time.duration_time."""

from datetime import timedelta

DURATION_HUMAN_SPEC = (
    (1.0e-6, 1e9, 1e3, "ns"),
    (1.0e-3, 1e6, 1e3, "us"),
    (1.0, 1e3, 1e3, "ms"),
    (60.0, 1e0, 60.0, "s"),
)


def duration_human(value: float) -> str:
    """
    Return a beautiful representation of the duration.

    It dynamically calculates the best unit to use.

    Returns
    -------
        str: the duration representation.

    """
    try:
        value = round(value, 2)
    except Exception:
        return str(value)

    for (
        top,
        mult,
        size,
        unit,
    ) in DURATION_HUMAN_SPEC:
        if value < top:
            result = round(value * mult, ndigits=2)
            if result < size:
                return f"{result}{unit}"
    try:
        txt = str(timedelta(seconds=float(f"{value:.1f}")))
        pos = txt.find(".")
        if pos == -1:
            return txt
        return txt[: pos + 2]
    except OverflowError:
        return "quasi-infinity \n(Python int too large to convert to C int)"
