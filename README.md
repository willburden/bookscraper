# bookscraper

An interactive tool to browse the book library at https://books.toscrape.com, using web scraping techniques.

## Usage

## Development

This project uses [uv](https://docs.astral.sh/uv/) to manage its dependencies. Start by [installing uv](https://docs.astral.sh/uv/getting-started/installation/) and checking you have an [appropriate Python version](./pyproject.toml).

The documentation for uv has more detail on [managing Python versions](https://docs.astral.sh/uv/guides/install-python/) and [working with project dependencies](https://docs.astral.sh/uv/guides/projects/).

### Clone the project and install its dependencies

```bash
git clone git@github.com:willburden/bookscraper.git
cd bookscraper
uv sync
```

### Run the project
```
uv run src
```

### Build an executable

You can use [PyInstaller](https://pyinstaller.org) to bundle the project into a single, self-contained executable file. Check you have the [necessary system packages](https://pyinstaller.org/en/stable/requirements.html#pyinstaller-requirements) installed. Then:

```
uv run pyinstaller bookscraper.spec
```

This creates a file `dist/bookscraper`, which can be installed to an appropriate directory for your system.
