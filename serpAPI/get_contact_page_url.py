from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


CONTACT_KEYWORDS = ["contact", "about", "get in touch", "reach us", "connect",
                    "reach out", "talk to us", "email us", "call us", "get ahold",
                    "inquiries", "inquiry", "support", "help", "info",
                    ]


COMMON_PATHS = [ "/contact", "/contact-us", "/contact_us",
                "/about", "/about-us", "/about_us",
                "/connect", "/reach-out", "/get-in-touch",
                "/info", "/information", "/support",
                "/help", "/inquiries",
                ]



def find_contact_link(soup, base_url):
    for a in soup.find_all("a", href=True): # Grab every <a> tag on the page with href
        text = a.get_text(strip=True).lower() # grabs clickable text ("Contact us")
        href = a["href"].lower() # actual URL path

        for kw in CONTACT_KEYWORDS:
            if kw in text or kw in href: # if any of the contact keywords appear in either the text or link, return link
                return urljoin(base_url, a["href"])

    return None # Else return none


def try_common_paths(browser, base_url): # Looking through common contact slugs if no contact link from find contact link
    for path in COMMON_PATHS:
        url = urljoin(base_url, path)
        page = browser.new_page()
        resp = page.goto(url, timeout=10000)
        status = resp.status if resp else 0
        page.close()
        if status == 200: # If we get a contact page, return url
            return url

    return None # Else return none


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "noscript"]):
        tag.decompose() # removes each of the following tags and their contents

    return soup.get_text(separator="\n", strip=True)


def get_contact_page(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=25000)
            home_html = page.content() # save homepage HTML
            page.close()
            soup = BeautifulSoup(home_html, "html.parser") # page.content() is HTML being passed in
            # 1.) look for a contact link in the homepage
            contact_url = find_contact_link(soup, url)
            # 2.) if number 1 failed, try common paths
            if not contact_url:
                contact_url = try_common_paths(browser, base_url=url)
            # 3.) fetch the contact page
            contact_html = None
            if contact_url and contact_url != url:
                page = browser.new_page()
                page.goto(contact_url, timeout=25000)
                contact_html = page.content()
                page.close()
            browser.close()
        return [contact_url, clean_html(home_html), clean_html(contact_html) if contact_html else None]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return [None, None, None]