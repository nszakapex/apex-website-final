#!/usr/bin/env python3
"""
Apex redesign/v2 merge tool.

Splices the UNTOUCHED contact form + every script/noscript block (submit
handler, nav/menu/reveal JS, any tracking pixels) from the current live
index.html into the redesigned file. Nothing in the form is rewritten —
action, hidden inputs, field names, and the SMS consent block stay
byte-identical, which keeps lead capture and A2P 10DLC compliance intact.

Usage (from the repo root, next to your current index.html):

    python merge.py

Inputs : index.html            (your current live file — read only)
         index.redesign.html   (the new build)
Output : index.v2.html         (the merged, production-ready file)

Nothing is overwritten. Review index.v2.html, then on a branch:
    git checkout -b redesign/v2
    copy/move index.v2.html over index.html, commit, push, open a PR,
    and check the Netlify deploy preview before merging.
"""
import re
import sys

ORIG = sys.argv[1] if len(sys.argv) > 1 else "index.html"
NEW = sys.argv[2] if len(sys.argv) > 2 else "index.redesign.html"
OUT = sys.argv[3] if len(sys.argv) > 3 else "index.v2.html"

FORM_START = "<!-- APEX:FORM_SPLICE_START -->"
FORM_END = "<!-- APEX:FORM_SPLICE_END -->"
SCRIPTS_START = "<!-- APEX:SCRIPTS_SPLICE_START -->"
SCRIPTS_END = "<!-- APEX:SCRIPTS_SPLICE_END -->"

def die(msg):
    print(f"\n  ✗ {msg}")
    sys.exit(1)

def read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        die(f"Could not find {path} — run this from the repo root.")

orig = read(ORIG)
new = read(NEW)
checks = []

# ---- 1. extract the form, verbatim -------------------------------------
m = re.search(r"<form\b.*?</form>", orig, re.S | re.I)
if not m:
    die(f"No <form> found in {ORIG}.")
form = m.group(0)
checks.append(("form extracted", f"{len(form):,} bytes, untouched"))

# keep the v1 styling hook if the form element itself doesn't carry it
splice_form = form
if "contact-form" not in form[:300]:
    splice_form = f'<div class="contact-form">\n{form}\n</div>'
    checks.append(("form wrapper", "added .contact-form shell (form element lacked the class)"))

# ---- 2. extract every script + noscript block, in document order -------
blocks = [
    (m.start(), m.group(0))
    for m in re.finditer(r"<script\b.*?</script>|<noscript\b.*?</noscript>", orig, re.S | re.I)
]
blocks.sort(key=lambda b: b[0])
scripts = "\n".join(b[1] for b in blocks)
if not blocks:
    die(f"No <script> blocks found in {ORIG} — that can't be right for this site.")
checks.append(("legacy scripts", f"{len(blocks)} block(s) carried over verbatim"))

# ---- 3. splice ----------------------------------------------------------
for marker in (FORM_START, FORM_END, SCRIPTS_START, SCRIPTS_END):
    if new.count(marker) != 1:
        die(f"Marker missing or duplicated in {NEW}: {marker}")

def replace_between(doc, start, end, payload):
    a = doc.index(start) + len(start)
    b = doc.index(end)
    return doc[:a] + "\n" + payload + "\n" + doc[b:]

merged = replace_between(new, FORM_START, FORM_END, splice_form)
merged = replace_between(merged, SCRIPTS_START, SCRIPTS_END, scripts)

# ---- 4. shim any element ids the legacy scripts expect ------------------
wanted = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]", scripts))
wanted |= set(re.findall(r"querySelector(?:All)?\(\s*['\"]#([A-Za-z][\w-]*)['\"]", scripts))
have = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", merged))
missing = sorted(wanted - have)
if missing:
    shims = "\n".join(f'<span id="{i}" hidden></span>' for i in missing)
    merged = merged.replace(SCRIPTS_START, shims + "\n" + SCRIPTS_START)
    checks.append(("id shims", f"added hidden anchors for: {', '.join(missing)}"))
else:
    checks.append(("script targets", f"all {len(wanted)} referenced ids resolve — no shims needed"))

# ---- 5. verify ----------------------------------------------------------
m2 = re.search(r"<form\b.*?</form>", merged, re.S | re.I)
if not m2 or m2.group(0) != form:
    die("Form in merged output is not byte-identical to the original. Aborting.")
checks.append(("form integrity", "merged form is byte-identical to the live one"))

if "sms-consent" in orig and "sms-consent" not in merged:
    die("SMS consent block missing from merged output.")
checks.append(("A2P consent", "SMS consent block present" if "sms-consent" in merged else "n/a (none in original)"))

anchors = set(re.findall(r'href="#([\w-]+)"', merged))
dead = sorted(a for a in anchors if a not in have | {"contact"} and f'id="{a}"' not in merged)
if dead:
    die(f"Dead anchors in merged file: {dead}")
checks.append(("anchors", f"all {len(anchors)} in-page anchors resolve"))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(merged)

print(f"\n  Merged → {OUT} ({len(merged):,} bytes)\n")
for name, detail in checks:
    print(f"  ✓ {name}: {detail}")
print(
    "\n  Next:\n"
    "    1. python -m http.server 8080  → open the page, submit a test lead\n"
    "    2. git checkout -b redesign/v2\n"
    f"    3. replace index.html with {OUT}, commit, push, open a PR\n"
    "    4. review the Netlify deploy preview before merging to main\n"
)
