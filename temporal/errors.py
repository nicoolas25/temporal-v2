class TemporalError(Exception):
    pass


class MalformedHistoryError(TemporalError):
    pass


class MissingValueError(TemporalError):
    pass


class MalformedPerspectiveError(TemporalError):
    pass
