import eater.assembly
import eater.part

def clock(register: eater.assembly.Register, clk: eater.part.Wire):
    clk.state = True
    register.evaluate()
    clk.state = False
    register.evaluate()


def test_register(vcc_rail: eater.part.Wire, gnd_rail: eater.part.Wire):
    reset = eater.part.Wire(False)
    address_in = eater.part.Wire(True)
    address_out = eater.part.Wire(True)
    clk = eater.part.Wire(False)

    bus = eater.part.Bus([eater.part.Wire(False) for _ in range(8)])

    register = eater.assembly.Register(bus, vcc_rail, gnd_rail, clk, address_in, address_out, reset)
    register.evaluate()

    print("hi")
