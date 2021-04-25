from __future__ import annotations

import collections
import dataclasses
from typing import Tuple

import pytest

import eater.assembly
import eater.part


def clock(register: RegisterTestHarness):
    register.clk.voltage.value = True
    register.register.evaluate()
    register.clk.voltage.value = False
    register.register.evaluate()


def clock_ram(ram: RamTestHarness):
    ram.clk.voltage.value = True
    ram.ram.evaluate()
    ram.clk.voltage.value = False
    ram.ram.evaluate()


TestPoint = collections.namedtuple("TestPoint", ["pin", "voltage"])


def input_pin(value: bool) -> TestPoint:
    junction = eater.part.Junction()
    vs = eater.part.VoltageSource(value)
    junction.set(vs)
    return TestPoint(junction, vs)


@dataclasses.dataclass
class RegisterTestHarness:
    register: eater.assembly.Register
    clk: TestPoint
    clr: TestPoint
    address_in: TestPoint
    address_out: TestPoint
    bus: eater.part.Bus


@pytest.fixture()
def empty_register() -> RegisterTestHarness:
    vcc_wire, vcc_src = input_pin(True)
    gnd_wire, gnd_src = input_pin(False)

    clk_wire, clk_src = input_pin(False)
    clr_wire, clr_src = input_pin(False)
    address_in_wire, address_in_src = input_pin(True)
    address_out_wire, address_out_src = input_pin(True)

    bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

    register = eater.assembly.Register(vcc_wire, gnd_wire, clr_wire, clk_wire, address_in_wire, address_out_wire, bus)

    return RegisterTestHarness(
        register=register,
        clk=TestPoint(clk_wire, clk_src),
        clr=TestPoint(clr_wire, clr_src),
        address_in=TestPoint(address_in_wire, address_in_src),
        address_out=TestPoint(address_out_wire, address_out_src),
        bus=bus,
    )


def test_clock_in_data(empty_register: RegisterTestHarness):
    empty_register.address_in.voltage.value = False
    empty_register.address_out.voltage.value = True
    empty_register.bus.pull_to([True] + [False] * 7)
    clock(empty_register)

    empty_register.address_in.voltage.value = True
    empty_register.address_out.voltage.value = False
    empty_register.bus.pull_to([None] * 8)
    clock(empty_register)

    assert empty_register.bus.value == [True] + [False] * 7
    assert empty_register.register.register_bus.value == [True] + [False] * 7


def test_cannot_clock_in_with_address_in_disabled(empty_register: RegisterTestHarness):
    # Load up register with True values
    empty_register.address_in.voltage.value = False
    empty_register.address_out.voltage.value = True
    empty_register.bus.pull_to([True] * 8)
    clock(empty_register)

    # Disable address input and try to load False values
    empty_register.address_in.voltage.value = True
    empty_register.address_out.voltage.value = True
    empty_register.bus.pull_to([False] * 8)
    clock(empty_register)

    # Write output to bus. It shouldn't have changed from True.
    empty_register.address_in.voltage.value = True
    empty_register.address_out.voltage.value = False
    empty_register.bus.pull_to([None] * 8)
    clock(empty_register)

    assert empty_register.bus.value == [True] * 8
    assert empty_register.register.register_bus.value == [True] * 8


@dataclasses.dataclass
class RamTestHarness:
    ram: eater.assembly.RamModule
    clk: TestPoint
    clr: TestPoint
    address_in: TestPoint
    ram_in: TestPoint
    ram_out: TestPoint
    bus: eater.part.Bus


