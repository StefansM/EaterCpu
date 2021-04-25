import dataclasses
from typing import List, Optional, Tuple

import pytest

import eater.part


@pytest.fixture(params=eater.part.PoweredPart.__subclasses__())
def logic_gate(request) -> eater.part.PoweredPart:
    return request.param()


def init_power(part: eater.part.PoweredPart):
    part.VCC.set(eater.part.VoltageSource(True))
    part.GND.set(eater.part.VoltageSource(False))


@pytest.mark.parametrize(
    ["vcc", "gnd"],
    [
        (False, False),
        (False, True),
        (True, True),
    ]
)
def test_all_parts_power_required(vcc: bool, gnd: bool, logic_gate: eater.part.PoweredPart):
    """Exception raised when VCC or GND are incorrect."""
    logic_gate.VCC.set(eater.part.VoltageSource(vcc))
    logic_gate.GND.set(eater.part.VoltageSource(gnd))

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
def test_quad_nand_logic(a: bool, b: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.QuadNandGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))
        gate.inputs[1].set(eater.part.VoltageSource(b))

        chip.evaluate()
        assert gate.output.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, True),
        (False, True, False),
        (True, False, False),
        (True, True, False),
    ]
)
def test_quad_nor_logic(a: bool, b: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.QuadNorGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))
        gate.inputs[1].set(eater.part.VoltageSource(b))

        gate.evaluate()
        assert gate.output.state == y


@pytest.mark.parametrize(
    ["a", "y"],
    [
        (False, True),
        (True, False),
    ]
)
def test_hex_not_logic(a: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.HexNotGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))

        gate.evaluate()
        assert gate.output.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ]
)
def test_quad_and_logic(a: bool, b: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.QuadAndGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))
        gate.inputs[1].set(eater.part.VoltageSource(b))

        gate.evaluate()
        assert gate.output.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, False),
        (False, True, True),
        (True, False, True),
        (True, True, True),
    ]
)
def test_quad_or_logic(a: bool, b: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.QuadOrGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))
        gate.inputs[1].set(eater.part.VoltageSource(b))

        gate.evaluate()
        assert gate.output.state == y


@pytest.mark.parametrize(
    ["a", "b", "y"],
    [
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, False),
    ]
)
def test_quad_xor_logic(a: bool, b: bool, y: bool):
    """All gates of output match truth table."""
    chip = eater.part.QuadXorGate()
    init_power(chip)

    for gate in chip.gates:
        gate.inputs[0].set(eater.part.VoltageSource(a))
        gate.inputs[1].set(eater.part.VoltageSource(b))

        gate.evaluate()
        assert gate.output.state == y


@pytest.fixture()
def octal_bus_chip() -> Tuple[eater.part.OctalBusTransceiver, eater.part.Bus, eater.part.Bus]:
    chip = eater.part.OctalBusTransceiver()
    init_power(chip)

    bus_a = eater.part.Bus([eater.part.Junction() for i in range(8)])
    bus_b = eater.part.Bus([eater.part.Junction() for i in range(8)])

    chip.set_bus_a(bus_a)
    chip.set_bus_b(bus_b)
    return chip, bus_a, bus_b


@pytest.mark.parametrize("direction", [True, False])
def test_bus_transfer_disabled_when_enabled_pin_high(
        octal_bus_chip: Tuple[eater.part.OctalBusTransceiver, eater.part.Bus, eater.part.Bus],
        direction: bool):
    """Nothing is transferred in either direction when E\u0305 is high."""
    chip, bus_a, bus_b = octal_bus_chip
    chip.ENABLED.set(eater.part.VoltageSource(True))
    chip.DIRECTION.set(eater.part.VoltageSource(direction))

    chip.evaluate()
    assert bus_a.value == [None] * 8
    assert bus_b.value == [None] * 8

    bus_a.pull_to([True] * 8)
    chip.evaluate()
    assert bus_b.value == [None] * 8
    bus_a.pull_to([None] * 8)

    bus_b.pull_to([True] * 8)
    chip.evaluate()
    assert bus_a.value == [None] * 8


