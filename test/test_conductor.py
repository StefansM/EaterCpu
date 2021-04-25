from typing import List, Optional

import pytest

import eater.part


@pytest.mark.parametrize(
    ["conductor_values", "expected", "raises"],
    [
        # Simple cases with a single conductor.
        ([True], True, False),
        ([False], False, False),
        # Multiple conductors merge together.
        ([True, True, True], True, False),
        ([False, False, False], False, False),
        # Mismatched levels raise exception
        ([False, True], None, True),
        ([True, False], None, True),
    ]
)
def test_pin_combines_values(conductor_values: List[Optional[bool]], expected: Optional[bool], raises: bool):
    """Logic levels on pin propagate to connected conductors."""
    pin = eater.part.Junction()
    voltage_sources = [eater.part.VoltageSource(v) for v in conductor_values]
    for vs in voltage_sources:
        pin.set(vs)

    if raises:
        with pytest.raises(ValueError):
            _ = pin.state

    else:
        assert pin.state == expected


def test_pin_sets_values():
    """Voltage source is reflected in pin state."""
    pin = eater.part.Junction()

    assert pin.state is None

    voltage_source = eater.part.VoltageSource(True)
    pin.set(voltage_source)
    assert pin.state

    voltage_source.value = False
    pin.set(voltage_source)
    assert not pin.state

    pin.clear(voltage_source)
    assert pin.state is None


def test_conductor_sets_values():
    """Values on connected conductors propagate to connected pins."""

    input_wire = eater.part.Junction()
    output_wire = eater.part.Junction([input_wire])

    input_wire.set(eater.part.VoltageSource(True))
    assert output_wire.state

