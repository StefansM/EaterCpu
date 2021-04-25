from typing import List, Optional, Tuple

import eater.part


def connect_power(vcc: eater.part.Junction, gnd: eater.part.Junction, part: eater.part.PoweredPart):
    part.VCC.conductors.append(vcc)
    part.GND.conductors.append(gnd)


class Register:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            register_in: eater.part.Junction, register_out: eater.part.Junction,
            bus: eater.part.Bus):

        self.gnd = gnd
        self.vcc = vcc

        self.clr = clr
        self.clk = clk
        self.register_in = register_in
        self.register_out = register_out
        self.bus = bus

        self.high_register = eater.part.FourBitDRegister()
        self.low_register = eater.part.FourBitDRegister()
        self.trans = eater.part.OctalBusTransceiver()
        self.register_bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

        connect_power(vcc, gnd, self.high_register)
        connect_power(vcc, gnd, self.low_register)
        connect_power(vcc, gnd, self.trans)

        self._connect_low_register_input()
        self._connect_low_register_output()
        self._connect_high_register_input()
        self._connect_high_register_output()
        self._connect_control_lines_to_register(self.low_register)
        self._connect_control_lines_to_register(self.high_register)
        self._connect_control_lines_to_transceiver()
        self._connect_bus_output()

    def _connect_control_lines_to_register(self, register: eater.part.FourBitDRegister):
        register.CLR.conductors.append(self.clr)
        register.CLK.conductors.append(self.clk)
        register.N.conductors.append(self.gnd)
        register.M.conductors.append(self.gnd)
        register.G1.conductors.append(self.register_in)
        register.G2.conductors.append(self.register_in)

    def _connect_low_register_input(self):
        self.low_register.D1.conductors.append(self.bus.conductors[3])
        self.low_register.D2.conductors.append(self.bus.conductors[2])
        self.low_register.D3.conductors.append(self.bus.conductors[1])
        self.low_register.D4.conductors.append(self.bus.conductors[0])

    def _connect_high_register_input(self):
        self.high_register.D1.conductors.append(self.bus.conductors[7])
        self.high_register.D2.conductors.append(self.bus.conductors[6])
        self.high_register.D3.conductors.append(self.bus.conductors[5])
        self.high_register.D4.conductors.append(self.bus.conductors[4])

    def _connect_low_register_output(self):
        self.low_register.Q1.conductors.append(self.trans.A5)
        self.low_register.Q2.conductors.append(self.trans.A6)
        self.low_register.Q3.conductors.append(self.trans.A7)
        self.low_register.Q4.conductors.append(self.trans.A8)

        self.low_register.Q1.conductors.append(self.register_bus.conductors[3])
        self.low_register.Q2.conductors.append(self.register_bus.conductors[2])
        self.low_register.Q3.conductors.append(self.register_bus.conductors[1])
        self.low_register.Q4.conductors.append(self.register_bus.conductors[0])

    def _connect_high_register_output(self):
        self.high_register.Q1.conductors.append(self.trans.A1)
        self.high_register.Q2.conductors.append(self.trans.A2)
        self.high_register.Q3.conductors.append(self.trans.A3)
        self.high_register.Q4.conductors.append(self.trans.A4)

        self.high_register.Q1.conductors.append(self.register_bus.conductors[7])
        self.high_register.Q2.conductors.append(self.register_bus.conductors[6])
        self.high_register.Q3.conductors.append(self.register_bus.conductors[5])
        self.high_register.Q4.conductors.append(self.register_bus.conductors[4])

    def _connect_bus_output(self):
        trans_out = [
            self.trans.B1,
            self.trans.B2,
            self.trans.B3,
            self.trans.B4,
            self.trans.B5,
            self.trans.B6,
            self.trans.B7,
            self.trans.B8,
        ]
        for bus_c, trans_c in zip(reversed(self.bus.conductors), trans_out):
            bus_c.conductors.append(trans_c)

    def evaluate(self):
        self.low_register.evaluate()
        self.high_register.evaluate()
        self.trans.evaluate()

    def _connect_control_lines_to_transceiver(self):
        self.trans.DIRECTION.conductors.append(self.vcc)
        self.trans.ENABLED.conductors.append(self.register_out)


