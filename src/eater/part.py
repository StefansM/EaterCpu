from __future__ import annotations

import abc
from typing import Any, List, Optional, Set, Tuple


def to_signed(unsigned: int) -> int:
    return 2**8 - unsigned


def to_unsigned(signed: int) -> int:
    return 2**8 + signed


def _bit_str(value: Optional[bool]) -> str:
    if value is None:
        return 'x'
    elif value:
        return '1'
    else:
        return '0'


def list_to_int(values: List[bool]) -> int:
    value = 0
    for i, bit in enumerate(values):
        if bit:
            value |= (1 << i)
    return value


def int_to_list(value: int, bits: int) -> List[bool]:
    out = []
    for i in range(bits):
        out.append(value & (1 << i) != 0)
    return out


class Bus:
    def __init__(self, conductors: List[Junction]):
        self.conductors = conductors
        self.voltage_sources = [VoltageSource(False) for _ in conductors]

    def __str__(self):
        bit_str = "".join([_bit_str(i.state) for i in self.conductors])
        return f"Bus({bit_str})"

    @property
    def value(self) -> List[Optional[bool]]:
        return [c.state for c in self.conductors]

    def pull_to(self, value: List[Optional[bool]]):
        for val, c, vs in zip(value, self.conductors, self.voltage_sources):
            if val is None:
                c.clear(vs)
            else:
                vs.value = val
                c.set(vs)


class VoltageSource:
    def __init__(self, value: bool):
        self.value = value

    def __str__(self):
        return f"VoltageSource({_bit_str(self.value)})"


class Junction:
    def __init__(self, conductors: List[Junction] = None):
        self._sources: Set[VoltageSource] = set()
        self.conductors = conductors if conductors is not None else []

    @property
    def state(self) -> Optional[bool]:
        logic_levels = [s.value for s in self._sources] + [c.state for c in self.conductors if c.state is not None]
        if not logic_levels:
            return None

        all_1 = all(logic_levels)
        all_0 = not any(logic_levels)

        if not (all_1 or all_0):
            raise ValueError("Conductors have different logic levels.")

        return all_1

    def set(self, source: VoltageSource):
        self._sources.add(source)
        for conductor in self.conductors:
            conductor.set(source)

    def clear(self, source: Any):
        if source in self._sources:
            self._sources.remove(source)

        for conductor in self.conductors:
            conductor.clear(source)

    def __str__(self):
        return f"Junction({_bit_str(self.state)})"


class PoweredJunction(Junction):
    def __init__(self, initial: bool):
        super().__init__()
        self.vs = VoltageSource(initial)
        self.set(self.vs)

    def on(self):
        self.vs.value = True
        self.set(self.vs)

    def off(self):
        self.vs.value = False
        self.set(self.vs)


class Pin(Junction):
    def __init__(self, pin_number: int, conductors: List[Junction] = None):
        super().__init__(conductors)
        self.pin_number = pin_number

    def __str__(self):
        return f"Pin({_bit_str(self.state)})"


class Gate(abc.ABC):
    def __init__(self, inputs: List[Pin], output: Pin):
        self.inputs = inputs
        self.output = output
        self._voltage_source = VoltageSource(False)

    @abc.abstractmethod
    def evaluate(self):
        pass


class NandGate(Gate):
    def evaluate(self):
        self._voltage_source.value = not all([i.state for i in self.inputs])
        self.output.set(self._voltage_source)


class NorGate(Gate):
    def evaluate(self):
        self._voltage_source.value = not any([i.state for i in self.inputs])
        self.output.set(self._voltage_source)


class NotGate(Gate):
    def evaluate(self):
        assert len(self.inputs) == 1, "Not gate must have a single input."
        self._voltage_source.value = not self.inputs[0].state
        self.output.set(self._voltage_source)


class AndGate(Gate):
    def evaluate(self):
        self._voltage_source.value = all([i.state for i in self.inputs])
        self.output.set(self._voltage_source)


