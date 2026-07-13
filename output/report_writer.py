import logging

from output.csv_writer import (
    CSV_FIELDS,
    write_events_csv,
    read_csv_rows,
    write_csv_rows,
)

logger = logging.getLogger(__name__)


def _filename_for_site(site):
    return f"{site.replace(' ', '_').lower()}_events.csv"


def _build_stats_rows(events, tracker):
    """Cost summary + event stats, rendered as (label, value) rows."""
    event_count = len(events)
    emails_processed = sum(1 for e in events if e.get("email"))
    email_hit_rate = emails_processed / event_count if event_count else 0

    return tracker.summary_rows() + [
        ("", ""),
        ("Event Count:", event_count),
        ("Emails Processed:", emails_processed),
        ("Email Hit Rate:", f"{email_hit_rate:.1%}"),
    ]


def _pad_rows(rows, width):
    for i in range(len(rows)):
        while len(rows[i]) < width:
            rows[i].append("")
    return rows


def _append_stats_column(rows, stats_rows):
    """Append stats rows to the right of the main table, with a blank-column gap."""
    for i, row in enumerate(rows):
        if i < len(stats_rows):
            label, val = stats_rows[i]
            rows[i] = row + ["", label, str(val)]
    return rows


def _append_empty_cities_column(rows, empty_cities):
    """Append 'Cities with no results' as a separate column to the far right."""
    if not empty_cities:
        return rows

    max_width = max(len(r) for r in rows)
    rows = _pad_rows(rows, max_width)

    rows[0] = rows[0] + ["", "Cities with no results"]
    for i, city in enumerate(empty_cities):
        idx = i + 1
        if idx < len(rows):
            rows[idx] = rows[idx] + ["", city]
        else:
            rows.append([""] * max_width + ["", city])
    return rows


def write_report(site, events, empty_cities, tracker):
    """Write the full per-site report: events table + cost/stats sidecar + empty cities column."""
    filename = _filename_for_site(site)

    write_events_csv(filename, events)

    stats_rows = _build_stats_rows(events, tracker)
    rows = read_csv_rows(filename)
    rows = _pad_rows(rows, len(CSV_FIELDS))
    rows = _append_stats_column(rows, stats_rows)
    rows = _append_empty_cities_column(rows, empty_cities)

    write_csv_rows(filename, rows)
    logger.info(f"Saved to {filename}")