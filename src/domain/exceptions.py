from decimal import Decimal
from typing import Any
from uuid import UUID


class LedgerDomainError(Exception):
    """Base exception for all domain-related failures."""

    def __init__(
        self, message: str = "A ledger domain invariant was violated."
    ) -> None:
        super().__init__(message)


class InsufficientEntriesError(LedgerDomainError):
    """Raised when a transaction contains fewer than two entries."""

    def __init__(self, count: int) -> None:
        super().__init__(
            f"A transaction must contain at least 2 entries; received {count}."
        )


class UnbalancedTransactionError(LedgerDomainError):
    """Raised when total debits do not equal total credits."""

    def __init__(self, debit_sum: Decimal, credit_sum: Decimal) -> None:
        imbalance = debit_sum - credit_sum
        super().__init__(
            f"Unbalanced transaction: total debits ({debit_sum}) != total credits ({credit_sum}). "
            f"Net imbalance: {imbalance}."
        )


class ZeroOrNegativeAmountError(LedgerDomainError):
    """Raised when an entry amount is zero or negative."""

    def __init__(self, amount: Decimal) -> None:
        super().__init__(
            f"Amount must be strictly positive (> Decimal('0')); received {amount}."
        )


class InvalidAmountError(LedgerDomainError):
    """Raised when an amount is not a Decimal instance."""

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"Amount must be an instance of Decimal to prevent precision loss; "
            f"received type {type(value).__name__}."
        )


class InvalidPrecisionError(LedgerDomainError):
    """Raised when an entry amount exceeds the permitted decimal scale."""

    def __init__(self, amount: Decimal, max_digits: int = 2) -> None:
        super().__init__(
            f"Amount {amount} exceeds maximum allowed decimal places ({max_digits})."
        )


class CurrencyMismatchError(LedgerDomainError):
    """Raised when entries within a transaction do not share the same currency."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            f"Currency mismatch: transaction currency is '{expected}', but entry has '{actual}'."
        )


class SelfTransferError(LedgerDomainError):
    """Raised when an entry attempts to balance against the same account."""

    def __init__(self, account_id: UUID) -> None:
        super().__init__(
            f"Self-transfer prohibited: account {account_id} cannot transfer to itself."
        )


class NaiveTimestampError(LedgerDomainError):
    """Raised when a transaction timestamp lacks explicit UTC timezone information."""

    def __init__(self) -> None:
        super().__init__(
            "Transaction timestamp must be timezone-aware and set to UTC (timezone.utc)."
        )