@pytest.mark.parametrize("direction", [True, False])
def test_bus_transfer_busses(
        octal_bus_chip: Tuple[eater.part.OctalBusTransceiver, eater.part.Bus, eater.part.Bus],
        direction: bool):
    """Bits are transferred from A → B when direction is high and B → A when low.."""
    chip, bus_a, bus_b = octal_bus_chip
    chip.ENABLED.set(eater.part.VoltageSource(False))
    chip.DIRECTION.set(eater.part.VoltageSource(direction))

    if direction:
        input_bus = bus_a
        output_bus = bus_b
    else:
        input_bus = bus_b
        output_bus = bus_a

    input_bus.pull_to([True] * 8)
    chip.evaluate()
    assert output_bus.value == [True] * 8


@pytest.fixture()
def four_bit_register() -> eater.part.FourBitDRegister:
    register = eater.part.FourBitDRegister()
    init_power(register)
    return register


@dataclasses.dataclass
class FourBitRegisterTestHarness:
    chip: eater.part.FourBitDRegister

    clock: eater.part.VoltageSource
    nm: List[eater.part.VoltageSource]
    g: List[eater.part.VoltageSource]
    clr: eater.part.VoltageSource

    data: List[eater.part.VoltageSource]


@pytest.fixture()
def latched_four_bit_register(four_bit_register: eater.part.FourBitDRegister) -> FourBitRegisterTestHarness:
    """Four-bit register with high bits latched into it."""

    # High data lines.
    data_vs = [eater.part.VoltageSource(True) for _ in range(4)]
    four_bit_register.D1.set(data_vs[0])
    four_bit_register.D2.set(data_vs[1])
    four_bit_register.D3.set(data_vs[2])
    four_bit_register.D4.set(data_vs[3])

    # Enable data input
    g_vs = [eater.part.VoltageSource(False) for _ in range(2)]
    four_bit_register.G1.set(g_vs[0])
    four_bit_register.G2.set(g_vs[1])

    # Enable gate output by setting N and M low.
    nm_vs = [eater.part.VoltageSource(False) for _ in range(2)]
    four_bit_register.N.set(nm_vs[0])
    four_bit_register.M.set(nm_vs[1])

    # Start with low clock line and latch in data
    clock_line = eater.part.VoltageSource(False)
    four_bit_register.CLK.set(clock_line)
    four_bit_register.evaluate()

    # Set clear low for normal operation
    clear_line = eater.part.VoltageSource(False)
    four_bit_register.CLR.set(clear_line)

    # Actually latch the data in
    clock_line.value = True
    four_bit_register.evaluate()

    # Bring clock low again so tests only need to bring it high.
    clock_line.value = False
    four_bit_register.evaluate()

    return FourBitRegisterTestHarness(
        chip=four_bit_register,
        clock=clock_line,
        nm=nm_vs,
        g=g_vs,
        clr=clear_line,
        data=data_vs,
    )


@pytest.mark.parametrize("clk", [True, False])
@pytest.mark.parametrize("g1", [True, False])
@pytest.mark.parametrize("g2", [True, False])
def test_clear_register(latched_four_bit_register: FourBitRegisterTestHarness, clk: bool, g1: bool, g2: bool):
    """Outputs are always low when CLR is set."""
    four_bit_register = latched_four_bit_register.chip
    latched_four_bit_register.clr.value = True

    four_bit_register.evaluate()

    assert not four_bit_register.Q1.state
    assert not four_bit_register.Q2.state
    assert not four_bit_register.Q3.state
    assert not four_bit_register.Q4.state


def test_latch_in_data(latched_four_bit_register: FourBitRegisterTestHarness):
    """Data can be read out after being latched in."""
    four_bit_register = latched_four_bit_register.chip

    assert four_bit_register.Q1.state
    assert four_bit_register.Q2.state
    assert four_bit_register.Q3.state
    assert four_bit_register.Q4.state


