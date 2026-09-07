from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from src.domain.exceptions import (
    CurrencyMismatchError,
    InsufficientEntriesError,
    InvalidAmountError,
    InvalidPrecisionError,
    NaiveTimestampError,
    SelfTransferError,
    UnbalancedTransactionError,
    ZeroOrNegativeAmountError,
)


class EntryDirection(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


@dataclass(frozen=True)
class Account:
    id: UUID
    name: str
    type: AccountType
    currency: str
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Account name cannot be empty.")
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(
                f"Currency code must be a 3-letter ISO code; got '{self.currency}'."
            )


@dataclass(frozen=True)
class LedgerEntry:
    id: UUID
    account_id: UUID
    amount: Decimal
    direction: EntryDirection
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise InvalidAmountError(self.amount)

        if self.amount <= Decimal("0"):
            raise ZeroOrNegativeAmountError(self.amount)

        if self.amount.as_tuple().exponent < -2:
            raise InvalidPrecisionError(self.amount, max_digits=2)

        if not isinstance(self.direction, EntryDirection):
            raise TypeError(
                f"direction must be an instance of EntryDirection, got {type(self.direction).__name__}."
            )


@dataclass(frozen=True)
class Transaction:
    id: UUID
    idempotency_key: str
    entries: tuple[LedgerEntry, ...]
    timestamp: datetime

    def __post_init__(self) -> None:

        if len(self.entries) < 2:
            raise InsufficientEntriesError(len(self.entries))

        credit_count = 0
        debit_count = 0
        credit_sum = Decimal("0")
        debit_sum = Decimal("0")
        currency = self.entries[0].currency

        for entry in self.entries:
            if entry.currency != currency:
                raise CurrencyMismatchError(expected=currency, actual=entry.currency)

            if entry.direction == EntryDirection.DEBIT:
                debit_count += 1
                debit_sum += entry.amount
            elif entry.direction == EntryDirection.CREDIT:
                credit_count += 1
                credit_sum += entry.amount

        if debit_count == 0 or credit_count == 0 or debit_sum != credit_sum:
            raise UnbalancedTransactionError(debit_sum, credit_sum)

        if (
            len(self.entries) == 2
            and self.entries[0].account_id == self.entries[1].account_id
        ):
            raise SelfTransferError(self.entries[0].account_id)

        if not (
            self.timestamp.tzinfo is not None and self.timestamp.tzinfo == timezone.utc
        ):
            raise NaiveTimestampError()
