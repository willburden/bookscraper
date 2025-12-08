from functools import cached_property
from typing import cast
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from bookbrowser import fetch


class BookPage:
    """A page listing the full information about a single book."""

    def __init__(self, url: str):
        self.url: str = url
        self.soup: BeautifulSoup = fetch.soup(url)

    @cached_property
    def _article(self) -> Tag:
        return expect(self.soup.article)

    @cached_property
    def title(self) -> str:
        return expect_string(self._article.h1)

    @cached_property
    def image_url(self) -> str:
        relative = expect_attr(self._article.img, "src")
        return urljoin(self.url, relative)

    @cached_property
    def description(self) -> str:
        header = expect(self._article.find(id="product_description"))
        desc = expect_string(header.find_next_sibling("p"))
        return desc.removesuffix("...more").strip()

    @cached_property
    def rating(self) -> int:
        return extract_rating(self._article)

    @cached_property
    def _table(self) -> Tag:
        return expect(self.soup.table)

    def _table_value(self, key: str) -> str:
        # The below find() invocation works and is documented at:
        # https://beautiful-soup-4.readthedocs.io/en/latest/index.html#the-string-argument
        # But it doesn't typecheck correctly! So I have to use cast to get it accepted.
        th = cast(Tag | None, self._table.find("th", string=key))  # pyright: ignore[reportCallIssue, reportArgumentType]
        th = expect(th)
        return expect_string(th.find_next_sibling("td"))

    @cached_property
    def upc(self) -> str:
        return expect(self._table_value("UPC"))

    @property
    def price_incl_tax(self) -> int:
        return self.price_excl_tax + self.tax

    @cached_property
    def price_excl_tax(self) -> int:
        string = expect(self._table_value("Price (excl. tax)"))
        return price_to_pence(string)

    @cached_property
    def tax(self) -> int:
        string = expect(self._table_value("Tax"))
        return price_to_pence(string)

    @cached_property
    def availability(self) -> int:
        # There don't seem to be any books out of stock in the catalogue,
        # so we don't know what the HTML would look like in that case.
        # This is a limitation of the test site so let's just assume it's in stock.
        string = expect(self._table_value("Availability"))
        string = string.removeprefix("In stock (")
        string = string.removesuffix(" available)")
        return int(string)

    @cached_property
    def num_reviews(self) -> int:
        return int(expect(self._table_value("Number of reviews")))


