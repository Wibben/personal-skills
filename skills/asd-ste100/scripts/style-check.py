#!/usr/bin/env python3
"""Check prose against the house rules of the asd-ste100 skill.

Complements ste-lint.py, which covers the ASD-STE100 structural rules. This
script covers the house rules that are mechanical to check:

  spelling      Canadian or American spelling, decided per document
  latin         Latin abbreviations (Google style)
  directional   "above" / "below" as references to document content
  timeless      time-sensitive words such as "currently" and "soon"
  clutter       words that do no work (Zinsser, Google)
  inclusive     non-inclusive terms (Google)
  heading       headings in title case or ending in a period (Google)
  exclaim       exclamation marks in prose

Fenced code blocks, inline code spans, and URLs are skipped. The spelling
variant is Canadian unless the document already uses American spelling and no
Canadian spelling. A mixed document takes the majority variant (Canadian on a
tie), and every word in the minority variant is reported.

Usage: style-check.py [--json] [--variant auto|canadian|american]
                      [--disable RULE,...] [FILE ...]
Reads stdin when no FILE is given. Exit 1 when there are findings.
"""

import argparse
import json
import re
import sys

# American -> Canadian. Each entry is (american_stem, canadian_stem, suffixes).
# The suffix list is explicit so that words such as "honorary" and "humorous",
# which have no "u" in Canadian English either, never match.
_OUR = ("", "s", "ed", "ing", "ful", "fully", "less", "able", "ably", "al",
        "ally", "ite", "ites", "er", "ers")
SPELLING_STEMS = [
    ("color", "colour", _OUR), ("behavior", "behaviour", _OUR),
    ("favor", "favour", _OUR), ("honor", "honour", _OUR),
    ("labor", "labour", _OUR), ("neighbor", "neighbour", _OUR + ("hood", "hoods", "ing")),
    ("flavor", "flavour", _OUR), ("harbor", "harbour", _OUR),
    ("rumor", "rumour", _OUR), ("vapor", "vapour", _OUR),
    ("armor", "armour", _OUR), ("endeavor", "endeavour", _OUR),
    ("odor", "odour", _OUR), ("humor", "humour", ("", "s", "ed", "ing", "less")),
    ("center", "centre", ("", "s")), ("centered", "centred", ("",)),
    ("centering", "centring", ("",)), ("fiber", "fibre", ("", "s")),
    ("liter", "litre", ("", "s")), ("theater", "theatre", ("", "s")),
    ("caliber", "calibre", ("", "s")), ("maneuver", "manoeuvre", ("", "s", "d")),
    ("defense", "defence", ("", "s", "less")), ("offense", "offence", ("", "s")),
    ("pretense", "pretence", ("", "s")), ("catalog", "catalogue", ("", "s", "d")),
    ("gray", "grey", ("", "s", "ed", "ing", "ish")),
    ("jewelry", "jewellery", ("",)),
]
for _base in ("travel", "cancel", "label", "model", "signal", "level", "fuel",
              "total", "tunnel", "channel", "marshal", "funnel", "counsel"):
    SPELLING_STEMS.append((_base + "ed", _base + "led", ("",)))
    SPELLING_STEMS.append((_base + "ing", _base + "ling", ("",)))
SPELLING_STEMS.append(("traveler", "traveller", ("", "s")))

LATIN = {
    r"e\.\s?g\.": "for example", r"i\.\s?e\.": "that is",
    r"etc\.": "and so on", r"via": "through, by, or using",
    r"vs\.?": "versus or compared with", r"cf\.": "see or compare",
    r"et al\.": "and others", r"n\.\s?b\.": "note",
}
DIRECTIONAL = r"\b(?:the|see|shown|listed|described|mentioned|noted|as|example|table|figure|section|list|steps|code|command)\s+(above|below)\b|\babove-mentioned\b"
TIMELESS = ["currently", "presently", "soon", "at the time of writing",
            "as of this writing", "at this time", "in the future"]
CLUTTER = {
    "please": "", "simply": "", "just": "", "easy": "", "easily": "",
    "basically": "", "actually": "", "very": "", "really": "", "quite": "",
    "obviously": "", "clearly": "", "of course": "", "note that": "",
    "in order to": "to", "utilize": "use", "utilizes": "uses",
    "utilization": "use", "at this point in time": "now",
    "due to the fact that": "because", "prior to": "before",
    "in the event that": "if", "is able to": "can", "are able to": "can",
    "a number of": "some, or the number", "whether or not": "whether",
    "it is important to": "",
}
INCLUSIVE = {
    "whitelist": "allowlist", "blacklist": "denylist",
    "whitelisted": "allowed", "blacklisted": "denied", "master": "primary or main",
    "slave": "replica, secondary, or subordinate", "sanity check": "check or quick check",
    "sanity-check": "check", "dummy": "placeholder or sample",
    "grandfathered": "legacy or exempt", "man-hours": "person-hours",
    "manpower": "workforce or staff", "crippled": "impaired or degraded",
}
SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "if", "in",
               "nor", "of", "on", "or", "so", "the", "to", "up", "vs", "with"}

