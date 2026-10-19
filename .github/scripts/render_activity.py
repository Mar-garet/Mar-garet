"""Render a compact 3D calendar from the owner's actual GitHub contributions."""

import argparse
import json
import math
import subprocess
from datetime import date
from html import escape
from pathlib import Path


QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""
LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}
THEMES = {
    "light": {
        "text": "#1f2328",
        "muted": "#59636e",
        "colors": ["#eff2f5", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
    "dark": {
        "text": "#f0f6fc",
        "muted": "#9198a1",
        "colors": ["#212830", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
}


def fetch_calendar(username: str) -> dict:
    response = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={username}"],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(response.stdout)
    if result.get("errors"):
        raise ValueError(f"GitHub contribution query failed: {result['errors']}")
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def shade(color: str, factor: float) -> str:
    return "#" + "".join(
        f"{round(int(color[i:i + 2], 16) * factor):02x}" for i in (1, 3, 5)
    )


def polygon(points: list[tuple[float, float]], color: str) -> str:
    coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{coordinates}" fill="{color}" />'


def render_calendar(calendar: dict, username: str, theme: str) -> str:
    weeks = calendar["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    if (
        not days
        or calendar["totalContributions"] < 0
        or any(day["contributionCount"] < 0 for day in days)
    ):
        raise ValueError("GitHub returned an empty or invalid contribution calendar")

    palette = THEMES[theme]
    # Foreshortened week/day axes keep a full year readable inside a profile README.
    week_dx, week_dy = 19, 3.8
    day_dx, day_dy = -10, 7
    gap = 0.86
    origin_x, origin_y = 86, 150
    width = math.ceil(origin_x + len(weeks) * week_dx + 24)
    height = math.ceil(origin_y + len(weeks) * week_dy + 7 * day_dy + 44)
    max_count = max(day["contributionCount"] for day in days)
    max_log = math.log1p(max_count) or 1
    bars = []
    padding = []

    # The API can omit days at the edges of the calendar, especially this week.
    # Complete the base before painting the real columns, without inventing data.
    for week_index, week in enumerate(weeks):
        known_weekdays = {day["weekday"] for day in week["contributionDays"]}
        for weekday in sorted(set(range(7)) - known_weekdays):
            x = origin_x + week_index * week_dx + weekday * day_dx
            y = origin_y + week_index * week_dy + weekday * day_dy
            a = (x, y - 2)
            b = (x + week_dx * gap, y + week_dy * gap - 2)
            c = (b[0] + day_dx * gap, b[1] + day_dy * gap)
            d = (x + day_dx * gap, y + day_dy * gap - 2)
            color = palette["colors"][0]
            padding.append(
                "<g>"
                + polygon([b, c, (c[0], c[1] + 2), (b[0], b[1] + 2)], shade(color, 0.64))
                + polygon([c, d, (d[0], d[1] + 2), (c[0], c[1] + 2)], shade(color, 0.82))
                + polygon([a, b, c, d], color)
                + "</g>"
            )

    # Paint back to front, so the nearer day and week faces cover the far faces.
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = day["weekday"]
            count = day["contributionCount"]
            color = palette["colors"][LEVELS[day["contributionLevel"]]]
            x = origin_x + week_index * week_dx + weekday * day_dx
            y = origin_y + week_index * week_dy + weekday * day_dy
            # A logarithmic height scale keeps isolated spikes within the canvas.
            bar_height = 2 + 88 * math.log1p(count) / max_log
            a = (x, y - bar_height)
            b = (x + week_dx * gap, y + week_dy * gap - bar_height)
            c = (b[0] + day_dx * gap, b[1] + day_dy * gap)
            d = (x + day_dx * gap, y + day_dy * gap - bar_height)
            label = f"{day['date']}: {count:,} contributions"
            bars.append(
                f'<g><title>{escape(label)}</title>'
                + polygon([b, c, (c[0], c[1] + bar_height), (b[0], b[1] + bar_height)], shade(color, 0.64))
                + polygon([c, d, (d[0], d[1] + bar_height), (c[0], c[1] + bar_height)], shade(color, 0.82))
                + polygon([a, b, c, d], color)
                + "</g>"
            )

    first, last = days[0]["date"], days[-1]["date"]
    period = f"{date.fromisoformat(first):%b %Y} / {date.fromisoformat(last):%b %Y}"
    title = f"{username}'s 3D contribution calendar: {calendar['totalContributions']:,} contributions"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">Daily GitHub contributions from {first} to {last}. Taller columns indicate more contributions, using a logarithmic height scale.</desc>
  <g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif">
    <text x="24" y="28" fill="{palette['text']}" font-size="18" font-weight="600">{calendar['totalContributions']:,} contributions</text>
    <text x="{width - 24}" y="28" text-anchor="end" fill="{palette['muted']}" font-size="14">{period}</text>
    <g id="calendar-padding" aria-hidden="true">{''.join(padding)}</g>
    {''.join(bars)}
    <text x="24" y="{height - 12}" fill="{palette['muted']}" font-size="13">One column per day · Height reflects activity</text>
  </g>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    calendar = fetch_calendar(args.username)
    # GitHub's aggregate and daily counts can differ, as in the 2026-10-18 run.
    # Preserve both API values instead of treating a mismatch as invalid data.
    daily_total = sum(
        day["contributionCount"]
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    )
    if daily_total != calendar["totalContributions"]:
        print(
            f"GitHub reported {calendar['totalContributions']:,} total contributions "
            f"and {daily_total:,} across daily counts; rendering the provided values."
        )
    rendered = {theme: render_calendar(calendar, args.username, theme) for theme in THEMES}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme, svg in rendered.items():
        (args.output_dir / f"contribution-calendar-v2-{theme}.svg").write_text(svg)
    print(f"Rendered {calendar['totalContributions']:,} real contributions in light and dark themes")


if __name__ == "__main__":
    main()
