from services.risiko import poin_suhu


def test_poin_suhu():
    assert poin_suhu(28) == 0
    assert poin_suhu(31) == 1
    assert poin_suhu(34) == 2
    assert poin_suhu(36) == 3
    