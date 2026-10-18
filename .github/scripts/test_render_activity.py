"""Regression coverage for contribution calendar refreshes."""

import contextlib
import io
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import render_activity


class CalendarRefreshTests(unittest.TestCase):
    def test_generation_tolerates_aggregate_and_daily_count_differences(self):
        for reported_total in (2, 9):
            with self.subTest(reported_total=reported_total), tempfile.TemporaryDirectory() as output:
                calendar = {
                    "totalContributions": reported_total,
                    "weeks": [{"contributionDays": [{
                        "date": "2026-10-18", "weekday": 0,
                        "contributionCount": 5, "contributionLevel": "FOURTH_QUARTILE",
                    }]}],
                }
                argv = ["render_activity.py", "--username", "example", "--output-dir", output]
                with (
                    patch.object(render_activity, "fetch_calendar", return_value=calendar),
                    patch.object(sys, "argv", argv),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    render_activity.main()
                for theme in render_activity.THEMES:
                    path = Path(output) / f"contribution-calendar-{theme}.svg"
                    root = ET.parse(path).getroot()
                    titles = [node.text for node in root.iter("{http://www.w3.org/2000/svg}title")]
                    self.assertIn(f"example's 3D contribution calendar: {reported_total} contributions", titles)
                    self.assertIn("2026-10-18: 5 contributions", titles)

    def test_empty_or_negative_counts_are_still_rejected(self):
        for total, counts in ((0, []), (-1, [0]), (0, [-1])):
            calendar = {
                "totalContributions": total,
                "weeks": [{"contributionDays": [{
                    "date": "2026-10-18", "weekday": 0,
                    "contributionCount": count, "contributionLevel": "NONE",
                } for count in counts]}],
            }
            with self.subTest(total=total, counts=counts):
                with self.assertRaisesRegex(ValueError, "empty or invalid"):
                    render_activity.render_calendar(calendar, "example", "light")


if __name__ == "__main__":
    unittest.main()