RULE_IDS = ("spelling", "latin", "directional", "timeless", "clutter",
            "inclusive", "heading", "exclaim")


def _phrase_re(phrase):
    return re.compile(r"\b" + phrase.replace(" ", r"\s+") + r"\b", re.IGNORECASE)


def _prose_lines(text):
    """Yield (line_number, line) with code and URLs blanked out."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in ("```", "~~~"):
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is not None:
            continue
        line = re.sub(r"`[^`]*`", " ", line)
        line = re.sub(r"\]\([^)]*\)|https?://\S+|<[^>\s]+>", " ", line)
        yield number, line


def _spelling_patterns():
    american, canadian = [], []
    for us_stem, ca_stem, suffixes in SPELLING_STEMS:
        group = "(?:" + "|".join(re.escape(s) for s in suffixes) + ")"
        american.append((re.compile(r"\b" + us_stem + group + r"\b", re.IGNORECASE), us_stem, ca_stem))
        canadian.append((re.compile(r"\b" + ca_stem + group + r"\b", re.IGNORECASE), ca_stem, us_stem))
    return american, canadian


def lint(text, filename, variant, disabled):
    findings = []
    lines = list(_prose_lines(text))

    def add(rule, number, message):
        if rule not in disabled:
            findings.append({"file": filename, "line": number, "rule": rule, "message": message})

    american, canadian = _spelling_patterns()
    hits = {"american": [], "canadian": []}
    for number, line in lines:
        for name, patterns in (("american", american), ("canadian", canadian)):
            for pattern, _, other in patterns:
                for match in pattern.finditer(line):
                    hits[name].append((number, match.group(0), other))
    if variant == "auto":
        variant = "american" if len(hits["american"]) > len(hits["canadian"]) else "canadian"
    minority = "canadian" if variant == "american" else "american"
    for number, word, other in hits[minority]:
        add("spelling", number, f'"{word}" is {minority} spelling; this document uses '
            f'{variant} (stem "{other}")')

    latin = [(re.compile(r"(?<![\w.])" + pattern + r"(?!\w)", re.IGNORECASE), fix)
             for pattern, fix in LATIN.items()]
    directional = re.compile(DIRECTIONAL, re.IGNORECASE)
    timeless = [_phrase_re(phrase) for phrase in TIMELESS]
    clutter = [(_phrase_re(phrase), phrase, fix) for phrase, fix in CLUTTER.items()]
    inclusive = [(_phrase_re(term), term, fix) for term, fix in INCLUSIVE.items()]

    for number, line in lines:
        for pattern, fix in latin:
            for match in pattern.finditer(line):
                add("latin", number, f'"{match.group(0)}": use "{fix}"')
        for match in directional.finditer(line):
            add("directional", number, f'"{match.group(0)}": use "preceding" or "following"')
        for pattern in timeless:
            for match in pattern.finditer(line):
                add("timeless", number, f'"{match.group(0)}" goes stale; state the version or date, or delete it')
        for pattern, phrase, fix in clutter:
            if pattern.search(line):
                add("clutter", number, f'"{phrase}": ' + (f'use "{fix}"' if fix else "delete it"))
        for pattern, term, fix in inclusive:
            if pattern.search(line):
                add("inclusive", number, f'"{term}": use "{fix}"')
        heading = re.match(r"\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if heading:
            words = re.findall(r"[A-Za-z][\w'-]*", heading.group(1))
            later = [w for w in words[1:] if w.lower() not in SMALL_WORDS and not w.isupper()]
            if len(later) >= 2 and sum(w[0].isupper() for w in later) > len(later) / 2:
                add("heading", number, "heading looks like title case; use sentence case")
            if heading.group(1).endswith("."):
                add("heading", number, "heading ends with a period")
        elif re.search(r"\w!(\s|$)", line):
            add("exclaim", number, "exclamation mark in prose")
    return variant, findings


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", metavar="FILE")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--variant", choices=("auto", "canadian", "american"), default="auto",
                        help="spelling variant (default: decide per document)")
    parser.add_argument("--disable", default="", metavar="RULES",
                        help="comma-separated rule ids: " + ", ".join(RULE_IDS))
    args = parser.parse_args(argv)
    disabled = {rule.strip() for rule in args.disable.split(",") if rule.strip()}
    unknown = disabled - set(RULE_IDS)
    if unknown:
        parser.error("unknown rule(s): " + ", ".join(sorted(unknown)))

    sources = [(path, open(path, encoding="utf-8").read()) for path in args.paths] \
        or [("<stdin>", sys.stdin.read())]
    results, all_findings = [], []
    for filename, text in sources:
        variant, findings = lint(text, filename, args.variant, disabled)
        results.append({"file": filename, "variant": variant, "findings": findings})
        all_findings.extend(findings)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f'{result["file"]}: spelling variant: {result["variant"]}')
            for f in sorted(result["findings"], key=lambda f: f["line"]):
                print(f'{f["file"]}:{f["line"]}: {f["rule"]}: {f["message"]}')
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