@pytest.mark.parametrize("g1,g2", [(True, False), (False, True), (True, True)])
def test_latch_unaffected_when_either_data_enable_pins_high(
        latched_four_bit_register: FourBitRegisterTestHarness,
        g1, g2):
    """Output is unaffected when either data enable pin is high."""
    four_bit_register = latched_four_bit_register.chip
    clock_line = latched_four_bit_register.clock
    g1_vs, g2_vs = latched_four_bit_register.g

    g1_vs.value = g1
    g2_vs.value = g2

    # Low data lines shouldn't get latched in because g1 or g2 is high.
    for data_vs in latched_four_bit_register.data:
        data_vs.value = False

    # Try and latch in data
    clock_line.value = True
    four_bit_register.evaluate()

    assert four_bit_register.Q1.state
    assert four_bit_register.Q2.state
    assert four_bit_register.Q3.state
    assert four_bit_register.Q4.state


@pytest.mark.parametrize("n,m", [(True, False), (False, True), (True, True)])
def test_output_is_high_impedance_when_gate_control_is_high(
        latched_four_bit_register: FourBitRegisterTestHarness,
        n: bool, m: bool):
    """Output is high impedance when either gate control pin is high."""
    four_bit_register = latched_four_bit_register.chip
    n_vs, m_vs = latched_four_bit_register.nm
    n_vs.value = n
    m_vs.value = m

    four_bit_register.evaluate()

    assert four_bit_register.Q1.state is None
    assert four_bit_register.Q2.state is None
    assert four_bit_register.Q3.state is None
    assert four_bit_register.Q4.state is None


def test_ram_can_read_and_write_data():
    """Data can be read in and out of RAM."""
    chip = eater.part.Ram()
    init_power(chip)

    chip.CHIP_SELECT.set(eater.part.VoltageSource(False))
    write_enable = eater.part.VoltageSource(True)
    out_enable = eater.part.VoltageSource(True)

    address_sources = [eater.part.VoltageSource(False) for _ in range(4)]
    data_sources = [eater.part.VoltageSource(False) for _ in range(8)]
    # Write to 16 memory locations
    for i in range(16):
        # Inverted line: enable write.
        write_enable.value = False
        chip.WRITE_ENABLE.set(write_enable)

        # Write the address to the data portion as well
        address = eater.part.int_to_list(i, 4)
        data = eater.part.int_to_list(i, 8)

        # Set address lines
        for address_bit, address_line, address_vs in zip(address, chip.address_lines, address_sources):
            address_vs.value = address_bit
            address_line.set(address_vs)

        # Set data lines
        for data_bit, (data_line, _), data_vs in zip(data, chip.io_lines, data_sources):
            data_vs.value = data_bit
            data_line.set(data_vs)

        # Read in data
        chip.evaluate()

        # Clear data lines
        for (data_line, _), data_vs in zip(chip.io_lines, data_sources):
            data_line.clear(data_vs)

        # Read data
        write_enable.value = True
        chip.WRITE_ENABLE.set(write_enable)
        out_enable.value = False
        chip.OUTPUT_ENABLE.set(out_enable)
        chip.evaluate()

        read_data = [pin.state for pin, _ in chip.io_lines[0:8]]
        assert read_data == data, f"Data in address {i}"


@dataclasses.dataclass()
class CounterTestHarness:
    counter: eater.part.BinaryCounter
    clock: eater.part.VoltageSource
    clr: eater.part.VoltageSource
    inputs: List[eater.part.VoltageSource]
    enable_p: eater.part.VoltageSource
    enable_t: eater.part.VoltageSource
    load: eater.part.VoltageSource

    def do_clock(self):
        self.clock.value = True
        self.counter.evaluate()
        self.clock.value = False
        self.counter.evaluate()

    def set_input(self, value: int):
        bits = eater.part.int_to_list(value, 4)
        for bit, vs in zip(bits, self.inputs):
            vs.value = bit

    def value(self):
        return eater.part.list_to_int([pin.state for pin, _ in self.counter.outputs])


