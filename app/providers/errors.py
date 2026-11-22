class ProviderError(Exception):
    """Base error for market data providers."""


class ProviderUnavailableError(ProviderError):
    """Network problem, timeout or server error. Safe to retry later."""


class RateLimitedError(ProviderError):
    """The provider rejected the request because of its rate limit."""


class ProviderResponseError(ProviderError):
    """The provider answered with something we do not understand."""