class InstructionRegister:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            instruction_in: eater.part.Junction, instruction_out: eater.part.Junction,
            instrucon_bus: eater.part.Bus, bus: eater.part.Bus):

        self.gnd = gnd
        self.vcc = vcc

        self.clr = clr
        self.clk = clk
        self.instruction_in = instruction_in
        self.instruction_out = instruction_out
        self.bus = bus
        self.instruction_bus = instrucon_bus

        self.high_register = eater.part.FourBitDRegister()
        self.low_register = eater.part.FourBitDRegister()
        self.trans = eater.part.OctalBusTransceiver()
        self.register_bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])

        connect_power(vcc, gnd, self.high_register)
        connect_power(vcc, gnd, self.low_register)
        connect_power(vcc, gnd, self.trans)

        self._connect_low_register_input()
        self._connect_low_register_output()
        self._connect_high_register_input()
        self._connect_high_register_output()
        self._connect_control_lines_to_register(self.low_register)
        self._connect_control_lines_to_register(self.high_register)
        self._connect_control_lines_to_transceiver()
        self._connect_bus_output()
        self._connect_instruction_bus()

    def _connect_instruction_bus(self):
        for bus_line, (_, output_pin, _) in zip(self.instruction_bus.conductors, self.high_register.lines):
            bus_line.conductors.append(output_pin)

    def _connect_control_lines_to_register(self, register: eater.part.FourBitDRegister):
        register.CLR.conductors.append(self.clr)
        register.CLK.conductors.append(self.clk)
        register.N.conductors.append(self.gnd)
        register.M.conductors.append(self.gnd)
        register.G1.conductors.append(self.instruction_in)
        register.G2.conductors.append(self.instruction_in)

    def _connect_low_register_input(self):
        self.low_register.D1.conductors.append(self.bus.conductors[3])
        self.low_register.D2.conductors.append(self.bus.conductors[2])
        self.low_register.D3.conductors.append(self.bus.conductors[1])
        self.low_register.D4.conductors.append(self.bus.conductors[0])

    def _connect_high_register_input(self):
        self.high_register.D1.conductors.append(self.bus.conductors[7])
        self.high_register.D2.conductors.append(self.bus.conductors[6])
        self.high_register.D3.conductors.append(self.bus.conductors[5])
        self.high_register.D4.conductors.append(self.bus.conductors[4])

    def _connect_low_register_output(self):
        self.low_register.Q1.conductors.append(self.trans.A5)
        self.low_register.Q2.conductors.append(self.trans.A6)
        self.low_register.Q3.conductors.append(self.trans.A7)
        self.low_register.Q4.conductors.append(self.trans.A8)

    def _connect_high_register_output(self):
        self.high_register.Q1.conductors.append(self.register_bus.conductors[3])
        self.high_register.Q2.conductors.append(self.register_bus.conductors[2])
        self.high_register.Q3.conductors.append(self.register_bus.conductors[1])
        self.high_register.Q4.conductors.append(self.register_bus.conductors[0])

    def _connect_bus_output(self):
        trans_out = [
            self.trans.B1,
            self.trans.B2,
            self.trans.B3,
            self.trans.B4,
            self.trans.B5,
            self.trans.B6,
            self.trans.B7,
            self.trans.B8,
        ]
        for bus_c, trans_c in zip(reversed(self.bus.conductors), trans_out):
            bus_c.conductors.append(trans_c)

    def evaluate(self):
        self.low_register.evaluate()
        self.high_register.evaluate()
        self.trans.evaluate()

    def _connect_control_lines_to_transceiver(self):
        self.trans.DIRECTION.conductors.append(self.vcc)
        self.trans.ENABLED.conductors.append(self.instruction_out)

    def _tie_unused_transceiver_lines_low(self):
        self.trans.A1.conductors.append(self.gnd)
        self.trans.A2.conductors.append(self.gnd)
        self.trans.A3.conductors.append(self.gnd)
        self.trans.A4.conductors.append(self.gnd)


class MemoryRegister:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            memory_in: eater.part.Junction,
            bus: eater.part.Bus):

        self.gnd = gnd
        self.vcc = vcc

        self.clr = clr
        self.clk = clk
        self.memory_in = memory_in
        self.bus = bus

        self.register = eater.part.FourBitDRegister()
        self.register_bus = eater.part.Bus([eater.part.Junction() for _ in range(4)])

        connect_power(vcc, gnd, self.register)

        self._connect_register_input()
        self._connect_register_output()
        self._connect_control_lines_to_register()

    def _connect_control_lines_to_register(self):
        self.register.CLR.conductors.append(self.clr)
        self.register.CLK.conductors.append(self.clk)
        self.register.N.conductors.append(self.gnd)
        self.register.M.conductors.append(self.gnd)
        self.register.G1.conductors.append(self.memory_in)
        self.register.G2.conductors.append(self.memory_in)

    def _connect_register_input(self):
        self.register.D1.conductors.append(self.bus.conductors[3])
        self.register.D2.conductors.append(self.bus.conductors[2])
        self.register.D3.conductors.append(self.bus.conductors[1])
        self.register.D4.conductors.append(self.bus.conductors[0])

    def _connect_register_output(self):
        self.register.Q1.conductors.append(self.register_bus.conductors[3])
        self.register.Q2.conductors.append(self.register_bus.conductors[2])
        self.register.Q3.conductors.append(self.register_bus.conductors[1])
        self.register.Q4.conductors.append(self.register_bus.conductors[0])

    def evaluate(self):
        self.register.evaluate()


