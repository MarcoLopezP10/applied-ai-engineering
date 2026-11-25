"""
Contains Duplicate · NeetCode 150 · Arrays & Hashing
Patrón: recorrer la lista guardando lo ya visto en un set; si un número ya está, hay duplicado.
Complejidad: O(n) tiempo, O(n) espacio
"""


def contains_duplicate(nums: list[int]) -> bool:
    seen = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False


if __name__ == "__main__":
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3, 4]) is False
    print("OK")
