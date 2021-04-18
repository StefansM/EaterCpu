from __future__ import annotations

import abc
from typing import Dict, List, Optional, Tuple


class Wire:
    def __init__(self, default_state: Optional[bool] = None):
        self.state = default_state

    def __str__(self):
        return f"Wire({'1' if self.state else '0'})"


class Bus:
    def __init__(self, conductors: List[Wire]):
        self.conductors = conductors

    def __str__(self):
        return "Bus(" + "".join(["1" if c.state else "0" for c in reversed(self.conductors)]) + ")"


class Junction:
    def __init__(self, conductors: Optional[List[Wire]] = None):
        self.conductors = conductors if conductors else []

    @property
    def state(self) -> Optional[bool]:
        state: Optional[bool] = None
        for conductor in self.conductors:
            if conductor.state is not None:
                if state is not None and conductor.state != state:
                    raise ValueError("Conductors have different logic levels.")

                state = conductor.state

        return state

    @state.setter
    def state(self, value: Optional[bool]):
        for conductor in self.conductors:
            conductor.state = value

    def __str__(self):
        return f"Junction({'0' if self.state else '1'})"


class Part(abc.ABC):
    @abc.abstractmethod
    def evaluate(self):
        pass

    @property
    @abc.abstractmethod
    def pins(self) -> Dict[int, Junction]:
        pass


