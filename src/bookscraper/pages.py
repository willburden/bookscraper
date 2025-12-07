from functools import cached_property
from bs4 import BeautifulSoup, Tag
from bookscraper import fetch, model
from typing import cast


def extract_rating(container: Tag) -> int:
    """Finds a star rating in the container and extracts its value as an integer out of 5."""

    rating = cast(Tag, container.find(class_="star-rating"))
    value = rating["class"][1]
    return {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}[value]


def convert_price(string: str) -> int:
    """Converts a string like "£31.48" into a number of pence, like 3148."""

    point = string.find(".")
    pounds = int(string[1:point])
    pence = int(string[point + 1:])

    return pounds * 100 + pence


class BookPage:
    """A page listing the full information about a single book."""

    def __init__(self, url: str):
        self.soup: BeautifulSoup = fetch.soup(url)

    @cached_property
    def _article(self) -> Tag:
        return cast(Tag, self.soup.article)

    @cached_property
    def title(self) -> str:
        return cast(str, cast(Tag, self._article.h1).string)

    @cached_property
    def image_url(self) -> str:
        return cast(str, cast(Tag, self._article.img)["src"])

    @cached_property
    def description(self) -> str:
        header = self._article.find(id="product_description")
        return cast(str, cast(Tag, cast(Tag, header).find_next_sibling("p")).string)

    @cached_property
    def rating(self) -> int:
        return extract_rating(self._article)
    
    @cached_property
    def _table(self) -> Tag:
        return cast(Tag, self.soup.table)

    def _table_value(self, key: str) -> str | None:
        th = cast(Tag, self._table.find("th", attrs={"string": key}))
        return cast(Tag, th.find_next_sibling("td")).string

    @cached_property
    def upc(self) -> str:
        return cast(str, self._table_value("UPC"))

    @cached_property
    def price_excl_tax(self) -> int:
        string = cast(str, self._table_value("Price (excl. tax)"))
        return convert_price(string)

    @cached_property
    def tax(self) -> int:
        string = cast(str, self._table_value("Tax"))
        return convert_price(string)

    @cached_property
    def availability(self) -> int:
        # There don't seem to be any books out of stock in the catalogue,
        # so we don't know what the HTML would look like in that case.
        # This is a limitation of the test site so let's just assume it's in stock.
        string = cast(str, self._table_value("Availability"))
        string = string.removeprefix("In stock (")
        string = string.removesuffix(" available)")
        return int(string)

    @cached_property
    def num_reviews(self) -> int:
        return int(cast(str, self._table_value("Number of reviews")))

    @cached_property
    def book(self) -> model.Book:
        return model.Book(
            title=self.title,
            image_url=self.image_url,
            description=self.description,
            rating=self.rating,
            upc=self.upc,
            price_excl_tax=self.price_excl_tax,
            tax=self.tax,
            availability=self.availability,
            num_reviews=self.num_reviews,
        )


class CataloguePage:
    """
    A page listing many books: either the full catalogue or only those in a particular
    category. If there are more than 20 results, they will be paginated, and this class
    will only represent a single page with at most 20 books. The adjacent pages can be
    accessed with the pager_links method.

    The book entries themselves contain only some of the information about a given book;
    for the full data, access the book's dedicated page with the BookPage class.

    This type of page also includes a sidebar with a full list of the available categories,
    which can be accessed with the categories method.
    """

    def __init__(self, url: str):
        self.soup: BeautifulSoup = fetch.soup(url)

    @cached_property
    def categories(self) -> list[model.Category]:
        sidebar = cast(Tag, self.soup.find(class_="side_categories"))
        inner_list = cast(Tag, cast(Tag, sidebar.ul).ul)
        links = inner_list("a")
        return [
            model.Category(
                name=cast(str, link.string).strip(),
                url=cast(str, link["href"])
            )
            for link in links
        ]

    @cached_property
    def books(self) -> list[model.CatalogueBook]:
        items = self.soup("article", class_="product_pod")
        return [
            model.CatalogueBook(
                title=cast(str, cast(Tag, item.find("a", title=True))["title"]),
                url=cast(str, cast(Tag, item.a)["href"]),
                thumbnail_url=cast(str, cast(Tag, item.img)["src"]),
                rating=extract_rating(item),
                price=convert_price(cast(str, cast(Tag, item.find(class_="price_color")).string))
            )
            for item in items
        ]

    @cached_property
    def _results_nums(self) -> list[int]:
        promotions = cast(Tag, self.soup.find(id="promotions"))
        form = cast(Tag, promotions.find_next_sibling("form"))
        return [
            int(cast(str, tag.string))
            for tag in form("strong")
        ]

    @property
    def num_results(self) -> int:
        return self._results_nums[0]
    
    @property
    def first_shown_result(self) -> int:
        return self._results_nums[1]
    
    @property
    def last_shown_result(self) -> int:
        return self._results_nums[2]

    @cached_property
    def _pager(self) -> Tag:
        return cast(Tag, self.soup.find(class_="pager"))

    @cached_property
    def _current_page_string(self) -> str:
        li = cast(Tag, self._pager.find(class_="current"))
        return cast(str, li.string).strip()

    @cached_property
    def num_pages(self) -> int:
        string = self._current_page_string
        return int(string[string.rfind(" ")+1:])
    
    @cached_property
    def current_page_num(self) -> int:
        string = self._current_page_string
        string = string.removeprefix("Page ")
        return int(string[:string.find(" ")])

    @cached_property
    def previous_page(self) -> str | None:
        li = self._pager.find(class_="previous")
        if li is None:
            return None
        
        return cast(str, cast(Tag, li.a)["href"])

    @cached_property
    def next_page(self) -> str | None:
        li = self._pager.find(class_="next")
        if li is None:
            return None
        
        return cast(str, cast(Tag, li.a)["href"])