class RamModule:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            address_in: eater.part.Junction,
            memory_in: eater.part.Junction, memory_out: eater.part.Junction,
            bus: eater.part.Bus):

        # Register for storing the RAM address
        self.address_register = MemoryRegister(vcc, gnd, clr, clk, address_in, bus)

        # RAM module itself
        self.ram = eater.part.Ram()
        connect_power(vcc, gnd, self.ram)
        self.ram.CHIP_SELECT.conductors.append(gnd)
        self.ram.OUTPUT_ENABLE.conductors.append(memory_out)
        self.ram.A0.conductors.append(self.address_register.register_bus.conductors[0])
        self.ram.A1.conductors.append(self.address_register.register_bus.conductors[1])
        self.ram.A2.conductors.append(self.address_register.register_bus.conductors[2])
        self.ram.A3.conductors.append(self.address_register.register_bus.conductors[3])
        self.ram.IO0.conductors.append(bus.conductors[0])
        self.ram.IO1.conductors.append(bus.conductors[1])
        self.ram.IO2.conductors.append(bus.conductors[2])
        self.ram.IO3.conductors.append(bus.conductors[3])
        self.ram.IO4.conductors.append(bus.conductors[4])
        self.ram.IO5.conductors.append(bus.conductors[5])
        self.ram.IO6.conductors.append(bus.conductors[6])
        self.ram.IO7.conductors.append(bus.conductors[7])

        # NAND gate used to select write enable when clock and memory input  are high.
        self.clk_nand = eater.part.QuadNandGate()
        connect_power(vcc, gnd, self.clk_nand)
        self.clk_nand.A1.conductors.append(clk)
        self.clk_nand.B1.conductors.append(memory_in)
        self.clk_nand.Y1.conductors.append(self.ram.WRITE_ENABLE)

    def evaluate(self):
        self.clk_nand.evaluate()
        self.address_register.evaluate()
        self.ram.evaluate()

    def fiddle(self, address: int, data: int):
        self.ram.fiddle(address, data)


class ProgramCounter:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            counter_out: eater.part.Junction,
            counter_enable: eater.part.Junction,
            jump: eater.part.Junction,
            bus: eater.part.Bus):

        self.trans = eater.part.OctalBusTransceiver()
        self.counter = eater.part.BinaryCounter()

        connect_power(vcc, gnd, self.trans)
        connect_power(vcc, gnd, self.counter)

        self.counter.D1.conductors.append(bus.conductors[0])
        self.counter.D2.conductors.append(bus.conductors[1])
        self.counter.D3.conductors.append(bus.conductors[2])
        self.counter.D4.conductors.append(bus.conductors[3])

        self.counter.LOAD.conductors.append(jump)
        self.counter.ENABLE_P.conductors.append(counter_enable)
        self.counter.ENABLE_T.conductors.append(counter_enable)
        self.counter.CLR.conductors.append(clr)
        self.counter.CLK.conductors.append(clk)

        self.trans.B4.conductors.append(self.counter.Q4)
        self.trans.B5.conductors.append(self.counter.Q3)
        self.trans.B6.conductors.append(self.counter.Q2)
        self.trans.B7.conductors.append(self.counter.Q1)

        self.trans.ENABLED.conductors.append(counter_out)
        self.trans.DIRECTION.conductors.append(gnd)

        self.trans.A4.conductors.append(bus.conductors[3])
        self.trans.A5.conductors.append(bus.conductors[2])
        self.trans.A6.conductors.append(bus.conductors[1])
        self.trans.A7.conductors.append(bus.conductors[0])

    def evaluate(self):
        self.counter.evaluate()
        self.trans.evaluate()

    def __str__(self):
        return f"ProgramCounter(value={ self.counter.count })"


