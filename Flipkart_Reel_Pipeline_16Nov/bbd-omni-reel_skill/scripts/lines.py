"""Compare what was SAID (whisper words, Devanagari or Latin) with what was SCRIPTED (romanised Hinglish).

Both sides are reduced to a consonant skeleton (Devanagari transliterated, aspiration/vowels dropped, digits to
English words), then aligned. Returns missing script words, extra spoken words (ad-libs), repeated phrases, and the
time span of the scripted speech - so a clip can be passed/failed and trimmed without a human listening.
"""
import difflib, re

DEV = {
    "अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ए": "e", "ऐ": "e", "ओ": "o", "औ": "o", "ऋ": "r",
    "क": "k", "ख": "k", "ग": "g", "घ": "g", "ङ": "n", "च": "c", "छ": "c", "ज": "j", "झ": "j", "ञ": "n",
    "ट": "t", "ठ": "t", "ड": "d", "ढ": "d", "ण": "n", "त": "t", "थ": "t", "द": "d", "ध": "d", "न": "n",
    "प": "p", "फ": "f", "ब": "b", "भ": "b", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "s", "ष": "s",
    "स": "s", "ह": "", "क़": "k", "ख़": "k", "ग़": "g", "ज़": "j", "ड़": "r", "ढ़": "r", "फ़": "f", "य़": "y",
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "e", "ो": "o", "ौ": "o", "ृ": "r",
    "ं": "n", "ँ": "n", "ः": "", "्": "", "़": "", "ॅ": "e", "ॉ": "o",
}
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine", "10": "ten", "13": "thirteen"}


def translit(w):
    w = re.sub(r"[।,.!?;:\"'()\-–—]", "", w.lower())
    if w in NUM:
        return NUM[w]
    if re.search(r"[ऀ-ॿ]", w):
        w = "".join(DEV.get(ch, ch) for ch in w)
    return w


SAME = {"par": "pe", "aur": "or", "toh": "to"}


def skel(w):
    """Consonant skeleton: robust to Hinglish spelling and Devanagari/Latin script choice."""
    w0 = re.sub(r"[^\w]", "", w.lower())
    if w0 in SAME:
        w = SAME[w0]
    latin = not re.search(r"[ऀ-ॿ]", w)
    w = translit(w)
    w = SAME.get(w, w)
    if latin:
        w = re.sub(r"g(?=[eiy])", "j", w)          # gym/gel -> j sound, as Devanagari writes it
        w = re.sub(r"c(?=[eiy])", "s", w)          # cement/city -> s
        w = re.sub(r"c(?![h])", "k", w)            # casual/cricket/campus -> k
    w = w.replace("ph", "f").replace("w", "v").replace("z", "j").replace("q", "k").replace("x", "ks")
    w = re.sub(r"(.)\1+", r"\1", w)
    k = re.sub(r"[aeiouhy\W_]", "", w)
    return k if k else "v"      # vowel-only fillers (hai/hi/ye/aa) share one token


def words_of(text):
    return [t for t in re.split(r"[\s\-–—]+", text) if re.sub(r"\W", "", t)]


def _eq(a, b):
    if a == b:
        return True
    a2, b2 = a.replace("j", "s"), b.replace("j", "s")
    if a2 == b2:
        return True
    return len(a) >= 2 and len(b) >= 2 and difflib.SequenceMatcher(None, a2, b2).ratio() >= 0.67


def merge_split(spoken, es):
    """Whisper splits brand words ('फ्लिप कार्ट'); join neighbours when the joined skeleton matches a script word."""
    out, i = [], 0
    while i < len(spoken):
        if i + 1 < len(spoken):
            j = skel(spoken[i][0] + spoken[i + 1][0])
            if any(_eq(j, e) for e in es) and not any(_eq(skel(spoken[i][0]), e) for e in es):
                out.append((spoken[i][0] + spoken[i + 1][0], spoken[i][1], spoken[i + 1][2])); i += 2; continue
        out.append(spoken[i]); i += 1
    return out


def compare(script_line, spoken):
    """script_line: romanised text. spoken: [(word, start, end)] from whisper.
    Returns dict(missing=[...], extra=[(text,t0,t1)], repeats=[(text,t0,t2)], first=t, last=t, ok=bool)."""
    exp = [w for w in words_of(script_line)]
    es = [skel(w) for w in exp]
    spoken = merge_split(spoken, es)
    ss = [skel(w) for w, _, _ in spoken]
    # map each spoken skeleton onto the closest expected skeleton so near-misspellings align
    canon = []
    for s in ss:
        best = max(es, key=lambda e: (s == e, s.replace("j", "s") == e.replace("j", "s"),
                                      difflib.SequenceMatcher(None, s.replace("j", "s"), e.replace("j", "s")).ratio())) if es else s
        canon.append(best if _eq(s, best) else "§" + s)
    sm = difflib.SequenceMatcher(None, es, canon, autojunk=False)
    missing, extra, matched, runs = [], [], [], [0]
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            matched += list(range(j1, j2))
        if op == "replace" and (i2 - i1) <= 2 and (j2 - j1) <= 2 and all(w[:1].isupper() for w in exp[i1:i2]):
            matched += list(range(j1, j2)); continue          # misheard brand name (Asics -> 'A6'): same slot
        if op in ("delete", "replace"):
            missing += exp[i1:i2]
            runs.append(sum(1 for w in exp[i1:i2] if skel(w) != "v"))
        if op == "insert" and j2 > j1:             # pure additions only; a 'replace' is a misheard script word
            extra.append((" ".join(w for w, _, _ in spoken[j1:j2]), spoken[j1][1], spoken[j2 - 1][2]))
    # back-to-back repeats of 1-4 words in what was spoken
    reps, n_ = [], [c for c in canon]
    for i in range(len(n_) - 1):                   # single word said twice ("sale sale") when the script has it once
        if n_[i] == n_[i + 1] and not n_[i].startswith("§") and n_[i] != "v" and len(n_[i]) >= 2 \
                and not any(es[k] == es[k + 1] == n_[i] for k in range(len(es) - 1)):
            reps.append((spoken[i][0], spoken[i][1], spoken[i + 1][1], spoken[i + 1][2]))
    for n in (4, 3, 2):
        for i in range(len(n_) - 2 * n + 1):
            if n_[i:i + n] == n_[i + n:i + 2 * n]:
                reps.append((" ".join(w for w, _, _ in spoken[i:i + n]), spoken[i][1], spoken[i + n][1], spoken[i + 2 * n - 1][2]))
    matched.sort()
    first = spoken[matched[0]][1] if matched else None
    last = spoken[matched[-1]][2] if matched else None
    # tolerate 1 short filler word (e.g. "hai") missing/extra; anything longer fails
    miss_real = [m for m in missing if skel(m) != "v"]
    extra_real = [e for e in extra if len(e[0].split()) >= 2 or len(skel(e[0])) >= 3]
    ok = len(miss_real) <= 1 and not extra_real and not reps
    return dict(missing=missing, extra=extra, repeats=reps, first=first, last=last, ok=ok, max_run=max(runs),
                coverage=round(1 - len(missing) / max(1, len(exp)), 2))
