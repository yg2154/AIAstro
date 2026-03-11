class MyNakshError(Exception):
    """Base exception."""


class SessionNotFoundError(MyNakshError):
    pass


class ZodiacCalculationError(MyNakshError):
    pass


class RAGIndexError(MyNakshError):
    pass


class LLMError(MyNakshError):
    pass
