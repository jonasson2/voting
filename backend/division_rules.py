
import math

def dhondt_gen():
    """Generate a d'Hondt divider sequence: 1, 2, 3..."""
    n = 1.0
    while True:
        yield n
        n += 1.0

def sainte_lague_gen():
    """Generate a Sainte-Lague divider sequence: 1, 3, 5..."""
    n = 1.0
    while True:
        yield n
        n += 2.0

def nordic_sainte_lague_gen():
    """Generate a Nordic Sainte-Lague divide sequence: 1.4, 3, 5..."""
    yield 1.4
    n = 3.0
    while True:
        yield n
        n += 2.0

def danish_gen():
    """Generate Danish divider sequence: 1, 4, 7,..."""
    n = 1.0
    while True:
        yield n
        n += 3.0

def huntington_hill_gen():
    """Generate Hill-Huntington divider sequence; modified for hh(0) -> \inf"""
    n = 0
    yield 0.00000000001
    while True:
        n += 1
        yield math.sqrt(n*(n+1))

def adams_gen():
    """Generate Hill-Huntington divider sequence; modified for hh(0) -> \inf"""
    n = 0
    yield 0.00000000001
    while True:
        n += 1
        yield n


# Quota rules:

def droop(total_votes, total_seats):
    return total_votes/(total_seats+1)

def hare(total_votes, total_seats):
    return total_votes/total_seats
