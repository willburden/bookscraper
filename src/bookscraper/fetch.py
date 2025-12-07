from bs4 import BeautifulSoup
import requests


def soup(url: str) -> BeautifulSoup:
    """Requests some HTML and parses it into a BeautifulSoup object."""

    markup = html(url)
    return BeautifulSoup(markup, "lxml")
    

def html(url: str) -> bytes:
    """Sends an HTTP GET request, returning the HTML content as bytes."""

    r = requests.get(url)
    r.raise_for_status()

    return r.content
