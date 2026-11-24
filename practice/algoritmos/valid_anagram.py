def isAnagram(s: str, t: str) -> bool:
    if len(s)!=len(t):
        return False
    sr=sorted(s)
    tr=sorted(t)
    if sr == tr:
        return True
    else:
        return False