class Alu:
    def __init__(
            self,
            vcc: eater.part.Junction, gnd: eater.part.Junction,
            clr: eater.part.Junction, clk: eater.part.Junction,
            result_out: eater.part.Junction,
            subtract: eater.part.Junction,
            flags_in: eater.part.Junction,
            carry_out: eater.part.Junction,
            zero_out: eater.part.Junction,
            a_bus: eater.part.Bus,
            b_bus: eater.part.Bus,
            bus: eater.part.Bus):

        self.low_adder = eater.part.FourBitAdder()
        self.high_adder = eater.part.FourBitAdder()
        self.trans = eater.part.OctalBusTransceiver()
        self.flags_register = eater.part.FourBitDRegister()
        self.low_subtract_xor = eater.part.QuadXorGate()
        self.high_subtract_xor = eater.part.QuadXorGate()

        connect_power(vcc, gnd, self.low_adder)
        connect_power(vcc, gnd, self.high_adder)
        connect_power(vcc, gnd, self.trans)
        connect_power(vcc, gnd, self.flags_register)
        connect_power(vcc, gnd, self.low_subtract_xor)
        connect_power(vcc, gnd, self.high_subtract_xor)

        # Subtract line goes to carry in of low adder
        self.low_adder.CARRY_IN.conductors.append(subtract)

        # Connect carry bit of low register to carry in of high
        self.low_adder.CARRY_OUT.conductors.append(self.high_adder.CARRY_IN)

        # Carry bit of high register  goes into flags register.
        self.high_adder.CARRY_OUT.conductors.append(self.flags_register.D1)

        # Handle zero bit in software for the moment, instead of wiring up logic chips
        self._zero_bit = eater.part.VoltageSource(False)
        self.flags_register.D2.set(self._zero_bit)

        # Always enable flag output gates
        self.flags_register.N.conductors.append(gnd)
        self.flags_register.M.conductors.append(gnd)
        # Connect flags enable to flags_in
        self.flags_register.G1.conductors.append(flags_in)
        self.flags_register.G2.conductors.append(flags_in)
        # Connect clock and clear lines
        self.flags_register.CLK.conductors.append(clk)
        self.flags_register.CLR.conductors.append(clr)
        # Connect flag output lines
        self.flags_register.Q1.conductors.append(carry_out)
        self.flags_register.Q2.conductors.append(zero_out)

        # Connect subtract control line and B register output to xor gates
        xor_gates = self.low_subtract_xor.gates + self.high_subtract_xor.gates
        for gate, bus_line in zip(xor_gates, b_bus.conductors):
            gate.inputs[0].conductors.append(bus_line)
            gate.inputs[1].conductors.append(subtract)

        # Connect output of xor gate (register b, possibly inverted xorwise)
        for gate, adder_in in zip(xor_gates, self.low_adder.b + self.high_adder.b):
            gate.output.conductors.append(adder_in)

        # Connect a inputs of adders to output of register a
        for bus_conductor, adder_in in zip(a_bus.conductors, self.low_adder.a + self.high_adder.a):
            bus_conductor.conductors.append(adder_in)

        # Connect adder outputs to bus transceiver
        for (trans_in, _), (adder_out, _) in zip(self.trans.a, self.low_adder.sum + self.high_adder.sum):
            trans_in.conductors.append(adder_out)

        # Connect control lines to transceiver
        self.trans.DIRECTION.conductors.append(vcc)
        self.trans.ENABLED.conductors.append(result_out)

        # Connect transceiver outputs to bus
        self.trans.set_bus_b(bus)

    def evaluate(self):
        self.low_subtract_xor.evaluate()
        self.high_subtract_xor.evaluate()
        self.low_adder.evaluate()
        self.high_adder.evaluate()
        self.trans.evaluate()

        is_zero = not any([pin.state for pin, _ in self.low_adder.sum + self.high_adder.sum])
        self._zero_bit.value = is_zero
        self.flags_register.evaluate()


class Output:
    # Placeholder for the moment
    def __init__(
            self,
            clk: eater.part.Junction, clr: eater.part.Junction,
            output_enable: eater.part.Junction,
            bus: eater.part.Bus):
        self.clk = clk
        self.clr = clr
        self.output_enable = output_enable
        self.bus = bus
        self.value = 0

    def evaluate(self):
        if self.clr.state:
            self.value = 0
            return

        if self.clk.state and self.output_enable.state:
            self.value = eater.part.list_to_int([i or False for i in self.bus.value])
            print(f"Output: {self.value}\t{bin(self.value)}\t{hex(self.value)}")