class CataloguePage:
    """
    A page listing many books, possibly filtered to a specific category. If there are
    more than 20 results, they will be paginated, and this class will only represent a
    single page with at most 20 books. The adjacent pages can be accessed with the
    `prev_page_url` and `next_page_url` methods.

    The book entries themselves contain only some of the information about a given book;
    for the full data, access the book's dedicated page with the `BookPage` class.

    This type of page also includes a sidebar with a full list of the available categories,
    which can be accessed with the `categories` method.
    """

    def __init__(self, url: str):
        self.url: str = url
        self.soup: BeautifulSoup = fetch.soup(url)

    class Category:
        """
        The part of a `CataloguePage` that contains information about a
        specific category in the sidebar.
        """

        def __init__(self, page: CataloguePage, tag: Tag):
            self.page: CataloguePage = page
            self.tag: Tag = tag

        @cached_property
        def name(self) -> str:
            return expect_string(self.tag).strip()

        @cached_property
        def url(self) -> str:
            return urljoin(self.page.url, expect_attr(self.tag, "href"))

    @cached_property
    def categories(self) -> list[CataloguePage.Category]:
        sidebar = expect(self.soup.find(class_="side_categories"))
        inner_list = expect(expect(sidebar.ul).ul)
        links = inner_list("a")
        return [
            self.Category(self, link)
            for link in links
        ]
    
    class Book:
        """
        The part of a `CataloguePage` that contains information about a specific
        book. It only contains some of the book's information; to get the full information,
        use `BookPage` with this instance's `url` property.
        """

        def __init__(self, page: CataloguePage, tag: Tag):
            self.page: CataloguePage = page
            self.tag: Tag = tag
        
        @cached_property
        def title(self) -> str:
            return expect_attr(self.tag.find("a", title=True), "title")
        
        @cached_property
        def url(self) -> str:
            relative = expect_attr(self.tag.a, "href")
            return urljoin(self.page.url, relative)
        
        @cached_property
        def thumbnail_url(self) -> str:
            relative = expect_attr(self.tag.img, "src")
            return urljoin(self.page.url, relative)
        
        @cached_property
        def rating(self) -> int:
            return extract_rating(self.tag)
        
        @cached_property
        def price(self) -> int:
            string = expect_string(self.tag.find(class_="price_color"))
            return price_to_pence(string)

    @cached_property
    def books(self) -> list[CataloguePage.Book]:
        items = self.soup(class_="product_pod")
        return [
            self.Book(self, item)
            for item in items
        ]
    
    @cached_property
    def header(self) -> str:
        return expect_string(self.soup.h1)

    @cached_property
    def _results_nums(self) -> list[int]:
        promotions = expect(self.soup.find(id="promotions"))
        form = expect(promotions.find_next_sibling("form"))
        return [int(expect_string(tag)) for tag in form("strong")]

    @property
    def num_results(self) -> int:
        return self._results_nums[0]

    @property
    def first_shown_result(self) -> int:
        try:
            return self._results_nums[1]
        except IndexError:
            return 1

    @property
    def last_shown_result(self) -> int:
        try:
            return self._results_nums[2]
        except IndexError:
            return self.num_results

    @cached_property
    def _pager(self) -> Tag | None:
        return self.soup.find(class_="pager")

    @cached_property
    def _current_page_string(self) -> str | None:
        if self._pager is None:
            return None
        
        li = expect(self._pager.find(class_="current"))
        return expect_string(li).strip()

    @cached_property
    def num_pages(self) -> int:
        if self._current_page_string is None:
            return 1

        string = self._current_page_string
        return int(string[string.rfind(" ") + 1 :])

    @cached_property
    def current_page_num(self) -> int:
        if self._current_page_string is None:
            return 1
        
        string = self._current_page_string
        string = string.removeprefix("Page ")
        return int(string[: string.find(" ")])

    @cached_property
    def prev_page_url(self) -> str | None:
        if self._pager is None:
            return None

        li = self._pager.find(class_="previous")
        if li is None:
            return None

        relative = expect_attr(li.a, "href")
        return urljoin(self.url, relative)

    @cached_property
    def next_page_url(self) -> str | None:
        if self._pager is None:
            return None

        li = self._pager.find(class_="next")
        if li is None:
            return None

        relative = expect_attr(li.a, "href")
        return urljoin(self.url, relative)


class UnexpectedMarkup(Exception):
    pass


def expect[T](value: T | None) -> T:
    """
    'Expect' that an optional value is present. This takes a value of type `T | None`,
    and either returns the value if it's of type `T` or raises an `UnexpectedMarkup` exception.
    """

    if value is None:
        raise UnexpectedMarkup
    else:
        return value


def expect_string(tag: Tag | None) -> str:
    """
    'Expect' an optional `Tag` not to be `None` and to have the `string` property.
    If it doesn't meet these expectations, raise an `UnexpectedMarkup` exception.
    
    This function also converts the string from a `NavigableString` to an ordinary `str`
    with no reference to the Beautiful Soup parse tree, so the parse tree isn't accidentally
    kept in memory.
    """

    string = expect(expect(tag).string)
    return str(string)


def expect_attr(tag: Tag | None, attr: str) -> str:
    """
    'Expect' an optional `Tag` not to be `None` and to have an attribute with a string value.
    If it doesn't meet these expectations, raise an `UnexpectedMarkup` exception.
    """

    value = expect(tag)[attr]
    if isinstance(value, str):
        return value
    else:
        raise UnexpectedMarkup


def extract_rating(container: Tag) -> int:
    """Finds a star rating in the container and extracts its value as an integer out of 5."""

    rating = expect(container.find(class_="star-rating"))
    value = rating["class"][1]
    return {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}[value]


def price_to_pence(price: str) -> int:
    """Converts a string like `"£31.48"` into a number of pence, like `3148`."""

    point = price.find(".")
    pounds = int(price[1:point])
    pence = int(price[point + 1 :])

    return pounds * 100 + pence


def pence_to_price(pence: int) -> str:
    """Converts a number of pence like `3148` into a string like `"£31.48"`."""

    return f"£{pence // 100}.{pence % 100:02}"
