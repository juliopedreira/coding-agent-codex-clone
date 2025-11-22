from calculator import add

def test_adds_integers():
    assert add(2, 3) == 5

def test_adds_negatives():
    assert add(-2, -3) == -5
