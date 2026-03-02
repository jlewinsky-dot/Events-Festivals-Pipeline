OUTDOOR_KEYWORDS = {
    "festival", "fest", "fair", "fairgrounds", "carnival",
    "market", "outdoor", "outside",
    "5k", "10k", "marathon", "triathlon", "race", "run",
    "bbq", "cookout", "tailgate", "tailgating", "picnic",
    "parade", "fireworks", "rodeo",
    "concert", "amphitheater", "music",
    "tournament", "softball", "baseball", "soccer", "field",
    "construction", "groundbreaking", "jobsite",
    "wedding", "reunion", "graduation",
    "fundraiser", "charity", "church",
    "homecoming", "campground", "trailhead",
    "cornmaze", "pumpkin", "harvest",
    "fishing", "golf", "cycling",
    "block party", "mud run",
}

EXCLUDE_KEYWORDS = {
    "job fair", "career fair", "career", "hiring",
    "job", "record fair", "baby fair", "science fair",
    "engineering fair", "workshop", "camp",
    "farmers market", "farmer's market"
}
# This function takes an event title, if an exlclude keyword is in the title, return False
# If an outdoor keyword is in the event title, return True and use this event. 
# Else, just return False
def is_outdoor_event(title):
    title = title.lower()
    for kw in EXCLUDE_KEYWORDS: 
        if kw in title:
            return False
    for kw in OUTDOOR_KEYWORDS:
        if kw in title:
            return True
    return False