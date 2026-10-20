def poin_suhu(suhu: float) -> int:
    """Menghitung poin risiko berdasarkan suhu (derajat Celcius).

    - <= 28 C: 0 poin
    - 29 - 31 C: 1 poin
    - 32 - 35 C: 2 poin
    - > 35 C: 3 poin
    """
    if suhu <= 28:
        return 0
    elif suhu <= 31:
        return 1
    elif suhu <= 35:
        return 2
    return 3