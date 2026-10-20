import pytest
from faker import Faker

from pyogmios.enums import Method
from pyogmios.models import (
    DigestBlake2bBlockHeader,
    Origin,
    Point,
    PointOrOrigin,
)
from pyogmios.models.request_model import (
    AcquireLedgerState,
    NextBlock,
    ReleaseLedgerState,
    Request,
)


def test_request_from_base_request():
    # Arrange
    fake = Faker()
    request_id = fake.pystr()
    method = fake.enum(Method)
    params = fake.pydict()

    # Act
    result = Request.from_base_request(request_id, method, params)

    # Assert
    assert isinstance(result, Request), "Result is not an instance of Request"
    assert result.id == request_id
    assert result.method == method.value
    assert result.params == params


def test_next_block_from_base():
    # Arrange
    fake = Faker()
    request_id = fake.pystr()

    # Act
    result = NextBlock.from_base(request_id)

    # Assert
    assert isinstance(result, NextBlock), "Result is not an instance of NextBlock"
    assert result.id == request_id
    assert result.method == Method.NEXT_BLOCK.value


def test_release_ledger_state_from_base():
    # Arrange
    fake = Faker()
    request_id = fake.pystr()

    # Act
    result = ReleaseLedgerState.from_base(request_id)

    # Assert
    assert isinstance(result, ReleaseLedgerState), "Result is not an instance of ReleaseLedgerState"
    assert result.id == request_id
    assert result.method == Method.RELEASE_LEDGER_STATE.value


@pytest.mark.parametrize(
    ("test_id", "request_id", "point", "expected_method"),
    [
        (
            "HP-1",
            "req-123",
            Point(
                slot=18446744073709552000,
                id=DigestBlake2bBlockHeader(
                    "c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"
                ),
            ),
            Method.ACQUIRE_LEDGER_STATE,
        ),
        ("HP-2", "req-456", Origin("origin"), Method.ACQUIRE_LEDGER_STATE),
        # Add more test cases with different combinations of request_id and point
    ],
)
def test_acquire_ledger_state_from_base(
    test_id, request_id: int | str, point: PointOrOrigin, expected_method
):
    # Act
    request = AcquireLedgerState.from_base(request_id, point)

    # Assert
    assert isinstance(request, AcquireLedgerState), (
        f"Test {test_id}: Result is not an instance of AcquireLedgerState"
    )
    assert request.method == expected_method.value, (
        f"Test {test_id}: Method is not set to ACQUIRE_LEDGER_STATE"
    )
    assert request.params["point"] == point.model_dump(), (
        f"Test {test_id}: Point is not set correctly"
    )
    assert request.id == request_id, f"Test {test_id}: Request ID is not set correctly"
