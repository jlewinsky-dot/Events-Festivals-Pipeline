OUTDOOR_KEYWORDS = {
    # festivals & fairs
    "festival", "fest", "fair", "fairgrounds", "carnival",
    "market", "outdoor", "outside",
    # races & runs
    "5k", "10k", "marathon", "triathlon", "race", "run",
    "half marathon", "relay", "dash", "trot", "sprint",
    "walk", "walkathon",
    # food & drink
    "bbq", "cookout", "tailgate", "tailgating", "picnic",
    "cook-off", "crawfish", "food truck",
    "beer", "wine", "bourbon", "whiskey",
    # parades & shows
    "parade", "fireworks", "rodeo",
    "car show", "truck show", "tractor pull",
    # music & performance
    "concert", "amphitheater", "music",
    # sports & recreation
    "tournament", "softball", "baseball", "soccer", "field",
    "football", "lacrosse", "rugby", "kickball",
    "fishing", "golf", "cycling",
    "mud run", "obstacle course", "color run",
    # construction & work
    "construction", "groundbreaking", "jobsite",
    # gatherings
    "wedding", "reunion", "graduation",
    "fundraiser", "charity", "church",
    "homecoming", "campground", "trailhead",
    "block party", "street party",
    # seasonal
    "cornmaze", "pumpkin", "harvest",
    "christmas tree", "easter egg hunt",
    "july 4th", "4th of july", "independence day",
    # other outdoor
    "flea market", "swap meet",
    "renaissance", "ren faire",
    "polo", "equestrian", "horse show",
    "air show", "balloon",
    "county", "state fair",
}

EXCLUDE_KEYWORDS = {
    "job fair", "career fair", "career", "hiring",
    "job", "record fair", "baby fair", "science fair",
    "engineering fair", "workshop", "camp",
    "farmers market", "farmer's market",
    "book fair", "book festival", "college fair", "health fair",
    "film festival", "film fest", "screening",
    "tattoo", "yarn", "playwright",
    "my fair lady", "expo",
    "tailgate brewing", "tailgate brewery",
    "beauty festival", "wellness fest",
    "yoga", "comedy", "networking",
    "fair haven", "tabitha fair",
    "weq fair", "vendor fair",
    "indoor", "convention", "conference",
    "seminar", "webinar", "virtual",
    "gala", "banquet", "luncheon",
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