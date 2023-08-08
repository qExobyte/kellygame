import random

def coin_flip(probability) -> bool:
    flip_number = random.random()
    heads = False
    if flip_number <= probability:
        heads = True
    return heads

def get_growth_rate(initial, final, rounds):
    total_growth = (final - initial) / initial
    growth = ((1 + total_growth) ** (1/rounds) - 1) * 100
    growth = format(growth, ".2f")
    return growth