@pytest.fixture()
def ram_harness() -> RamTestHarness:
    vcc_wire, vcc_src = input_pin(True)
    gnd_wire, gnd_src = input_pin(False)

    clk_wire, clk_src = input_pin(False)
    clr_wire, clr_src = input_pin(False)
    address_in_wire, address_in_src = input_pin(True)
    memory_in_wire, memory_in_src = input_pin(False)
    memory_out_wire, memory_out_src = input_pin(True)

    bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

    ram = eater.assembly.RamModule(
        vcc_wire, gnd_wire,
        clr_wire, clk_wire,
        address_in_wire,
        memory_in_wire, memory_out_wire,
        bus
    )

    return RamTestHarness(
        ram=ram,
        clk=TestPoint(clk_wire, clk_src),
        clr=TestPoint(clr_wire, clr_src),
        address_in=TestPoint(address_in_wire, address_in_src),
        ram_in=TestPoint(memory_in_wire, memory_in_src),
        ram_out=TestPoint(memory_out_wire, memory_out_src),
        bus=bus,
    )


def test_read_write_ram(ram_harness: RamTestHarness):
    address = 10
    data = 20

    # Enable address input, set address on bus and load address into register
    ram_harness.address_in.voltage.value = False
    ram_harness.bus.pull_to(eater.part.int_to_list(address, 4))
    clock_ram(ram_harness)

    # Disable address input, set data on bus, enable ram input and load data into ram
    ram_harness.address_in.voltage.value = True
    ram_harness.bus.pull_to(eater.part.int_to_list(data, 8))
    ram_harness.ram_in.voltage.value = True
    clock_ram(ram_harness)

    # Disable ram input, clear bus, enable ram output, load data into bus
    ram_harness.address_in.voltage.value = True
    ram_harness.ram_out.voltage.value = False
    ram_harness.ram_in.voltage.value = False
    ram_harness.bus.pull_to([None] * 8)
    clock_ram(ram_harness)

    result = eater.part.list_to_int(ram_harness.bus.value)
    assert result == data


@dataclasses.dataclass
class ProgramCounterTestHarness:
    pc: eater.assembly.ProgramCounter
    clk: TestPoint
    clr: TestPoint
    counter_enable: TestPoint
    jump: TestPoint
    counter_out: TestPoint
    bus: eater.part.Bus

    def do_clock(self):
        self.clk.voltage.value = True
        self.pc.evaluate()
        self.clk.voltage.value = False
        self.pc.evaluate()

    def value(self) -> int:
        return eater.part.list_to_int([p.state for p in self.bus.conductors[0:4]])


@pytest.fixture()
def program_counter() -> ProgramCounterTestHarness:
    vcc_wire, vcc_src = input_pin(True)
    gnd_wire, gnd_src = input_pin(False)

    clk_wire, clk_src = input_pin(False)
    clr_wire, clr_src = input_pin(True)
    counter_enable_wire, counter_enable_src = input_pin(True)
    jump_wire, jump_src = input_pin(True)
    counter_out_wire, counter_out_src = input_pin(True)

    bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

    pc = eater.assembly.ProgramCounter(
        vcc_wire, gnd_wire,
        clr_wire, clk_wire,
        counter_out_wire, counter_enable_wire, jump_wire,
        bus
    )
    return ProgramCounterTestHarness(
        pc=pc,
        clk=TestPoint(clk_wire, clk_src),
        clr=TestPoint(clr_wire, clr_src),
        counter_enable=TestPoint(counter_enable_wire, counter_enable_src),
        jump=TestPoint(jump_wire, jump_src),
        counter_out=TestPoint(counter_out_wire, counter_out_src),
        bus=bus,
    )


def test_increment_program_counter(program_counter: ProgramCounterTestHarness):
    # Nothing on bus. Count 7 times.
    assert program_counter.bus.value == [None] * 8
    [program_counter.do_clock() for _ in range(7)]

    # Stop counting, enable count output
    program_counter.counter_enable.voltage.value = False
    program_counter.counter_out.voltage.value = False
    program_counter.do_clock()

    # Count is now on the bus
    assert program_counter.value() == 7