class OrGate(Gate):
    def evaluate(self):
        self._voltage_source.value = any([i.state for i in self.inputs])
        self.output.set(self._voltage_source)


class XorGate(Gate):
    def evaluate(self):
        assert len(self.inputs) == 2, "XOR gate must have two inputs."
        a = int(self.inputs[0].state or False)
        b = int(self.inputs[1].state or False)
        self._voltage_source.value = bool(a ^ b)
        self.output.set(self._voltage_source)


class Part(abc.ABC):
    @abc.abstractmethod
    def evaluate(self):
        pass


class PoweredPart(Part, abc.ABC):
    def __init__(self, *args, vcc: Pin, gnd: Pin, **kwargs):
        super().__init__(*args, **kwargs)
        self.VCC = vcc
        self.GND = gnd

    def evaluate(self):
        super().evaluate()
        assert self.VCC.state, "VCC is not high."
        assert not self.GND.state, "GND is not low."


class LogicPart(Part, abc.ABC):
    def __init__(self, *args, gates: List[Gate], **kwargs):
        super().__init__(*args, **kwargs)
        self.gates = gates

    def evaluate(self):
        super().evaluate()
        for gate in self.gates:
            gate.evaluate()


class QuadNandGate(LogicPart, PoweredPart):
    """
    74LS00 Quad 2-Input Positive NAND Gate DIP-14

    https://www.jameco.com/z/74LS00-Major-Brands-IC-74LS00-Quad-2-Input-Positive-NAND-Gate-DIP-14_46252.html
    """

    def __init__(self):
        self.A1 = Pin(1)
        self.B1 = Pin(2)
        self.Y1 = Pin(3)

        self.A2 = Pin(4)
        self.B2 = Pin(5)
        self.Y2 = Pin(6)

        self.Y3 = Pin(8)
        self.A3 = Pin(9)
        self.B3 = Pin(10)

        self.Y4 = Pin(11)
        self.A4 = Pin(12)
        self.B4 = Pin(13)

        gates = [
            NandGate([self.A1, self.B1], self.Y1),
            NandGate([self.A2, self.B2], self.Y2),
            NandGate([self.A3, self.B3], self.Y3),
            NandGate([self.A4, self.B4], self.Y4),
        ]

        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class QuadNorGate(PoweredPart, LogicPart):
    """
    74LS02 QUAD 2-INPUT POSITIVE NOR GATE

    https://www.jameco.com/z/74LS02-Major-Brands-IC-74LS02-QUAD-2-INPUT-POSITIVE-NOR-GATE_46287.html
    """

    def __init__(self):
        self.Y1 = Pin(1)
        self.A1 = Pin(2)
        self.B1 = Pin(3)

        self.Y2 = Pin(4)
        self.A2 = Pin(5)
        self.B2 = Pin(6)

        self.A3 = Pin(8)
        self.B3 = Pin(9)
        self.Y3 = Pin(10)

        self.A4 = Pin(11)
        self.B4 = Pin(12)
        self.Y4 = Pin(13)

        gates = [
            NorGate([self.A1, self.B1], self.Y1),
            NorGate([self.A2, self.B2], self.Y2),
            NorGate([self.A3, self.B3], self.Y3),
            NorGate([self.A4, self.B4], self.Y4),
        ]
        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class HexNotGate(PoweredPart, LogicPart):
    """
    74LS04 Hex Inverter

    https://www.jameco.com/z/74LS04-Major-Brands-IC-74LS04-Hex-Inverter_46316.html
    """

    def __init__(self):
        self.A1 = Pin(1)
        self.Y1 = Pin(2)

        self.A2 = Pin(3)
        self.Y2 = Pin(4)

        self.A3 = Pin(5)
        self.Y3 = Pin(6)

        self.Y4 = Pin(8)
        self.A4 = Pin(9)

        self.Y5 = Pin(10)
        self.A5 = Pin(11)

        self.Y6 = Pin(12)
        self.A6 = Pin(13)

        gates = [
            NotGate([self.A1], self.Y1),
            NotGate([self.A2], self.Y2),
            NotGate([self.A3], self.Y3),
            NotGate([self.A4], self.Y4),
            NotGate([self.A5], self.Y5),
            NotGate([self.A6], self.Y6),
        ]
        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class QuadAndGate(PoweredPart, LogicPart):
    """
    74LS08 Quad 2-Input Positive AND Gate

    https://www.jameco.com/z/74LS08-Major-Brands-IC-74LS08-Quad-2-Input-Positive-AND-Gate_46375.html
    """

    def __init__(self):
        self.A1 = Pin(1)
        self.B1 = Pin(2)
        self.Y1 = Pin(3)

        self.A2 = Pin(4)
        self.B2 = Pin(5)
        self.Y2 = Pin(6)

        self.Y3 = Pin(8)
        self.A3 = Pin(9)
        self.B3 = Pin(10)

        self.Y4 = Pin(11)
        self.A4 = Pin(12)
        self.B4 = Pin(13)

        gates = [
            AndGate([self.A1, self.B1], self.Y1),
            AndGate([self.A2, self.B2], self.Y2),
            AndGate([self.A3, self.B3], self.Y3),
            AndGate([self.A4, self.B4], self.Y4),
        ]
        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class QuadOrGate(PoweredPart, LogicPart):
    """
    74LS32 Quad 2-Input Positive OR Gate

    https://www.jameco.com/z/74LS32-Major-Brands-IC-74LS32-Quad-2-Input-Positive-OR-Gate_47466.html
    """

    def __init__(self):
        self.A1 = Pin(1)
        self.B1 = Pin(2)
        self.Y1 = Pin(3)

        self.A2 = Pin(4)
        self.B2 = Pin(5)
        self.Y2 = Pin(6)

        self.Y3 = Pin(8)
        self.A3 = Pin(9)
        self.B3 = Pin(10)

        self.Y4 = Pin(11)
        self.A4 = Pin(12)
        self.B4 = Pin(13)

        gates = [
            OrGate([self.A1, self.B1], self.Y1),
            OrGate([self.A2, self.B2], self.Y2),
            OrGate([self.A3, self.B3], self.Y3),
            OrGate([self.A4, self.B4], self.Y4),
        ]
        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class QuadXorGate(PoweredPart, LogicPart):
    """
    IC 74LS86 QUAD 2-INPUT EXCLUSIVE OR GATE

    https://www.jameco.com/z/74LS86-Major-Brands-IC-74LS86-QUAD-2-INPUT-EXCLUSIVE-OR-GATE_48098.html
    """
    def __init__(self):
        self.A1 = Pin(1)
        self.B1 = Pin(2)
        self.Y1 = Pin(3)

        self.A2 = Pin(4)
        self.B2 = Pin(5)
        self.Y2 = Pin(6)

        self.Y3 = Pin(8)
        self.A3 = Pin(9)
        self.B3 = Pin(10)

        self.Y4 = Pin(11)
        self.A4 = Pin(12)
        self.B4 = Pin(13)

        gates = [
            XorGate([self.A1, self.B1], self.Y1),
            XorGate([self.A2, self.B2], self.Y2),
            XorGate([self.A3, self.B3], self.Y3),
            XorGate([self.A4, self.B4], self.Y4),
        ]

        super().__init__(vcc=Pin(14), gnd=Pin(7), gates=gates)


