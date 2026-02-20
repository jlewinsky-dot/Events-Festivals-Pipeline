from openai import OpenAI
from dotenv import load_dotenv
import serpapi
import os
import json

load_dotenv()
client = OpenAI()


def extract_contact_info(home_html, contact_html=None):
    content = f"HOMEPAGE:\n{home_html}"
    if contact_html:
        content += f"\n\nCONTACT PAGE:\n{contact_html}"

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract contact information from the provided website text. "
                    "Return a JSON object with these keys: email, phone, mailing_address in this exact order. "
                    "Only return info you can clearly see on the page. "
                    "Do not guess or make anything up. "
                    "Use null for any field you cannot find."
                ),
            },
            {
                "role": "user",
                "content": content,
            },
        ],
    )

    result = json.loads(response.choices[0].message.content)
    return [result.get("email"), result.get("phone"), result.get("mailing_address")]


def fill_missing_fields(event_title, location, contact_info):
    # For any null fields, search Google and ask GPT to extract the missing info.
    fields = ["email", "phone", "mailing_address"]
    
    for i, field in enumerate(fields):
        if contact_info[i] is not None:  # already have it, skip
            continue

        # Search Google for the missing field
        query = f"{event_title} {location} {field.replace('_', ' ')}"
        results = serpapi.GoogleSearch({
            "engine": "google",
            "q": query,
            "api_key": os.getenv("SERPAPI_KEY"),
        }).get_dict()

        # Grab text snippets from top results
        snippets = []
        for r in results.get("organic_results", [])[:5]:
            if r.get("snippet"):
                snippets.append(r["snippet"])

        if not snippets:  # nothing found, move on
            continue

        # Ask GPT to extract just the missing field from the snippets
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Extract the {field.replace('_', ' ')} for {event_title} from the search results below. "
                        f"Return a JSON object with one key: {field}. "
                        "Only return info you can clearly see. "
                        "Do not guess or make anything up. "
                        "Use null if you cannot find it."
                    ),
                },
                {
                    "role": "user",
                    "content": "\n".join(snippets),
                },
            ],
        )

        result = json.loads(response.choices[0].message.content)
        contact_info[i] = result.get(field)

    return contact_info