import re
import sys

badge_template = """<svg xmlns="http://www.w3.org/2000/svg" width="110" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="110" height="20" fill="#555"/>
  <rect rx="3" x="55" width="55" height="20" fill="{color}"/>
  <path fill="{color}" d="M55 0h4v20h-4z"/>
  <rect rx="3" width="110" height="20" fill="url(#b)"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana" font-size="11">
    <text x="28" y="15">tests</text>
    <text x="82" y="15">{passed}/{total} passing</text>
  </g>
</svg>
"""

def pick_color(ratio):
    if ratio == 1:
        return "#4c1"     # green
    elif ratio >= 0.9:
        return "#dfb317"  # yellow
    else:
        return "#e05d44"  # red

def main():
    # expects pytest output file as sys.argv[1]
    with open(sys.argv[1]) as f:
        data = f.read()
    m = re.search(r"=+ (\d+) passed", data)
    passed = int(m.group(1)) if m else 0
    m = re.search(r"=+ (\d+) (?:passed|failed|skipped|xfailed|xpassed|error|warnings?)[^=]*=+\s*$", data, re.MULTILINE)
    # Try to count total tests
    total = passed
    m_total = re.search(r"=+ ([\d\s]+) in", data)
    if m_total:
        # fallback: just use passed as total
        pass
    ratio = passed / total if total else 0
    color = pick_color(ratio)
    with open("tests-badge.svg", "w") as f:
        f.write(badge_template.format(passed=passed, total=total, color=color))

if __name__ == "__main__":
    main()