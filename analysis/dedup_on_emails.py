# Creating a set of emails, if the event's email is in the set already, discard that event
# So basically I am keeping the first event with instance of an email
def deduplicate(events):
    seen = set()
    duplicated_events = []
    for event in events:
        if event.get('email') in seen and event.get('email') is not None:
            continue
        else:
            duplicated_events.append(event)
            seen.add(event.get('email'))
    return duplicated_events

        