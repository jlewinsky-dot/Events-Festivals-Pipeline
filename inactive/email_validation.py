from openai import OpenAI
import json

# UNUSED FOR NOW
'''
def email_confidence(email, event_title, organizer_url, venue_address):
    client = OpenAI()
    if not email:
        return None

    response = client.chat.completions.create(
        model="gpt-4.1",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are evaluating whether an email address belongs to the organizer of an event. "
                    "Return a JSON object with one key: confidence. "
                    "Be skeptical. Default to 'low' unless you have a clear reason to go higher. "
                    "\n\n"
                    "'high': the email domain clearly matches the event name or organizer website domain. "
                    "Example: event is 'CMA Fest', organizer site is cmafest.com, email is FestTickets@CMAworld.com — CMA is the same org, thats high. "
                    "Example: event is 'Deep Tropics Festival', email is Support@deeptropics.org — obvious match, high. "
                    "\n\n"
                    "'medium': the email is from a free provider (gmail, yahoo, outlook, aol) and could plausibly belong to a small event organizer. "
                    "Example: event is 'Nashville Mushroom Festival', email is tnmushroomfest@gmail.com — gmail but name matches, medium. "
                    "\n\n"
                    "'low': the email belongs to a venue, park, tourism board, ticketing platform, convention center, or any entity that is NOT the event organizer. "
                    "Example: event is 'Water Lantern Festival', email is mail@conservancyonline.com — thats a park conservancy, not the lantern festival organizer, low. "
                    "Example: event is 'Sumner County Irish Festival', email is info@visitsumnertn.com — thats a tourism board, low. "
                    "Example: event is 'Oyster Crawfish Fest', email is info@parktavern.com — Park Tavern is a venue, low. "
                    "Example: email contains '[email protected]' — thats spam protection garbage, low. "
                    "\n\n"
                    "Use the venue address provided to help identify venue-related emails. "
                    "No explanation, just the JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Event: {event_title}\n"
                    f"Organizer site: {organizer_url}\n"
                    f"Venue/Address: {venue_address}\n"
                    f"Email: {email}"
                ),
            },
        ],
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("confidence")
'''