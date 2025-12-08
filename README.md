# bookbrowser

An interactive tool to browse the book library at https://books.toscrape.com, using web scraping techniques.

## Usage

To run the tool, simply run:

```
bookbrowser
```

This will start the main menu. From there, you can enter one of the displayed command inputs
(surrounded with square brackets, for example: `view [c]ategories`) and press enter.

When a list is shown, for example:

```
[0] A book
[1] Another book
[2] A third book
```

You can enter the index number surrounded by square brackets to select a particular entry in the list.

## Development

This project uses [uv](https://docs.astral.sh/uv/) to manage its dependencies. Start by [installing uv](https://docs.astral.sh/uv/getting-started/installation/) and checking you have an [appropriate Python version](./pyproject.toml).

The documentation for uv has more detail on [managing Python versions](https://docs.astral.sh/uv/guides/install-python/) and [working with project dependencies](https://docs.astral.sh/uv/guides/projects/).

### Clone the project and install its dependencies

```bash
git clone https://github.com/willburden/bookbrowser.git
cd bookbrowser
uv sync
```

### Run the project
```
uv run src
```

### Build an executable

You can use [PyInstaller](https://pyinstaller.org) to bundle the project into a single, self-contained executable file. Check you have the [necessary system packages](https://pyinstaller.org/en/stable/requirements.html#pyinstaller-requirements) installed. Then:

```
uv run pyinstaller bookbrowser.spec
```

This creates a file `dist/bookbrowser`, which can be installed to an appropriate directory for your system.
