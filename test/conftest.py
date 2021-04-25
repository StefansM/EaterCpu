import pytest

import eater.part


@pytest.fixture()
def vcc_rail() -> eater.part.Junction:
    return eater.part.Junction(True)


@pytest.fixture()
def gnd_rail() -> eater.part.Junction:
    return eater.part.Junction(False)
