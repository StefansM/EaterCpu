from typing import List, Optional

import pytest

import eater.part


@pytest.mark.parametrize(
    ["conductor_values", "expected", "raises"],
    [
        # Simple cases with a single conductor.
        ([True], True, False),
        ([False], False, False),
        ([None], None, False),
        # Multiple conductors merge together.
        ([True, True, True], True, False),
        ([False, False, False], False, False),
        # High impedance line does not affect result
        ([False, False, None], False, False),
        ([True, True, None], True, False),
        # Mismatched levels raise exception
        ([False, True], None, True),
        ([True, False], None, True),
    ]
)
def test_pin_combines_values(conductor_values: List[Optional[bool]], expected: Optional[bool], raises: bool):
    """Logic levels on pin propagate to connected conductors."""
    conductors = [eater.part.Wire(v) for v in conductor_values]
    pin = eater.part.Junction(conductors)

    if raises:
        with pytest.raises(ValueError):
            _ = pin.state

    else:
        assert pin.state == expected


def test_pin_sets_values():
    """Values set on pin propagate to connected conductors."""
    conductors = [eater.part.Wire() for _ in range(3)]
    pin = eater.part.Junction(conductors)

    assert pin.state is None

    pin.state = True
    for conductor in conductors:
        assert conductor.state

    pin.state = False
    for conductor in conductors:
        assert not conductor.state

    pin.state = None
    for conductor in conductors:
        assert conductor.state is None