class LogicPart(Part, abc.ABC):
    def __init__(self):
        self._pins = {i + 1: Junction() for i in range(self.VCC)}

    @property
    @abc.abstractmethod
    def VCC(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def GND(self) -> int:
        pass

    @property
    def pins(self) -> Dict[int, Junction]:
        return self._pins

    @property
    @abc.abstractmethod
    def gates(self) -> Tuple[List[int], int]:
        pass

    @abc.abstractmethod
    def evaluate_gate(self, inputs: List[int], output: int):
        pass

    def evaluate(self):
        assert self.pins[self.VCC].state, "VCC is not high."
        assert not self.pins[self.GND].state, "GND is not low."
        for inputs, output in self.gates:
            self.evaluate_gate(inputs, output)


class QuadNandGate(LogicPart):
    """
    74LS00 Quad 2-Input Positive NAND Gate DIP-14

    https://www.jameco.com/z/74LS00-Major-Brands-IC-74LS00-Quad-2-Input-Positive-NAND-Gate-DIP-14_46252.html
    """
    A1 = 1
    B1 = 2
    Y1 = 3

    A2 = 4
    B2 = 5
    Y2 = 6

    GND = 7
    Y3 = 8
    A3 = 9
    B3 = 10

    Y4 = 11
    A4 = 12
    B4 = 13

    VCC = 14

    gates = [
        ([A1, B1], Y1),
        ([A2, B2], Y2),
        ([A3, B3], Y3),
        ([A4, B4], Y4),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 2, "Gates are not dual-input."
        self.pins[output].state = not (self.pins[inputs[0]].state and self.pins[inputs[1]].state)


class QuadNorGate(LogicPart):
    """
    74LS02 QUAD 2-INPUT POSITIVE NOR GATE

    https://www.jameco.com/z/74LS02-Major-Brands-IC-74LS02-QUAD-2-INPUT-POSITIVE-NOR-GATE_46287.html
    """

    Y1 = 1
    A1 = 2
    B1 = 3

    Y2 = 4
    A2 = 5
    B2 = 6

    GND = 7

    A3 = 8
    B3 = 9
    Y3 = 10

    A4 = 11
    B4 = 12
    Y4 = 13

    VCC = 14

    gates = [
        ([A1, B1], Y1),
        ([A2, B2], Y2),
        ([A3, B3], Y3),
        ([A4, B4], Y4),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 2, "Gates are not dual-input."
        self.pins[output].state = not (self.pins[inputs[0]].state or self.pins[inputs[1]].state)


class HexNotGate(LogicPart):
    """
    74LS04 Hex Inverter

    https://www.jameco.com/z/74LS04-Major-Brands-IC-74LS04-Hex-Inverter_46316.html
    """

    A1 = 1
    Y1 = 2

    A2 = 3
    Y2 = 4

    A3 = 5
    Y3 = 6

    GND = 7

    Y4 = 8
    A4 = 9

    Y5 = 10
    A5 = 11

    Y6 = 12
    A6 = 13

    VCC = 14

    gates = [
        ([A1], Y1),
        ([A2], Y2),
        ([A3], Y3),
        ([A4], Y4),
        ([A5], Y5),
        ([A6], Y6),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 1, "Invert can only take one input per gate."
        self.pins[output].state = not self.pins[inputs[0]].state


class QuadAndGate(LogicPart):
    """
    74LS08 Quad 2-Input Positive AND Gate

    https://www.jameco.com/z/74LS08-Major-Brands-IC-74LS08-Quad-2-Input-Positive-AND-Gate_46375.html
    """
    A1 = 1
    B1 = 2
    Y1 = 3

    A2 = 4
    B2 = 5
    Y2 = 6

    GND = 7

    Y3 = 8
    A3 = 9
    B3 = 10

    Y4 = 11
    A4 = 12
    B4 = 13

    VCC = 14

    gates = [
        ([A1, B1], Y1),
        ([A2, B2], Y2),
        ([A3, B3], Y3),
        ([A4, B4], Y4),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 2, "Gate are not dual-input."
        self.pins[output].state = self.pins[inputs[0]].state and self.pins[inputs[1]].state


class QuadOrGate(LogicPart):
    """
    74LS32 Quad 2-Input Positive OR Gate

    https://www.jameco.com/z/74LS32-Major-Brands-IC-74LS32-Quad-2-Input-Positive-OR-Gate_47466.html
    """

    A1 = 1
    B1 = 2
    Y1 = 3

    A2 = 4
    B2 = 5
    Y2 = 6

    GND = 7

    Y3 = 8
    A3 = 9
    B3 = 10

    Y4 = 11
    A4 = 12
    B4 = 13

    VCC = 14


    gates = [
        ([A1, B1], Y1),
        ([A2, B2], Y2),
        ([A3, B3], Y3),
        ([A4, B4], Y4),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 2, "Gate are not dual-input."
        self.pins[output].state = self.pins[inputs[0]].state or self.pins[inputs[1]].state


class OctalBusTransceiver(LogicPart):
    """
    74LS245 Tri-State Octal Bus Transceiver

    https://www.jameco.com/z/74LS245-Major-Brands-IC-74LS245-Tri-State-Octal-Bus-Transceiver_47212.html
    """

    DIRECTION = 1

    A1 = 2
    A2 = 3
    A3 = 4
    A4 = 5
    A5 = 6
    A6 = 7
    A7 = 8
    A8 = 9

    GND = 10

    B8 = 11
    B7 = 12
    B6 = 13
    B5 = 14
    B4 = 15
    B3 = 16
    B2 = 17
    B1 = 18

    ENABLED_INVERTED = 19

    VCC = 20

    gates = [
        ([A1], B1),
        ([A2], B2),
        ([A3], B3),
        ([A4], B4),
        ([A5], B5),
        ([A6], B6),
        ([A7], B7),
        ([A8], B8),
    ]

    def evaluate_gate(self, inputs: List[int], output: int):
        assert len(inputs) == 1, "Bus transceiver takes a single input."
        if self.pins[self.ENABLED_INVERTED].state:
            self.pins[inputs[0]].state = None
            self.pins[output].state = None
            return

        direction = self.pins[self.DIRECTION].state
        if direction:
            self.pins[output].state = self.pins[inputs[0]].state
        else:
            self.pins[inputs[0]].state = self.pins[output].state


class FourBitDRegister(Part):
    """
    74LS173 4-BIT D-TYPE REGISTER 3-STATE OUTPUT

    https://www.jameco.com/z/74LS173-Major-Brands-IC-74LS173-4-BIT-D-TYPE-REGISTER-3-STATE-OUTPUT_46922.html
    """

    M = 1
    N = 2
    Q1 = 3
    Q2 = 4
    Q3 = 5
    Q4 = 6
    CLK = 7
    GND = 8
    G1 = 9
    G2 = 10
    D4 = 11
    D3 = 12
    D2 = 13
    D1 = 14
    CLR = 15
    VCC = 16

    lines = [
        (D1, Q1),
        (D2, Q2),
        (D3, Q3),
        (D4, Q4),
    ]

    def __init__(self):
        self._pins = {i + 1: Junction() for i in range(self.VCC)}
        self._state = [False] * 4
        self._last_clock = False

    # TODO: Implement N, M
    def evaluate(self):
        assert self.pins[self.VCC].state, "VCC is not high."
        assert not self.pins[self.GND].state, "GND is not low."

        # If the clear pin is high, reset the state to zero.
        if self.pins[self.CLR].state:
            self._state = [False] * 4
            self._set_outputs()
            return

        # If either data enable pit is high, nothing changes.
        g1 = self.pins[self.G1].state
        g2 = self.pins[self.G2].state
        if g1 or g2:
            return

        # On a rising edge, latch in the data bits.
        clock = self.pins[self.CLK].state
        if clock and not self._last_clock:
            self._state = [self.pins[d].state for d, _ in self.lines]
            self._set_outputs()

    def _set_outputs(self):
        for (_, q), data_bit in zip(self.lines, self._state):
            self.pins[q].state = data_bit

    @property
    def pins(self) -> Dict[int, Junction]:
        return self._pins

    def value(self) -> List[bool]:
        return self._state