def test_jump_program_counter(program_counter: ProgramCounterTestHarness):
    # Enable jump, push 9 to bus, disable count.
    program_counter.jump.voltage.value = False
    program_counter.bus.pull_to(eater.part.int_to_list(9, 4))
    program_counter.counter_enable.voltage.value = False
    program_counter.do_clock()

    # Clear bus, clear jump, enable output.
    program_counter.bus.pull_to([None] * 8)
    program_counter.jump.voltage.value = True
    program_counter.counter_out.voltage.value = False
    program_counter.do_clock()

    assert program_counter.value() == 9


@dataclasses.dataclass
class AluTestHarness:
    alu: eater.assembly.Alu
    clk: TestPoint
    clr: TestPoint
    result_out: TestPoint
    subtract: TestPoint
    flags_in: TestPoint
    carry_out: eater.part.Junction
    zero_out: eater.part.Junction
    a_bus: eater.part.Bus
    b_bus: eater.part.Bus
    bus: eater.part.Bus

    def do_clock(self):
        self.clk.voltage.value = True
        self.alu.evaluate()
        self.clk.voltage.value = False
        self.alu.evaluate()

    def value(self) -> int:
        return eater.part.list_to_int([p.state for p in self.bus.conductors])


@pytest.fixture()
def alu() -> AluTestHarness:
    vcc = input_pin(True)
    gnd = input_pin(False)

    clk = input_pin(False)
    clr = input_pin(False)
    result_out = input_pin(True)
    subtract = input_pin(False)
    flags_in = input_pin(True)
    carry_out = eater.part.Junction()
    zero_out = eater.part.Junction()
    a_bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])
    b_bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])
    main_bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

    alu = eater.assembly.Alu(
        vcc=vcc.pin, gnd=gnd.pin,
        clr=clr.pin, clk=clk.pin,
        result_out=result_out.pin,
        subtract=subtract.pin,
        flags_in=flags_in.pin,
        carry_out=carry_out,
        zero_out=zero_out,
        a_bus=a_bus, b_bus=b_bus, bus=main_bus
    )

    return AluTestHarness(
        alu=alu,
        clk=clk, clr=clr,
        result_out=result_out, subtract=subtract, flags_in=flags_in,
        carry_out=carry_out, zero_out=zero_out,
        a_bus=a_bus, b_bus=b_bus, bus=main_bus
    )


@pytest.mark.parametrize(
    ["a", "b", "subtract", "expected_sum", "expected_carry", "expected_zero"],
    [
        (1, 2, False, 3, False, False),
        (255, 1, False, 0, True, True),
        (0, 0, False, 0, False, True),
        (0, 0, True, 0, True, True),  # 0 - 0 does trigger a carry
        (0, 1, True, eater.part.to_unsigned(-1), False, False),
        (eater.part.to_unsigned(-255), 1, True, 0, True, True),
    ]
)
def test_alu_can_add(
        alu: AluTestHarness,
        a: int, b: int, subtract: bool,
        expected_sum: int, expected_carry: bool, expected_zero: bool):
    alu.a_bus.pull_to(eater.part.int_to_list(a, 8))
    alu.b_bus.pull_to(eater.part.int_to_list(b, 8))

    # Enable flags in and bus output
    alu.flags_in.voltage.value = False
    alu.result_out.voltage.value = False

    # Optionally enable subtract line
    alu.subtract.voltage.value = subtract

    alu.do_clock()
    actual_result = eater.part.list_to_int(alu.bus.value)
    actual_carry = alu.carry_out.state
    actual_zero = alu.zero_out.state

    assert actual_result == expected_sum
    assert actual_carry == expected_carry
    assert actual_zero == expected_zero


def test_control_runs():
    control = eater.assembly.Control()

    lda = 0b0000 << 4
    add = 0b0001 << 4

    control.ram.fiddle(0, lda | 14)
    control.ram.fiddle(1, add | 15)

    control.ram.fiddle(14, 1)
    control.ram.fiddle(15, 2)

    control.lda()
    control.add()
    control.out()
    print()
