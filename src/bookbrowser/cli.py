import abc
import functools
from typing import Callable, TypedDict, cast, override

from bookbrowser.parse import BookPage, CataloguePage, pence_to_price


def main():
    """Run the command-line interface."""

    print("Welcome to bookbrowser")

    screen = MainMenu("https://books.toscrape.com/index.html")
    
    while screen is not None:
        screen.print()
        screen = screen.handle_command()


class Screen(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def print(self):
        """Print the Screen's main content."""

    @abc.abstractmethod
    def commands(self) -> list[Command | None]:
        """Return a list of commands the user may enter."""
    
    def handle_command(self) -> Screen | None:
        """
        Prints a command list, loops until the user enters a valid command, then
        runs that command.
        """

        commands = [c for c in self.commands() if c is not None]

        while True:
            try:
                print()
                self._print_commands(commands)
                next_screen = self._take_command(commands)
                print()

                return next_screen
            except InvalidInput as error:
                print(error)
                continue

    def _print_commands(self, commands: list[Command]):
        """Print a command list telling the user what they can do."""

        print(", ".join([
            self._command_tip(command)
            for command in commands
        ]), end="? ")
    
    def _command_tip(self, command: Command) -> str:
        """
        Create the bit of text telling the user how to enact a command.

        If the input for the command is a substring of the description,
        it will be integrated like this: `view [c]ategories`. Otherwise,
        the input will just be displayed before like: `[/] quit`.
        """

        parts = command["description"].partition(command["input"])
        if parts[1] == "":
            return f"[{command["input"]}] {command["description"]}"
        else:
            return f"{parts[0]}[{parts[1]}]{parts[2]}"
    
    def _take_command(self, commands: list[Command]) -> Screen | None:
        """
        Execute one command given by the user's input. Raises UnrecognisedCommand
        if their input doesn't match any commands.
        """

        try:
            inp = input().lower()
        except KeyboardInterrupt, EOFError:
            return None

        try:
            command = next(
                c for c in commands
                if self._command_matches(c, inp)
            )

            return command["callback"](inp)

        except StopIteration:
            raise UnrecognisedCommand

    def _command_matches(self, command: Command, inp: str) -> bool:
        """
        Evaluate whether an input matches a command. If a predicate function
        is supplied, use that. Otherwise, check for string equality.
        """

        if command["input_predicate"] is not None:
            return command["input_predicate"](inp)
        else:
            return command["input"].lower() == inp


class InvalidInput(Exception):
    """
    Exception indicating that the user entered an invalid input and should
    be prompted again.
    """

    @override
    def __str__(self) -> str:
        return "Invalid input"


class UnrecognisedCommand(InvalidInput):
    """
    Exception indicating that no available command matched the input.
    """

    @override
    def __str__(self) -> str:
        return "Unrecognised command"


class IndexOutOfRange(InvalidInput):
    """
    Exception indicating that no available command matched the input.
    """

    @override
    def __str__(self) -> str:
        return "Index out of range"


class Command(TypedDict):
    """
    A possible action for a user to take.

    `input` is the string that the user must enter to enact this command.
    For special inputs like ranges, an `input_predicate` can be supplied.

    `description` is a short bit of text that describes the command.

    `callback` is a function that takes the input as a keyword argument and returns a `Screen`,
    which will be the new active screen. Alternatively, if `None` is returned,
    the program will exit.
    """

    description: str
    input: str
    input_predicate: Callable[[str], bool] | None
    callback: Callable[[str], Screen | None]


# Allow two forms for the decorated functions, one with `self` and one without.
type CommandImpl[S] = Callable[[str], Screen | None] | Callable[[S, str], Screen | None]


def command[S](
    description: str,
    input: str,
    input_predicate: Callable[[str], bool] | None = None
) -> Callable[[CommandImpl[S]], Callable[..., Command]]:
    """
    Decorator to convert a function of the form:
    ```
    @command("d", "Do something")
    def do_something(inp) -> Screen:
        ...
    ```
    Into:
    ```
    def do_something() -> Command:
        return Command(
            input="d",
            description="Do something",
            callback=lambda inp: ...
        )
    ```
    """

    def decorator(func: Callable[..., Screen | None]) -> Callable[..., Command]:

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> Command:
            def callback(inp: str) -> Screen | None:
                return func(*args, inp, **kwargs)

            return Command(
                input=input,
                input_predicate=input_predicate,
                description=description,
                callback=callback,
            )

        return wrapper

    return decorator


@command("quit", "q")
def quit(_inp: str) -> None:
    pass


class MainMenu(Screen):
    def __init__(self, url: str):
        self.url: str = url

    @override
    def print(self):
        pass

    @override
    def commands(self) -> list[Command | None]:
        return [
            self.browse_all(),
            self.view_categories(),
            quit()
        ]

    @command("browse all", "a")
    def browse_all(self, _inp: str) -> Screen:
        return Browse(CataloguePage(self.url))

    @command("view categories", "c")
    def view_categories(self, _inp: str) -> Screen:
        return Categories(CataloguePage(self.url))


class Browse(Screen):
    def __init__(self, page: CataloguePage):
        self.page: CataloguePage = page

    @override
    def print(self):
        print(
            f"{self.page.header} - page {self.page.current_page_num} of {self.page.num_pages}"
        )
        
        print_list(self.page.books, lambda book: book.title)

    @override
    def commands(self) -> list[Command | None]:
        return [
            self.select_book(),
            self.prev_page(),
            self.next_page(),
            self.view_categories(),
            quit(),
        ]

    @command(
        "enter book index",
        "num",
        input_predicate=lambda inp: inp.isnumeric(),
    )
    def select_book(self, inp: str) -> Screen:
        index = int(inp)
        if index < 0 or index >= len(self.page.books):
            raise IndexOutOfRange
        
        url = self.page.books[index].url
        return BookDetails(url, prev_screen=self)
    
    def next_page(self) -> Command | None:
        if self.page.next_page_url is None:
            return None

        @command("next page", "n")
        def inner(_inp: str) -> Screen:
            # Cast to show that self.page.next_page_url can't be None here.
            return Browse(CataloguePage(cast(str, self.page.next_page_url)))

        return inner()
    
    def prev_page(self) -> Command | None:
        if self.page.prev_page_url is None:
            return None

        @command("previous page", "p")
        def inner(_inp: str) -> Screen:
            # Cast to show that self.page.prev_page_url can't be None here.
            return Browse(CataloguePage(cast(str, self.page.prev_page_url)))

        return inner()

    @command("view categories", "c")
    def view_categories(self, _inp: str) -> Screen:
        return Categories(self.page)


class BookDetails(Screen):
    def __init__(self, url: str, prev_screen: Screen):
        self.page: BookPage = BookPage(url)
        self.prev_screen: Screen = prev_screen
    
    @override
    def print(self):
        print(f"{self.page.title} (UPC: {self.page.upc})")
        print(" ".join(["★"] * self.page.rating) + f" from {self.page.num_reviews} reviews")
        print(f"{pence_to_price(self.page.price_incl_tax)} ({self.page.availability} copies in stock)")
        print("\n" + self.page.description)

    @override
    def commands(self) -> list[Command | None]:
        return [
            self.go_back(),
            quit(),
        ]

    @command("go back", "b")
    def go_back(self, _inp: str) -> Screen:
        return self.prev_screen


class Categories(Screen):
    def __init__(self, page: CataloguePage):
        self.page: CataloguePage = page
    
    @override
    def print(self):
        print("Categories")

        print_list(self.page.categories, lambda cat: cat.name)
    
    @override
    def commands(self) -> list[Command | None]:
        return [
            self.select_category(),
            self.browse_all(),
            quit(),
        ]

    @command(
        "enter category index",
        "num",
        input_predicate=lambda inp: inp.isnumeric(),
    )
    def select_category(self, inp: str) -> Screen:
        index = int(inp)
        if index < 0 or index >= len(self.page.categories):
            raise IndexOutOfRange
        
        url = self.page.categories[index].url
        return Browse(CataloguePage(url))

    @command("browse all books", "a")
    def browse_all(self, _inp: str) -> Screen:
        return Browse(self.page)


def print_list[T](values: list[T], repr: Callable[[T], object]):
    for (index, value) in enumerate(values):
        print(f"  [{index}] ", end="")
        print(repr(value))