class OctalBusTransceiver(PoweredPart):
    """
    74LS245 Tri-State Octal Bus Transceiver

    https://www.jameco.com/z/74LS245-Major-Brands-IC-74LS245-Tri-State-Octal-Bus-Transceiver_47212.html
    """

    def __init__(self):
        super().__init__(vcc=Pin(20), gnd=Pin(10))
        self.DIRECTION = Pin(1)

        self.A1 = Pin(2)
        self.A2 = Pin(3)
        self.A3 = Pin(4)
        self.A4 = Pin(5)
        self.A5 = Pin(6)
        self.A6 = Pin(7)
        self.A7 = Pin(8)
        self.A8 = Pin(9)

        self.B8 = Pin(11)
        self.B7 = Pin(12)
        self.B6 = Pin(13)
        self.B5 = Pin(14)
        self.B4 = Pin(15)
        self.B3 = Pin(16)
        self.B2 = Pin(17)
        self.B1 = Pin(18)

        self.ENABLED = Pin(19)

        a_pins = [self.A1, self.A2, self.A3, self.A4, self.A5, self.A6, self.A7, self.A8]
        b_pins = [self.B1, self.B2, self.B3, self.B4, self.B5, self.B6, self.B7, self.B8]
        self.a = [(pin, VoltageSource(False)) for pin in a_pins]
        self.b = [(pin, VoltageSource(False)) for pin in b_pins]

    def _connect_bus(self, bus: Bus, pins: List[Tuple[Pin, VoltageSource]]):
        for conductor, (pin, _) in zip(bus.conductors, pins):
            pin.conductors.append(conductor)

    def set_bus_a(self, bus: Bus):
        self._connect_bus(bus, self.a)

    def set_bus_b(self, bus: Bus):
        self._connect_bus(bus, self.b)

    def evaluate(self):
        super().evaluate()

        # Disable outputs when enable is high
        if self.ENABLED.state:
            for pin, voltage in self.a + self.b:
                pin.clear(voltage)
            return

        direction = self.DIRECTION.state
        if direction is None:
            raise ValueError("Direction pin not tied high or low.")
        elif direction:
            inputs = self.a
            outputs = self.b
        else:
            inputs = self.b
            outputs = self.a

        for (in_pin, in_vs), (out_pin, out_vs) in zip(inputs, outputs):
            out_vs.value = in_pin.state
            out_pin.set(out_vs)

    def __str__(self):
        a_state = "".join([_bit_str(pin.state) for pin, _ in self.a])
        b_state = "".join([_bit_str(pin.state) for pin, _ in self.b])
        return f"OctalBusTransceiver(a={a_state}, b={b_state})"


