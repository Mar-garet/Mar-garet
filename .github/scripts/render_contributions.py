"""Build contribution cards from official logos and current GitHub star counts."""

import argparse
import base64
import json
import struct
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "contributions"
THEMES = {
    "light": {"surface": "#ffffff", "border": "#d1d9e0", "text": "#1f2328", "muted": "#59636e"},
    "dark": {"surface": "#161b22", "border": "#3d444d", "text": "#f0f6fc", "muted": "#9198a1"},
}


def logo_image(filename: str) -> str:
    """Fit an unchanged original logo into a centered 40-pixel square."""
    path = ASSETS / filename
    data = path.read_bytes()
    if path.suffix == ".svg":
        viewbox = ET.fromstring(data).attrib["viewBox"].split()
        width, height = float(viewbox[2]), float(viewbox[3])
        media_type = "image/svg+xml"
    else:
        width, height = struct.unpack(">II", data[16:24])
        media_type = "image/png"
    scale = 40 / max(width, height)
    width, height = width * scale, height * scale
    x, y = 18 + (40 - width) / 2, 22 + (40 - height) / 2
    encoded = base64.b64encode(data).decode("ascii")
    return (
        f'<image x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'href="data:{media_type};base64,{encoded}" />'
    )


def render_card(name: str, logo: str, stars: int, theme: str) -> str:
    palette = THEMES[theme]
    title = escape(f"{name}: {stars:,} GitHub stars")
    star = (ASSETS / "star.svg").read_text()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="274" height="96" viewBox="0 0 274 96" role="img" aria-labelledby="title">
  <title id="title">{title}</title>
  <rect x="0.5" y="0.5" width="259" height="83" rx="10" fill="{palette['surface']}" stroke="{palette['border']}" />
  {logo_image(logo)}
  <text x="76" y="34" fill="{palette['text']}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif" font-size="16" font-weight="600">{escape(name)}</text>
  <g transform="translate(76 45) scale(0.667)" color="{palette['muted']}">{star}</g>
  <text x="99" y="58" fill="{palette['muted']}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif" font-size="13">{stars:,} stars</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    projects = json.loads((ASSETS / "projects.json").read_text())

    counts = {}
    for project in projects:
        response = subprocess.run(
            ["gh", "api", f"repos/{project['repo']}", "--jq", ".stargazers_count"],
            check=True,
            capture_output=True,
            text=True,
        )
        stars = int(response.stdout.strip())
        if stars < 0:
            raise ValueError(f"Invalid star count for {project['repo']}")
        counts[project["repo"]] = stars

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for project in projects:
        for theme in THEMES:
            logo = project.get("dark_logo", project["logo"]) if theme == "dark" else project["logo"]
            card = render_card(project["name"], logo, counts[project["repo"]], theme)
            (args.output_dir / f"{project['slug']}-{theme}.svg").write_text(card)
        print(f"{project['repo']}: {counts[project['repo']]:,} stars")

    snapshot = {"updated_at": datetime.now(timezone.utc).isoformat(), "repositories": counts}
    (args.output_dir / "stars.json").write_text(json.dumps(snapshot, indent=2) + "\n")


if __name__ == "__main__":
    main()
