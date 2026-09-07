import dataclasses
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import uuid4

import pytest

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
from src.domain.models import (
    Account,
    AccountType,
    EntryDirection,
    LedgerEntry,
    Transaction,
)


@pytest.mark.parametrize("scenario", ["empty", "single_leg"])
def test_transaction_raises_error_when_fewer_than_two_entries(
    scenario: Literal["empty", "single_leg"],
):
    account_a = uuid4()
    single_leg = LedgerEntry(
        id=uuid4(),
        account_id=account_a,
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )

    invalid_entries = () if scenario == "empty" else (single_leg,)

    with pytest.raises(InsufficientEntriesError):
        Transaction(
            id=uuid4(),
            idempotency_key=f"txn-degenerate-{scenario}",
            entries=invalid_entries,
            timestamp=datetime.now(timezone.utc),
        )


def test_transaction_raises_unbalanced_error_when_debits_do_not_equal_credits():
    account_a = uuid4()
    account_b = uuid4()

    debit_entry = LedgerEntry(
        id=uuid4(),
        account_id=account_a,
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )

    unbalanced_credit_entry = LedgerEntry(
        id=uuid4(),
        account_id=account_b,
        amount=Decimal("80.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )

    with pytest.raises(UnbalancedTransactionError):
        Transaction(
            id=uuid4(),
            idempotency_key="txn-balance-fail-001",
            entries=(debit_entry, unbalanced_credit_entry),
            timestamp=datetime.now(timezone.utc),
        )


def test_ledger_entry_raises_type_error_when_amount_is_float():
    account_a = uuid4()

    with pytest.raises(InvalidAmountError):
        LedgerEntry(
            id=uuid4(),
            account_id=account_a,
            amount=100.50,
            direction=EntryDirection.DEBIT,
            currency="EUR",
        )


@pytest.mark.parametrize(
    "invalid_amount",
    [
        Decimal("0.00"),
        Decimal("-10.00"),
        Decimal("-0.01"),
    ],
)
def test_ledger_entry_raises_error_when_amount_is_zero_or_negative(
    invalid_amount: Decimal,
):
    account_a = uuid4()

    with pytest.raises(ZeroOrNegativeAmountError):
        LedgerEntry(
            id=uuid4(),
            account_id=account_a,
            amount=invalid_amount,
            direction=EntryDirection.DEBIT,
            currency="EUR",
        )


def test_ledger_entry_raises_frozen_instance_error_on_attribute_mutation():
    account_a = uuid4()
    ledger_entry = LedgerEntry(
        id=uuid4(),
        account_id=account_a,
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        ledger_entry.amount = Decimal("200.00")


def test_transaction_raises_frozen_instance_error_on_attribute_mutation():
    account_a = uuid4()
    account_b = uuid4()

    debit = LedgerEntry(
        id=uuid4(),
        account_id=account_a,
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )
    credit = LedgerEntry(
        id=uuid4(),
        account_id=account_b,
        amount=Decimal("100.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )

    txn = Transaction(
        id=uuid4(),
        idempotency_key="txn-immutable-001",
        entries=(debit, credit),
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        txn.idempotency_key = "tampered-key"


def test_multi_leg_transaction_instantiates_successfully_when_balanced():
    account_a = uuid4()
    account_b = uuid4()
    account_c = uuid4()

    # 1 Debit of €100 offset by 2 Credits of €50
    debit = LedgerEntry(
        id=uuid4(),
        account_id=account_a,
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )
    credit_1 = LedgerEntry(
        id=uuid4(),
        account_id=account_b,
        amount=Decimal("50.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )
    credit_2 = LedgerEntry(
        id=uuid4(),
        account_id=account_c,
        amount=Decimal("50.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )

    txn = Transaction(
        id=uuid4(),
        idempotency_key="txn-split-001",
        entries=(debit, credit_1, credit_2),
        timestamp=datetime.now(timezone.utc),
    )

    assert len(txn.entries) == 3
    assert txn.idempotency_key == "txn-split-001"


def test_transaction_raises_currency_mismatch_error():
    debit = LedgerEntry(
        id=uuid4(),
        account_id=uuid4(),
        amount=Decimal("100.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )
    credit = LedgerEntry(
        id=uuid4(),
        account_id=uuid4(),
        amount=Decimal("100.00"),
        direction=EntryDirection.CREDIT,
        currency="USD",
    )

    with pytest.raises(CurrencyMismatchError):
        Transaction(
            id=uuid4(),
            idempotency_key="txn-fx-001",
            entries=(debit, credit),
            timestamp=datetime.now(timezone.utc),
        )


def test_transaction_raises_self_transfer_error():
    shared_account_id = uuid4()
    debit = LedgerEntry(
        id=uuid4(),
        account_id=shared_account_id,
        amount=Decimal("50.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )
    credit = LedgerEntry(
        id=uuid4(),
        account_id=shared_account_id,
        amount=Decimal("50.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )

    with pytest.raises(SelfTransferError):
        Transaction(
            id=uuid4(),
            idempotency_key="txn-self-001",
            entries=(debit, credit),
            timestamp=datetime.now(timezone.utc),
        )


def test_transaction_raises_naive_timestamp_error():
    debit = LedgerEntry(
        id=uuid4(),
        account_id=uuid4(),
        amount=Decimal("10.00"),
        direction=EntryDirection.DEBIT,
        currency="EUR",
    )
    credit = LedgerEntry(
        id=uuid4(),
        account_id=uuid4(),
        amount=Decimal("10.00"),
        direction=EntryDirection.CREDIT,
        currency="EUR",
    )

    with pytest.raises(NaiveTimestampError):
        Transaction(
            id=uuid4(),
            idempotency_key="txn-naive-tz-001",
            entries=(debit, credit),
            timestamp=datetime.now(),
        )


def test_ledger_entry_raises_invalid_precision_error_on_sub_cent_scale():
    with pytest.raises(InvalidPrecisionError):
        LedgerEntry(
            id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("10.125"),  # 3 decimal places
            direction=EntryDirection.DEBIT,
            currency="EUR",
        )


def test_account_instantiation_valid():
    account = Account(
        id=uuid4(),
        name="Operating Cash",
        type=AccountType.ASSET,
        currency="EUR",
    )
    assert account.is_active is True
    assert account.currency == "EUR"


@pytest.mark.parametrize("invalid_currency", ["eu", "euros", "eur", "123", ""])
def test_account_raises_value_error_on_invalid_currency(
    invalid_currency: Literal["eu", "euros", "eur", "123", ""],
):
    with pytest.raises(ValueError):
        Account(
            id=uuid4(),
            name="Operating Cash",
            type=AccountType.ASSET,
            currency=invalid_currency,
        )


def test_account_raises_value_error_on_empty_name():
    with pytest.raises(ValueError):
        Account(
            id=uuid4(),
            name="   ",
            type=AccountType.ASSET,
            currency="EUR",
        )