class FourBitDRegister(PoweredPart):
    """
    74LS173 4-BIT D-TYPE REGISTER 3-STATE OUTPUT

    https://www.jameco.com/z/74LS173-Major-Brands-IC-74LS173-4-BIT-D-TYPE-REGISTER-3-STATE-OUTPUT_46922.html
    """

    def __init__(self):
        super().__init__(vcc=Pin(16), gnd=Pin(8))
        self.M = Pin(1)
        self.N = Pin(2)
        self.Q1 = Pin(3)
        self.Q2 = Pin(4)
        self.Q3 = Pin(5)
        self.Q4 = Pin(6)
        self.CLK = Pin(7)
        self.G1 = Pin(9)
        self.G2 = Pin(10)
        self.D4 = Pin(11)
        self.D3 = Pin(12)
        self.D2 = Pin(13)
        self.D1 = Pin(14)
        self.CLR = Pin(15)

        self.lines = [
            (self.D1, self.Q1, VoltageSource(False)),
            (self.D2, self.Q2, VoltageSource(False)),
            (self.D3, self.Q3, VoltageSource(False)),
            (self.D4, self.Q4, VoltageSource(False)),
        ]

        self._state = [False] * 4
        self._last_clock = False

    def evaluate(self):
        super().evaluate()

        # If either gate control pin is high, output is enabled.
        if self.N.state or self.M.state:
            for _, out_pin, vs in self.lines:
                out_pin.clear(vs)

        # If the clear pin is high, reset the state to zero.
        if self.CLR.state:
            self._state = [False] * 4
            self._set_outputs()
            return

        # If either data enable pin is high, nothing changes.
        if self.G1.state or self.G2.state:
            return

        # On a rising edge, latch in the data bits.
        clock = self.CLK.state
        if clock and not self._last_clock:
            self._state = [d.state for d, _, _ in self.lines]
            self._set_outputs()
            self._last_clock = clock

    def _set_outputs(self):
        for (_, q, vs), data_bit in zip(self.lines, self._state):
            vs.value = data_bit
            q.set(vs)

    def value(self) -> List[bool]:
        return self._state

    def __str__(self):
        bit_str = "".join([_bit_str(i) for i in self.value()])
        return f"FourBitRegister({bit_str})"


