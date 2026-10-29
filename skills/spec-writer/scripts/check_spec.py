#!/usr/bin/env python3
"""Structural check for a spec written from assets/spec-template.md.

Usage:  python3 scripts/check_spec.py <spec.md>

Checks what a reader can verify mechanically: size chosen, required sections present and in order,
every gap (G#) covered by an acceptance criterion (AC#) and vice versa, ACs complete and free of
vague words, decisions have a state, label legend present, leftover template placeholders.
It cannot judge whether the content is *true* or *good* - that is the spec review's job.

Exit code: 0 = no errors (warnings allowed), 1 = errors found, 2 = usage / file problem.
Standard library only.
"""
import re
import sys

# ---- profile: spec-writer (general) -------------------------------------------------------------
PROFILE = "spec-writer"
REQUIRED = {  # section numbers required per size
    "Short": [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13],
    "Full": list(range(0, 14)),
}
GAPS_SECTION, AC_SECTION, DECISIONS_SECTION = 4, 8, 7
DECISION_STATES = ("decided", "recommended", "open")
REQUIRE_LEGEND = True
LABEL_SECTIONS = (2, 3)  # bullet lines here should carry a label
LABELS = ("✅", "🗣", "❓")
VERIFIED_SECTION = None          # section whose title must say "verified on `<branch>`, YYYY-MM-DD"
CITATION_SECTION = None          # section that must cite code as path/file.ext:line
CHECK_MIGRATION_PROVISIONAL = False
# --------------------------------------------------------------------------------------------------

VAGUE = ("fast", "quick", "easy", "user-friendly", "user friendly", "intuitive", "seamless",
         "appropriate", "appropriately", "etc", "as needed", "works well", "properly", "robust")
SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$", re.M)
SUB_RE = re.compile(r"^###\s+(\d+)\.(\d+)\b", re.M)


