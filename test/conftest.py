import pytest

import eater.part


@pytest.fixture()
def vcc_rail() -> eater.part.Wire:
    return eater.part.Wire(True)


@pytest.fixture()
def gnd_rail() -> eater.part.Wire:
    return eater.part.Wire(False)