class Ram(PoweredPart):
    """
    71256SA12TPG

    https://www.digikey.co.uk/product-detail/en/renesas-electronics-america-inc/71256SA12TPG/800-3674-ND/2011023
    """
    def __init__(self):
        super().__init__(vcc=Pin(28), gnd=Pin(14))
        self.A0 = Pin(10)
        self.A1 = Pin(9)
        self.A2 = Pin(8)
        self.A3 = Pin(7)
        self.A4 = Pin(6)
        self.A5 = Pin(5)
        self.A6 = Pin(4)
        self.A7 = Pin(3)
        self.A8 = Pin(25)
        self.A9 = Pin(24)
        self.A10 = Pin(21)
        self.A11 = Pin(23)
        self.A12 = Pin(2)
        self.A13 = Pin(26)
        self.A14 = Pin(1)

        self.IO0 = Pin(11)
        self.IO1 = Pin(12)
        self.IO2 = Pin(13)
        self.IO3 = Pin(15)
        self.IO4 = Pin(16)
        self.IO5 = Pin(17)
        self.IO6 = Pin(18)
        self.IO7 = Pin(19)

        self.WRITE_ENABLE = Pin(27)
        self.OUTPUT_ENABLE = Pin(22)
        self.CHIP_SELECT = Pin(20)

        self.address_lines = [
            self.A0,
            self.A1,
            self.A2,
            self.A3,
            self.A4,
            self.A5,
            self.A6,
            self.A7,
            self.A8,
            self.A9,
            self.A10,
            self.A11,
            self.A12,
            self.A13,
        ]

        self.io_lines = [
            (self.IO0, VoltageSource(False)),
            (self.IO1, VoltageSource(False)),
            (self.IO2, VoltageSource(False)),
            (self.IO3, VoltageSource(False)),
            (self.IO4, VoltageSource(False)),
            (self.IO5, VoltageSource(False)),
            (self.IO6, VoltageSource(False)),
            (self.IO7, VoltageSource(False)),
        ]

        self._memory = [0] * (2**15)

    def _high_z(self):
        for pin, vs in self.io_lines:
            pin.clear(vs)

    def evaluate(self):
        super().evaluate()

        # Inverted
        if self.CHIP_SELECT.state:
            self._high_z()
            return

        # Inverted
        if not self.WRITE_ENABLE.state:
            # Reading from data pins to memory, so need to remove our voltage source.
            self._high_z()
            data = list_to_int([pin.state for pin, _ in self.io_lines])
            address = list_to_int([pin.state for pin in self.address_lines])
            self._memory[address] = data
            return

        # Inverted
        if not self.OUTPUT_ENABLE.state:
            address = list_to_int([pin.state for pin in self.address_lines])
            data = int_to_list(self._memory[address], 8)
            for (pin, vs), bit in zip(self.io_lines, data):
                vs.value = bit
                pin.set(vs)
            return

        self._high_z()

    def fiddle(self, address: int, data: int):
        self._memory[address] = data


