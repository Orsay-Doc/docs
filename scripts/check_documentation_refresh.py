#!/usr/bin/env python3
"""Deterministic checks for the approved documentation refresh."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEW_PAGES = (
    "fr/guides&tutorials/ai-sequence-builder",
    "en/guides&tutorials/ai-sequence-builder",
    "fr/guides&tutorials/export-conversations",
    "en/guides&tutorials/export-conversations",
)
EXPECTED_GUIDE_TITLES = {
    "fr/guides&tutorials/ai-sequence-builder.mdx": "✨ Créer une séquence avec l'IA",
    "en/guides&tutorials/ai-sequence-builder.mdx": "✨ Create a sequence with AI",
    "fr/guides&tutorials/export-conversations.mdx": "📤 Exporter des conversations",
    "en/guides&tutorials/export-conversations.mdx": "📤 Export conversations",
}
EXPECTED_GUIDE_SIDEBAR_TITLES = {
    "fr/guides&tutorials/ai-sequence-builder.mdx": "✨ Créer une séquence avec l'IA",
    "en/guides&tutorials/ai-sequence-builder.mdx": "✨ Create a sequence with AI",
    "fr/guides&tutorials/export-conversations.mdx": "📤 Exporter des conversations",
    "en/guides&tutorials/export-conversations.mdx": "📤 Export conversations",
}
EXPECTED_CHANGELOG_LINKS = {
    "fr/changelog.mdx": (
        "/fr/personal-whatsapp/3-sequence#voice-message-template",
        "/fr/guides&tutorials/voice-cloning#clone-your-voice",
        "/fr/guides&tutorials/ai-sequence-builder",
        "/fr/guides&tutorials/agents#resources",
        "/fr/overview/analytics#export",
        "/fr/guides&tutorials/export-conversations",
    ),
    "en/changelog.mdx": (
        "/en/personal-whatsapp/3-sequence#voice-message-template",
        "/en/guides&tutorials/voice-cloning#clone-your-voice",
        "/en/guides&tutorials/ai-sequence-builder",
        "/en/guides&tutorials/agents#resources",
        "/en/overview/analytics#export",
        "/en/guides&tutorials/export-conversations",
    ),
}
OBSOLETE_CHANGELOG_LINKS = {
    "fr/changelog.mdx": (
        "/fr/guides&tutorials/sequences#personal-whatsapp-audio",
        "/fr/guides&tutorials/sequences#build-with-ai",
        "/fr/guides&tutorials/conversations#export",
    ),
    "en/changelog.mdx": (
        "/en/guides&tutorials/sequences#personal-whatsapp-audio",
        "/en/guides&tutorials/sequences#build-with-ai",
        "/en/guides&tutorials/conversations#export",
    ),
}
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
BAD_ANCHOR_RE = re.compile(r"^#{1,6}\s+.+\s\[#[-A-Za-z0-9_]+\]\s*$")
EXPLICIT_ANCHOR_RE = re.compile(r"\s*\{#([-A-Za-z0-9_]+)\}\s*$")
LINK_RE = re.compile(r"\[[^\]]+\]\((/[^)]+)\)")


def slugify(title: str) -> str:
    title = EXPLICIT_ANCHOR_RE.sub("", title).lower()
    title = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", title).strip("-")


def anchors(path: Path) -> set[str]:
    result: set[str] = set()
    for match in HEADING_RE.finditer(path.read_text(encoding="utf-8")):
        heading = match.group(1)
        explicit = EXPLICIT_ANCHOR_RE.search(heading)
        result.add(explicit.group(1) if explicit else slugify(heading))
    return result


def check_link(link: str, source: str, errors: list[str]) -> None:
    route, _, fragment = link.partition("#")
    target = ROOT / (route.lstrip("/") + ".mdx")
    if not target.is_file():
        errors.append(f"{source}: missing link target {route}")
    elif fragment and fragment not in anchors(target):
        errors.append(f"{source}: missing fragment #{fragment} in {route}")


def main() -> int:
    errors: list[str] = []
    mdx_files = sorted(ROOT.rglob("*.mdx"))
    for path in mdx_files:
        rel = path.relative_to(ROOT)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if BAD_ANCHOR_RE.fullmatch(line):
                errors.append(f"{rel}:{line_number}: heading ends with invalid [#id] anchor")

    config = json.loads((ROOT / "docs.json").read_text(encoding="utf-8"))
    nav_pages = {
        page
        for dropdown in config["navigation"]["dropdowns"]
        for group in dropdown["groups"]
        for page in group["pages"]
    }
    for route in NEW_PAGES:
        if not (ROOT / f"{route}.mdx").is_file():
            errors.append(f"missing required page {route}.mdx")
        if route not in nav_pages:
            errors.append(f"missing navigation entry {route}")

    if not (ROOT / "en/home.mdx").is_file():
        errors.append("missing locale-explicit English home en/home.mdx")
    if "en/home" not in nav_pages:
        errors.append("English home navigation must use en/home")
    if "index" in nav_pages:
        errors.append("English home navigation must not use the root index route")

    redirects = {
        (redirect["source"], redirect["destination"])
        for redirect in config.get("redirects", [])
    }
    for redirect in (("/", "/fr/home"), ("/index", "/fr/home")):
        if redirect not in redirects:
            errors.append(f"missing French root redirect {redirect[0]} -> {redirect[1]}")

    css = (ROOT / "custom.css").read_text(encoding="utf-8")
    css_rules = re.findall(r"([^{}]+)\{([^}]*)\}", css, re.DOTALL)
    cta_outer_declarations = [
        declarations
        for selectors, declarations in css_rules
        if "#topbar-cta-button" in (selector.strip() for selector in selectors.split(","))
    ]
    if any("background-color" in declarations for declarations in cta_outer_declarations):
        errors.append("custom.css: CTA background must not be applied to the outer list item")
    cta_surface_rule = re.search(r"#topbar-cta-button\s*>\s*a\s*\{([^}]*)\}", css, re.DOTALL)
    if not cta_surface_rule:
        errors.append("custom.css: missing direct CTA anchor rule")
    else:
        declarations = cta_surface_rule.group(1)
        if "background-color: transparent" not in declarations:
            errors.append("custom.css: direct CTA anchor background must be transparent")
        if "color: #ffffff" not in declarations:
            errors.append("custom.css: direct CTA anchor is missing white text")
    cta_rounded_surface_rule = re.search(
        r"#topbar-cta-button\s*>\s*a\s*>\s*span\.absolute\.inset-0\s*\{([^}]*)\}",
        css,
        re.DOTALL,
    )
    if not cta_rounded_surface_rule:
        errors.append("custom.css: missing nested rounded CTA surface rule")
    elif "background-color: var(--orsay-link)" not in cta_rounded_surface_rule.group(1):
        errors.append("custom.css: nested rounded CTA surface is missing its brand background")

    for source, expected_title in EXPECTED_GUIDE_TITLES.items():
        text = (ROOT / source).read_text(encoding="utf-8")
        if f'title: "{expected_title}"' not in text:
            errors.append(f'{source}: expected title "{expected_title}"')

    for source, expected_sidebar_title in EXPECTED_GUIDE_SIDEBAR_TITLES.items():
        text = (ROOT / source).read_text(encoding="utf-8")
        if f'sidebarTitle: "{expected_sidebar_title}"' not in text:
            errors.append(
                f'{source}: expected sidebarTitle "{expected_sidebar_title}"'
            )

    for source, expected_links in EXPECTED_CHANGELOG_LINKS.items():
        text = (ROOT / source).read_text(encoding="utf-8")
        for link in expected_links:
            if f"]({link})" not in text:
                errors.append(f"{source}: missing exact changelog destination {link}")
            check_link(link, source, errors)
        for link in OBSOLETE_CHANGELOG_LINKS[source]:
            if f"]({link})" in text:
                errors.append(f"{source}: obsolete changelog destination remains {link}")

    scoped_files = {f"{route}.mdx" for route in NEW_PAGES}
    for source in sorted(scoped_files):
        path = ROOT / source
        if not path.is_file():
            continue
        for link in LINK_RE.findall(path.read_text(encoding="utf-8")):
            check_link(link, source, errors)

    for faq in ("fr/resources/faq.mdx", "en/resources/faq.mdx"):
        try:
            baseline = subprocess.run(
                ["git", "show", f"origin/main:{faq}"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"cannot compare {faq} with origin/main: {exc}")
        else:
            if (ROOT / faq).read_bytes() != baseline:
                errors.append(f"{faq}: differs from origin/main")

    if errors:
        print(f"FAIL: {len(errors)} documentation refresh check(s) failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: documentation refresh checks are green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
