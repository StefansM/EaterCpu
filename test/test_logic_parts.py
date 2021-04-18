from typing import List, Optional

import pytest

import eater.part


@pytest.fixture(params=[eater.part.QuadNorGate(), eater.part.QuadNandGate()])
def logic_gate(request) -> eater.part.LogicPart:
    return request.param


def init_power(part: eater.part.LogicPart):
    part.pins[part.VCC].conductors.append(eater.part.Wire(True))
    part.pins[part.GND].conductors.append(eater.part.Wire(False))


@pytest.mark.parametrize(
    ["vcc", "gnd"],
    [
        (False, False),
        (False, True),
        (True, True),
    ]
)
def test_all_parts_power_required(vcc: bool, gnd: bool, logic_gate: eater.part.LogicPart):
    """Exception raised when VCC or GND are incorrect."""
    logic_gate.pins[logic_gate.VCC].state = vcc
    logic_gate.pins[logic_gate.GND].state = gnd

    with pytest.raises(AssertionError):
        logic_gate.evaluate()


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, True),
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.QuadNandGate.gates,
)
def test_quad_nand_logic(
        a: bool, b: bool, y: bool,
        inputs: List[int], output: int):
    """All gates of output match truth table."""
    gate = eater.part.QuadNandGate()
    init_power(gate)

    probe_a = eater.part.Wire(a)
    probe_b = eater.part.Wire(b)
    probe_y = eater.part.Wire()

    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[inputs[1]].conductors.append(probe_b)
    gate.pins[output].conductors.append(probe_y)

    gate.evaluate()
    assert probe_y.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, True),
        (False, True, False),
        (True, False, False),
        (True, True, False),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.QuadNorGate.gates,
)
def test_quad_nor_logic(
        a: bool, b: bool, y: bool,
        inputs: List[int], output: int):
    """All gates of output match truth table."""
    gate = eater.part.QuadNorGate()
    init_power(gate)

    probe_a = eater.part.Wire(a)
    probe_b = eater.part.Wire(b)
    probe_y = eater.part.Wire()

    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[inputs[1]].conductors.append(probe_b)
    gate.pins[output].conductors.append(probe_y)

    gate.evaluate()
    assert probe_y.state == y


@pytest.mark.parametrize(
    ["a", "y"],
    [
        (False, True),
        (True, False),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.HexNotGate.gates,
)
def test_hex_not_logic(
        a: bool, y: bool,
        inputs: List[int], output: int):
    """All gates of output match truth table."""
    gate = eater.part.HexNotGate()
    init_power(gate)

    probe_a = eater.part.Wire(a)
    probe_y = eater.part.Wire()

    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[output].conductors.append(probe_y)

    gate.evaluate()
    assert probe_y.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.QuadAndGate.gates,
)
def test_quad_and_logic(
        a: bool, b: bool, y: bool,
        inputs: List[int], output: int):
    """All gates of output match truth table."""
    gate = eater.part.QuadAndGate()
    init_power(gate)

    probe_a = eater.part.Wire(a)
    probe_b = eater.part.Wire(b)
    probe_y = eater.part.Wire()

    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[inputs[1]].conductors.append(probe_b)
    gate.pins[output].conductors.append(probe_y)

    gate.evaluate()
    assert probe_y.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, False),
        (False, True, True),
        (True, False, True),
        (True, True, True),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.QuadOrGate.gates,
)
def test_quad_or_logic(
        a: bool, b: bool, y: bool,
        inputs: List[int], output: int):
    """All gates of output match truth table."""
    gate = eater.part.QuadOrGate()
    init_power(gate)

    probe_a = eater.part.Wire(a)
    probe_b = eater.part.Wire(b)
    probe_y = eater.part.Wire()

    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[inputs[1]].conductors.append(probe_b)
    gate.pins[output].conductors.append(probe_y)

    gate.evaluate()
    assert probe_y.state == y


