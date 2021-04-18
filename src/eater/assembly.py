from typing import List

import eater.part


def attach_power(vcc: eater.part.Wire, gnd: eater.part.Wire, part: eater.part.Part):
    # TODO: Fix types for VCC, GND
    part.pins[part.VCC].conductors.append(vcc)
    part.pins[part.GND].conductors.append(gnd)


def attach(device1: eater.part.Part, pin1: int, device2: eater.part.Part, pin2: int):
    wire = eater.part.Wire()
    device1.pins[pin1].conductors.append(wire)
    device2.pins[pin2].conductors.append(wire)


class Register:
    def __init__(self, bus: eater.part.Bus,
                 vcc: eater.part.Wire, gnd: eater.part.Wire, clk: eater.part.Wire,
                 address_in: eater.part.Wire, address_out: eater.part.Wire,
                 reset: eater.part.Wire):
        self.bus = bus
        self.transceiver = eater.part.OctalBusTransceiver()
        self.low_register = eater.part.FourBitDRegister()
        self.high_register = eater.part.FourBitDRegister()

        self.register_out = eater.part.Bus([eater.part.Wire() for _ in range(8)])

        attach_power(vcc, gnd, self.transceiver)
        attach_power(vcc, gnd, self.low_register)
        attach_power(vcc, gnd, self.high_register)

        self.transceiver.pins[self.transceiver.ENABLED_INVERTED].conductors.append(address_out)
        self.transceiver.pins[self.transceiver.DIRECTION].conductors.append(vcc)

        self.transceiver.pins[self.transceiver.B1].conductors.append(bus.conductors[7])
        self.transceiver.pins[self.transceiver.B2].conductors.append(bus.conductors[6])
        self.transceiver.pins[self.transceiver.B3].conductors.append(bus.conductors[5])
        self.transceiver.pins[self.transceiver.B4].conductors.append(bus.conductors[4])
        self.transceiver.pins[self.transceiver.B5].conductors.append(bus.conductors[3])
        self.transceiver.pins[self.transceiver.B6].conductors.append(bus.conductors[2])
        self.transceiver.pins[self.transceiver.B7].conductors.append(bus.conductors[1])
        self.transceiver.pins[self.transceiver.B8].conductors.append(bus.conductors[0])

        self._attach_control_lines(self.low_register, gnd, clk, address_in, reset)
        self._attach_control_lines(self.high_register, gnd, clk, address_in, reset)

        self.high_register.pins[self.high_register.D4].conductors.append(bus.conductors[4])
        self.high_register.pins[self.high_register.D3].conductors.append(bus.conductors[5])
        self.high_register.pins[self.high_register.D2].conductors.append(bus.conductors[6])
        self.high_register.pins[self.high_register.D1].conductors.append(bus.conductors[7])

        attach(self.high_register, self.high_register.D1, self.transceiver, self.transceiver.A1)
        attach(self.high_register, self.high_register.D2, self.transceiver, self.transceiver.A2)
        attach(self.high_register, self.high_register.D3, self.transceiver, self.transceiver.A3)
        attach(self.high_register, self.high_register.D4, self.transceiver, self.transceiver.A4)

        self.low_register.pins[self.low_register.D4].conductors.append(bus.conductors[0])
        self.low_register.pins[self.low_register.D3].conductors.append(bus.conductors[1])
        self.low_register.pins[self.low_register.D2].conductors.append(bus.conductors[2])
        self.low_register.pins[self.low_register.D1].conductors.append(bus.conductors[3])

        attach(self.low_register, self.low_register.D1, self.transceiver, self.transceiver.A5)
        attach(self.low_register, self.low_register.D2, self.transceiver, self.transceiver.A6)
        attach(self.low_register, self.low_register.D3, self.transceiver, self.transceiver.A7)
        attach(self.low_register, self.low_register.D4, self.transceiver, self.transceiver.A8)

    def value(self):
        return self.high_register.value() + self.low_register.value()

    def __str__(self):
        return "Register[" + "".join(["1" if v else "0" for v in self.value()]) + "]"

    def evaluate(self):
        self.low_register.evaluate()
        self.high_register.evaluate()
        self.transceiver.evaluate()

    def _attach_control_lines(
            self,
            register: eater.part.FourBitDRegister,
            gnd: eater.part.Wire, clk: eater.part.Wire,
            address_in: eater.part.Wire,
            reset: eater.part.Wire):
        register.pins[register.CLR].conductors.append(reset)
        register.pins[register.CLK].conductors.append(clk)
        register.pins[register.G1].conductors.append(address_in)
        register.pins[register.G2].conductors.append(address_in)
        register.pins[register.M].conductors.append(gnd)
        register.pins[register.N].conductors.append(gnd)