@pytest.fixture()
def counter() -> CounterTestHarness:
    counter = eater.part.BinaryCounter()
    init_power(counter)

    clock_vs = eater.part.VoltageSource(False)
    clr_vs = eater.part.VoltageSource(True)
    inputs_vs = [eater.part.VoltageSource(False) for _ in range(4)]
    enable_p_vs = eater.part.VoltageSource(True)
    enable_t_vs = eater.part.VoltageSource(True)
    load = eater.part.VoltageSource(True)

    counter.CLK.set(clock_vs)
    counter.CLR.set(clr_vs)
    counter.ENABLE_P.set(enable_p_vs)
    counter.ENABLE_T.set(enable_t_vs)
    counter.LOAD.set(load)

    for vs, pin in zip(inputs_vs, counter.inputs):
        pin.set(vs)

    return CounterTestHarness(
        counter=counter,
        clock=clock_vs, clr=clr_vs,
        inputs=inputs_vs,
        enable_p=enable_p_vs,
        enable_t=enable_t_vs,
        load=load,
    )


def test_increment_counter(counter: CounterTestHarness):
    [counter.do_clock() for _ in range(7)]
    assert counter.value() == 7


def test_load_counter(counter: CounterTestHarness):
    counter.load.value = False
    counter.set_input(10)
    counter.do_clock()
    assert counter.value() == 10

    counter.load.value = True
    counter.do_clock()
    assert counter.value() == 11


@pytest.mark.parametrize("enable", [(False, True), (True, False), (False, False)])
def test_counter_not_incremented_when_enable_low(counter: CounterTestHarness, enable: Tuple[bool, bool]):
    enable_p, enable_t = enable
    counter.enable_p.value = enable_p
    counter.enable_t.value = enable_t
    counter.do_clock()
    assert counter.value() == 0


def test_ripple_carry_when_all_bits_high(counter: CounterTestHarness):
    """Ripple carry pin is high when counter is 15 and enable_t is high."""
    counter.load.value = False
    counter.set_input(15)
    counter.do_clock()

    assert counter.counter.CARRY.state


def test_ripple_carry_disabled_when_enable_t_low(counter: CounterTestHarness):
    counter.load.value = False
    counter.set_input(15)
    counter.enable_t.value = False
    counter.do_clock()

    assert not counter.counter.CARRY.state


@dataclasses.dataclass()
class AdderTestHarness:
    adder: eater.part.FourBitAdder
    a_bus: eater.part.Bus
    b_bus: eater.part.Bus
    sum_bus: eater.part.Bus


@pytest.fixture()
def adder() -> AdderTestHarness:
    adder = eater.part.FourBitAdder()
    init_power(adder)

    a_bus = eater.part.Bus([eater.part.Junction() for _ in range(4)])
    b_bus = eater.part.Bus([eater.part.Junction() for _ in range(4)])
    sum_bus = eater.part.Bus([eater.part.Junction() for _ in range(4)])
    adder.connect_a(a_bus)
    adder.connect_b(b_bus)
    adder.connect_sum(sum_bus)

    return AdderTestHarness(
        adder=adder,
        a_bus=a_bus,
        b_bus=b_bus,
        sum_bus=sum_bus,
    )


@pytest.mark.parametrize(
    ["a", "b", "carry_in", "sum", "carry_out"],
    [
        (0b0000, 0b0000, False, 0b0000, False),
        (0b0001, 0b0000, False, 0b0001, False),
        (0b0001, 0b0001, False, 0b0010, False),
        (0b1111, 0b0001, False, 0b0000, True),
        (0b1111, 0b1111, False, 0b1110, True),
        (0b0000, 0b0000, True,  0b0001, False),
        (0b1111, 0b1111, True,  0b1111, True),
    ]
)
def test_adder(adder: AdderTestHarness, a: int, b: int, carry_in: bool, sum: int, carry_out: int):
    adder.a_bus.pull_to(eater.part.int_to_list(a, 4))
    adder.b_bus.pull_to(eater.part.int_to_list(b, 4))
    adder.adder.CARRY_IN.set(eater.part.VoltageSource(carry_in))

    adder.adder.evaluate()
    assert sum == eater.part.list_to_int(adder.sum_bus.value)
    assert carry_out == adder.adder.CARRY_OUT.state
