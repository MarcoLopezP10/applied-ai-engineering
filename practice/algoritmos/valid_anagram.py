"""
Valid Anagram · NeetCode 150 · Arrays & Hashing
Patrón: dos palabras son anagramas si, ordenando sus letras, quedan iguales.
Complejidad: O(n log n) tiempo, O(n) espacio
"""


def valid_anagram(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    return sorted(s) == sorted(t)


if __name__ == "__main__":
    assert valid_anagram("anagram", "nagaram") is True
    assert valid_anagram("rat", "car") is False
    print("OK")
