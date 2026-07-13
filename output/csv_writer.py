import csv

CSV_FIELDS = [
    "city_state", "aerial_mileage", "yard_city_state",
    "title", "date", "address", "url", "contact_page",
    "email", "phone",
    "sells_food", "sells_alcohol", "sells_vip",
    "estimated_attendees", "attendees_source",
    "profitability",
]


def write_events_csv(filename, events):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(events)


def read_csv_rows(filename):
    with open(filename, newline="") as f:
        return list(csv.reader(f))


def write_csv_rows(filename, rows):
    with open(filename, "w", newline="") as f:
        csv.writer(f).writerows(rows)