@pytest.mark.parametrize(
    ["a", "b", "enabled_inverted", "direction"],
    [
        # Bus A → B (Enabled)
        (True, True, False, True),
        (False, False, False, True),
        # Bus A ← B (Enabled)
        (True, True, False, False),
        (False, False, False, False),
        # Bus A → B (Disabled)
        (True, None, True, True),
        (False, None, True, True),
        # Bus A ← B (Disabled)
        (None, True, True, False),
        (None, False, True, False),
    ]
)
@pytest.mark.parametrize(
    ["inputs", "output"],
    eater.part.OctalBusTransceiver.gates,
)
def test_octal_transceiver(
        a: Optional[bool], b: Optional[bool], enabled_inverted: bool, direction: bool,
        inputs: List[int], output: int):
    """Octal transceiver transfers bits in both directions unless disabled."""
    gate = eater.part.OctalBusTransceiver()
    init_power(gate)

    probe_not_enabled = eater.part.Wire(enabled_inverted)
    probe_direction = eater.part.Wire(direction)

    gate.pins[gate.ENABLED_INVERTED].conductors.append(probe_not_enabled)
    gate.pins[gate.DIRECTION].conductors.append(probe_direction)

    gate.pins[gate.ENABLED_INVERTED].state = enabled_inverted
    gate.pins[gate.DIRECTION].state = direction

    probe_a = eater.part.Wire()
    probe_b = eater.part.Wire()
    gate.pins[inputs[0]].conductors.append(probe_a)
    gate.pins[output].conductors.append(probe_b)

    if direction:
        # A -> B
        gate.pins[inputs[0]].state = a
        gate.evaluate()
        assert gate.pins[output].state == b
    else:
        # B -> A
        gate.pins[output].state = b
        gate.evaluate()
        assert gate.pins[inputs[0]].state == a


@pytest.fixture()
def four_bit_register(vcc_rail: eater.part.Wire, gnd_rail: eater.part.Wire) -> eater.part.FourBitDRegister:
    register = eater.part.FourBitDRegister()

    for pin in register.pins.values():
        pin.conductors.append(eater.part.Wire())

    register.pins[register.VCC].state = True
    register.pins[register.GND].state = False

    return register

@pytest.fixture()
def latched_four_bit_register(four_bit_register: eater.part.FourBitDRegister) -> eater.part.FourBitDRegister:
    """Four-bit register with high bits latched into it."""

    # High data lines.
    for d, _ in four_bit_register.lines:
        four_bit_register.pins[d].state = True

    four_bit_register.pins[four_bit_register.CLK].state = False
    four_bit_register.evaluate()
    # Actually latch the data in
    four_bit_register.pins[four_bit_register.CLK].state = True
    four_bit_register.evaluate()
    # Bring clock low again so tests only need to bring it high.
    four_bit_register.pins[four_bit_register.CLK].state = False
    four_bit_register.evaluate()

    return four_bit_register


@pytest.mark.parametrize("clk", [True, False])
@pytest.mark.parametrize("g1", [True, False])
@pytest.mark.parametrize("g2", [True, False])
def test_clear_register(four_bit_register: eater.part.FourBitDRegister, clk: bool, g1: bool, g2: bool):
    """Outputs are always low when CLR is set."""
    four_bit_register.pins[four_bit_register.CLR].state = True
    four_bit_register.pins[four_bit_register.CLK].state = clk
    four_bit_register.pins[four_bit_register.G1].state = g1
    four_bit_register.pins[four_bit_register.G2].state = g2

    for d, _ in four_bit_register.lines:
        four_bit_register.pins[d].state = True

    four_bit_register.evaluate()

    for _, q in four_bit_register.lines:
        assert not four_bit_register.pins[q].state


@pytest.mark.parametrize("data", [True, False])
def test_latch_in_data(four_bit_register: eater.part.FourBitDRegister, data: bool):
    """Data can be read out after being latched in."""
    four_bit_register.pins[four_bit_register.CLR].state = False
    four_bit_register.pins[four_bit_register.G1].state = False
    four_bit_register.pins[four_bit_register.G2].state = False

    four_bit_register.pins[four_bit_register.CLK].state = False

    # Set data lines.
    for d, _ in four_bit_register.lines:
        four_bit_register.pins[d].state = data

    # Does not affect anything because clock hasn't changed
    four_bit_register.evaluate()
    for _, q in four_bit_register.lines:
        assert four_bit_register.pins[q].state is None

    # Now trigger the clock and outputs should be set.
    four_bit_register.pins[four_bit_register.CLK].state = True
    four_bit_register.evaluate()
    for _, q in four_bit_register.lines:
        assert four_bit_register.pins[q].state == data


@pytest.mark.parametrize("g", [(True, False), (False, True), (True, True)])
def test_latch_unaffected_when_either_data_enable_pins_high(
        latched_four_bit_register: eater.part.FourBitDRegister,
        g: bool):
    """Output is unaffected when either data enable pin is high."""

    # Low data lines.
    for d, _ in latched_four_bit_register.lines:
        latched_four_bit_register.pins[d].state = False

    latched_four_bit_register.pins[latched_four_bit_register.CLK].state = True
    latched_four_bit_register.evaluate()

    for _, q in latched_four_bit_register.lines:
        assert latched_four_bit_register.pins[q]
