from typing import List
from rapidfuzz import fuzz


CORPORATE_SUFFIXES = [
    'LLC', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO', 'LTD',
    'LP', 'LLP', 'PLC', 'PC', 'PLLC', 'P.C.'
]


COMMON_VARIATIONS = {
    'google': ['Google', 'Alphabet Inc', 'Google LLC', 'Google Client Services LLC', 'Alphabet'],
    'microsoft': ['Microsoft', 'Microsoft Corporation', 'Microsoft Corp', 'MSFT'],
    'apple': ['Apple', 'Apple Inc', 'Apple Computer', 'Apple Corp'],
    'amazon': ['Amazon', 'Amazon.com', 'AWS', 'Amazon Web Services', 'Amazon Inc'],
    'meta': ['Meta', 'Facebook', 'Meta Platforms', 'Facebook Inc', 'FACEBOOK'],
}


COMMON_MISSPELLINGS = {
    'google': ['gogle', 'googel', 'goolge'],
    'microsoft': ['mircosoft', 'microsft', 'microsofy'],
    'apple': ['appl', 'aple'],
    'amazon': ['amzon', 'amazom'],
    'facebook': ['facbook', 'facebbok'],
}


def normalize(name: str) -> str:
    if not name:
        return ''
    s = name.strip().upper().replace('.', '')
    for suf in CORPORATE_SUFFIXES:
        suf_up = ' ' + suf
        if s.endswith(suf_up):
            s = s[: -len(suf_up)]
            break
    return ' '.join(s.split())


def generate_variations(company_name: str, limit: int = 6) -> List[str]:
    base = company_name.strip()
    if not base:
        return []
    vars_: List[str] = [base, base.upper(), base.lower(), base.title()]
    n = normalize(base)
    if n and n.lower() != base.lower():
        vars_.append(n.title())
        for suf in ['LLC', 'Inc', 'Corporation', 'Corp']:
            vars_.append(f"{n.title()} {suf}")
    lower = base.lower()
    for k, vals in COMMON_VARIATIONS.items():
        if k in lower:
            vars_.extend(vals)
    for k, vals in COMMON_MISSPELLINGS.items():
        if k in lower:
            vars_.extend(vals)
    seen, out = set(), []
    for v in vars_:
        vv = v.strip()
        if vv and vv not in seen:
            seen.add(vv)
            out.append(vv)
    return out[:limit]


def similarity(a: str, b: str) -> float:
    aN, bN = normalize(a), normalize(b)
    if not aN or not bN:
        return 0.0
    return max(
        fuzz.ratio(aN, bN),
        fuzz.partial_ratio(aN, bN),
        fuzz.token_sort_ratio(aN, bN)
    ) / 100.0


