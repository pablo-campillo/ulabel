"""Domain-level exceptions for the ulabel application."""


class DomainError(Exception):
    """Base exception for all domain-specific errors.

    All custom exceptions raised within the domain layer should inherit
    from this class to allow consumers to catch domain errors uniformly.
    """

    pass