class Control:
    def parse_mnemonic(self, line) -> Tuple[str, str]:
        split = line.strip().split()
        instruction = split[0]
        param = split[1] if len(split) > 1 else None
        return instruction, param

    program = """\
    LDA 14
    ADD 15
    OUT
    """

    def do_clock(self):
        self.clk.on()
        self.not_clk.off()

        self.pc.evaluate()
        self.ram.evaluate()
        self.instruction_register.evaluate()
        self.register_a.evaluate()
        self.register_b.evaluate()
        self.alu.evaluate()
        self.output.evaluate()

        self.clk.off()
        self.not_clk.on()

        self.pc.evaluate()
        self.instruction_register.evaluate()
        self.register_a.evaluate()
        self.register_b.evaluate()
        self.ram.evaluate()
        self.alu.evaluate()
        self.output.evaluate()

    def disable_all(self):
        self.clk.off()
        self.clr.off()
        self.not_clk.on()
        self.not_clr.on()

        self.address_in.on()
        self.memory_in.off()
        self.memory_out.on()
        self.instruction_out.on()
        self.instruction_in.on()
        self.counter_enable.off()
        self.counter_out.on()
        self.jump.on()
        self.result_out.on()
        self.subtract.off()
        self.flags_in.on()
        self.b_in.on()
        self.b_out.on()
        self.a_in.on()
        self.a_out.on()
        self.output_enable.off()

    def fetch(self):
        # Enable counter output and address input
        self.counter_out.off()
        self.address_in.off()
        self.do_clock()
        self.counter_out.on()
        self.address_in.on()

        # Enable RAM out and instruction register in
        self.memory_out.off()
        self.instruction_in.off()
        self.do_clock()
        self.memory_out.on()
        self.instruction_in.on()

        # Increment program counter
        self.counter_enable.on()
        self.do_clock()
        self.counter_enable.off()


    def __init__(self):
        self.vcc = eater.part.PoweredJunction(True)
        self.gnd = eater.part.PoweredJunction(False)

        self.clk = eater.part.PoweredJunction(False)
        self.clr = eater.part.PoweredJunction(False)
        # These inverted lines are just a convenience.
        # TODO: Wire up inverter.
        self.not_clk = eater.part.PoweredJunction(True)
        self.not_clr = eater.part.PoweredJunction(True)

        # Don't worry about the voltages here. We set them in disable_all()
        self.a_in = eater.part.PoweredJunction(True)
        self.a_out = eater.part.PoweredJunction(True)
        self.b_in = eater.part.PoweredJunction(True)
        self.b_out = eater.part.PoweredJunction(True)
        self.instruction_in = eater.part.PoweredJunction(True)
        self.instruction_out = eater.part.PoweredJunction(True)
        self.address_in = eater.part.PoweredJunction(True)
        self.memory_in = eater.part.PoweredJunction(True)
        self.memory_out = eater.part.PoweredJunction(True)
        self.result_out = eater.part.PoweredJunction(True)
        self.subtract = eater.part.PoweredJunction(True)
        self.flags_in = eater.part.PoweredJunction(True)
        self.carry_out = eater.part.PoweredJunction(True)
        self.zero_out = eater.part.PoweredJunction(True)
        self.output_enable = eater.part.PoweredJunction(True)
        self.counter_out = eater.part.PoweredJunction(True)
        self.counter_enable = eater.part.PoweredJunction(True)
        self.jump = eater.part.PoweredJunction(True)
        self.disable_all()

        self.bus = eater.part.Bus([eater.part.Junction() for _ in range(8)])
        self.instruction_bus = eater.part.Bus([eater.part.Junction() for _ in range(4)])

        self.register_a = Register(self.vcc, self.gnd, self.clr, self.clk, self.a_in, self.a_out, self.bus)
        self.register_b = Register(self.vcc, self.gnd, self.clr, self.clk, self.b_in, self.b_out, self.bus)
        self.instruction_register = InstructionRegister(self.vcc, self.gnd, self.clr, self.clk, self.instruction_in, self.instruction_out, self.instruction_bus, self.bus)
        self.output = Output(self.clk, self.clr, self.output_enable, self.bus)

        self.ram = RamModule(self.vcc, self.gnd, self.clr, self.clk, self.address_in, self.memory_in, self.memory_out, self.bus)
        self.alu = Alu(self.vcc, self.gnd, self.clr, self.clk, self.result_out, self.subtract, self.flags_in, self.carry_out, self.zero_out, self.register_a.register_bus, self.register_b.register_bus, self.bus)
        self.pc = ProgramCounter(self.vcc, self.gnd, self.not_clr, self.clk, self.counter_out, self.counter_enable, self.jump, self.bus)