def sections(text):
    found = list(SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        out.append((int(m.group(1)), m.group(2).strip(), text[m.end():end]))
    return out


def table_rows(body, prefix):
    return [ln for ln in body.splitlines() if re.match(rf"^\|\s*{prefix}\d+\s*\|", ln)]


def main(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"error: cannot read {path}: {e}")
        return 2
    errors, warnings = [], []
    secs = sections(text)
    by_num = {n: (title, body) for n, title, body in secs}

    # size
    m = re.search(r"\*\*Size:\*\*\s*([A-Za-z]+)(\s*\|)?", text)
    if not m:
        errors.append("No '**Size:** Short|Full' line in the header.")
        size = "Full"
    elif m.group(2) or m.group(1) not in REQUIRED:
        errors.append("Size not chosen - write 'Short' or 'Full', not 'Short | Full'.")
        size = "Full"
    else:
        size = m.group(1)

    # sections present and ordered
    nums = [n for n, _, _ in secs]
    if nums != sorted(nums):
        errors.append(f"Sections out of order: {nums}")
    for n in REQUIRED[size]:
        if n not in by_num:
            errors.append(f"Missing required section '## {n}.' for a {size} spec "
                          "(write 'None' rather than deleting it).")
    for n, _, body in secs:
        subs = [(int(a), int(b)) for a, b in SUB_RE.findall(body)]
        if any(a != n for a, _ in subs):
            errors.append(f"§{n} has subsections numbered for another section: {subs}")
        if [b for _, b in subs] != sorted(b for _, b in subs):
            errors.append(f"§{n} subsections out of order: {[f'{a}.{b}' for a, b in subs]}")

    # gaps and ACs
    gaps = set()
    if GAPS_SECTION in by_num:
        gaps = {int(g) for row in table_rows(by_num[GAPS_SECTION][1], "G")
                for g in re.findall(r"^\|\s*G(\d+)", row)}
        if not gaps:
            errors.append(f"§{GAPS_SECTION} has no numbered gaps (| G1 | ...).")
    acs = {}
    if AC_SECTION in by_num:
        for row in table_rows(by_num[AC_SECTION][1], "AC"):
            ac = int(re.match(r"^\|\s*AC(\d+)", row).group(1))
            acs[ac] = row
        if not acs:
            errors.append(f"§{AC_SECTION} has no numbered acceptance criteria (| AC1 | ...).")
    covered = set()
    for ac, row in acs.items():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        refs = {int(g) for g in re.findall(r"\bG(\d+)\b", row)}
        if not refs and not re.search(r"\bR\d+\b", row):
            errors.append(f"AC{ac} does not name the gap (G#) or rule (R#) it covers.")
        for g in refs - gaps:
            errors.append(f"AC{ac} covers G{g}, which is not in the gaps table.")
        covered |= refs
        if any(c == "" for c in cells[1:]):
            errors.append(f"AC{ac} has empty cells.")
        low = row.lower()
        hits = [w for w in VAGUE if re.search(rf"\b{re.escape(w)}\b", low)]
        if hits:
            errors.append(f"AC{ac} uses vague wording {hits} - state an observable result.")
    for g in sorted(gaps - covered):
        errors.append(f"G{g} has no acceptance criterion.")

    # decisions
    if DECISIONS_SECTION in by_num:
        body = by_num[DECISIONS_SECTION][1]
        rows = table_rows(body, "D")
        if not rows and "none" not in body.lower():
            warnings.append(f"§{DECISIONS_SECTION} has no D# rows and doesn't say 'None'.")
        for row in rows:
            d = re.match(r"^\|\s*D(\d+)", row).group(1)
            if not any(s in row.lower() for s in DECISION_STATES):
                errors.append(f"D{d} has no state ({' / '.join(DECISION_STATES)}).")

    # labels
    if REQUIRE_LEGEND and not all(l in text.split("## 0.")[0] for l in LABELS):
        errors.append("Header lacks the label legend line (✅ / 🗣 / ❓).")
    for n in LABEL_SECTIONS:
        if n in by_num:
            bare = [ln.strip() for ln in by_num[n][1].splitlines()
                    if ln.strip().startswith("- ") and not any(l in ln for l in LABELS)
                    and not re.match(r"- \*\*(Who|Goal|Today|Project rules)\b", ln.strip())]
            if bare:
                warnings.append(f"§{n}: {len(bare)} bullet(s) without a ✅/🗣/❓ label, e.g. '{bare[0][:70]}'")

    # codebase-grounding checks (project profiles)
    if VERIFIED_SECTION is not None and VERIFIED_SECTION in by_num:
        title = by_num[VERIFIED_SECTION][0]
        if not re.search(r"verified on `[^`]+`.*\d{4}-\d{2}-\d{2}", title):
            errors.append(f"§{VERIFIED_SECTION} title must read 'verified on `<branch>`, YYYY-MM-DD'.")
    if CITATION_SECTION is not None and CITATION_SECTION in by_num:
        if not re.search(r"[\w./-]+\.\w+:\d+", by_num[CITATION_SECTION][1]):
            errors.append(f"§{CITATION_SECTION} cites no code location (path/file.ext:line).")
    if CHECK_MIGRATION_PROVISIONAL:
        for mig in sorted(set(re.findall(r"\b(\d{4})_\w+\.sql\b", text))):
            if "provisional" not in text.lower():
                errors.append(f"Migration {mig} is named but not marked provisional.")
                break

    # leftovers
    placeholders = re.findall(r"<(?!!--)[A-Za-z][^<>\n]{0,60}>", re.sub(r"<!--.*?-->", "", text, flags=re.S))
    if placeholders:
        warnings.append(f"{len(placeholders)} template placeholder(s) left, e.g. {placeholders[:3]}")
    if re.search(r"\bTBD\b|\bTODO\b", text):
        warnings.append("Contains TBD/TODO.")

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"check_spec ({PROFILE}): {size} spec, {len(gaps)} gaps, {len(acs)} ACs - "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
