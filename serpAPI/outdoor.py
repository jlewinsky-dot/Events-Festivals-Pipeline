OUTDOOR_KEYWORDS = {
    "festival", "fest", "fair", "market", "outdoor",
    "block party", "bbq", "cookout", "carnival",
    "parade", "5k", "marathon", "rodeo"
} 

EXCLUDE_KEYWORDS = {
    "job fair", "career fair", "career", "hiring",
    "job", "record fair", "baby fair", "science fair",
    "engineering fair", "workshop", "camp",
    "farmers market", "farmer's market"
}

def is_outdoor_event(title):
    title = title.lower()
    for kw in EXCLUDE_KEYWORDS: 
        if kw in title:
            return False
    for kw in OUTDOOR_KEYWORDS:
        if kw in title:
            return True
    return False