class BinaryCounter(PoweredPart):
    """
    IC 74LS161 4-Bit Synchronous Binary Counter DIP-16

    https://www.jameco.com/z/74LS161-Major-Brands-IC-74LS161-4-Bit-Synchronous-Binary-Counter-DIP-16_46818.html
    """

    def __init__(self):
        self.CLR = Pin(1)
        self.CLK = Pin(2)
        self.D1 = Pin(3)
        self.D2 = Pin(4)
        self.D3 = Pin(5)
        self.D4 = Pin(6)
        self.ENABLE_P = Pin(7)
        self.LOAD = Pin(9)
        self.ENABLE_T = Pin(10)
        self.Q4 = Pin(11)
        self.Q3 = Pin(12)
        self.Q2 = Pin(13)
        self.Q1 = Pin(14)
        self.CARRY = Pin(15)

        self._carry_vs = VoltageSource(False)
        self.CARRY.set(self._carry_vs)

        self.outputs = [
            (self.Q1, VoltageSource(False)),
            (self.Q2, VoltageSource(False)),
            (self.Q3, VoltageSource(False)),
            (self.Q4, VoltageSource(False)),
        ]

        self.inputs = [self.D1, self.D2, self.D3, self.D4]
        self._last_clock = False

        self.count = 0

        super().__init__(vcc=Pin(16), gnd=Pin(8))

    def _write_count(self):
        bits = int_to_list(self.count, 4)
        for (pin, vs), bit in zip(self.outputs, bits):
            vs.value = bit
            pin.set(vs)

    def _read_count(self):
        bits = [pin.state for pin in self.inputs]
        self.count = list_to_int(bits)

    def _set_carry(self):
        if self.count == 15 and self.ENABLE_T.state:
            self._carry_vs.value = True
        else:
            self._carry_vs.value = False

    def evaluate(self):
        super().evaluate()

        if not self.CLR.state:
            self.count = 0
            self._write_count()
            return

        if not self.LOAD.state:
            self._read_count()
            self._write_count()
            self._set_carry()
            return

        # Only operate on rising edge.
        if not (self.CLK.state and not self._last_clock):
            self._last_clock = self.CLK.state
            return

        if self.ENABLE_P.state and self.ENABLE_T.state:
            self.count = (self.count + 1) % 16
            self._set_carry()
            self._write_count()

    def __str__(self):
        return f"BinaryCounter({self.count})"


class FourBitAdder(PoweredPart):
    """
    IC 74LS283 4-BIT BINARY FULL ADD FAST CARRY

    https://www.jameco.com/z/74LS283-Major-Brands-IC-74LS283-4-BIT-BINARY-FULL-ADD-FAST-CARRY_47423.html
    """
    def __init__(self):
        self.S2 = Pin(1)
        self.B2 = Pin(2)
        self.A2 = Pin(3)
        self.S1 = Pin(4)
        self.A1 = Pin(5)
        self.B1 = Pin(6)
        self.CARRY_IN = Pin(7)
        self.CARRY_OUT = Pin(9)
        self.S4 = Pin(10)
        self.B4 = Pin(11)
        self.A4 = Pin(12)
        self.S3 = Pin(13)
        self.A3 = Pin(14)
        self.B3 = Pin(15)

        self.a = [self.A1, self.A2, self.A3, self.A4]
        self.b = [self.B1, self.B2, self.B3, self.B4]
        self.sum = [
            (self.S1, VoltageSource(False)),
            (self.S2, VoltageSource(False)),
            (self.S3, VoltageSource(False)),
            (self.S4, VoltageSource(False)),
        ]
        self._carry_out_vs = VoltageSource(False)

        super().__init__(vcc=Pin(16), gnd=Pin(8))

    def _write(self, value: int):
        for bit, (pin, vs) in zip(int_to_list(value, 4), self.sum):
            vs.value = bit
            pin.set(vs)

    def _connect_bus(self, pins: List[Junction], bus: Bus):
        for pin, bus_line in zip(pins, bus.conductors):
            pin.conductors.append(bus_line)

    def connect_a(self, bus: Bus):
        self._connect_bus(self.a, bus)

    def connect_b(self, bus: Bus):
        self._connect_bus(self.b, bus)

    def connect_sum(self, bus: Bus):
        self._connect_bus([pin for pin, _ in self.sum], bus)

    def evaluate(self):
        super().evaluate()

        a = list_to_int([pin.state for pin in self.a])
        b = list_to_int([pin.state for pin in self.b])
        carry = int(self.CARRY_IN.state or False)

        result = a + b + carry
        result_carry = bool(result & (1 << 4))
        result_non_carry = result & 0b1111

        self._carry_out_vs.value = result_carry
        self.CARRY_OUT.set(self._carry_out_vs)

        self._write(result_non_carry)
