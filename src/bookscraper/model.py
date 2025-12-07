from typing import TypedDict


class Book(TypedDict):
    """The full set of information about a book."""

    title: str
    image_url: str
    description: str
    rating: int
    upc: str
    price_excl_tax: int
    tax: int
    availability: int
    num_reviews: int


class CatalogueBook(TypedDict):
    """The information shown on a catalogue page about a particular book."""

    title: str
    url: str
    thumbnail_url: str
    rating: int
    price: int


class Category(TypedDict):
    """A browsable category of books available at a particular URL."""

    name: str
    url: str
