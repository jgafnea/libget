from collections import namedtuple

from libgen_api import LibgenSearch
from pyshorteners import Shortener
from rich import box
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

Book = namedtuple("Book", "title, year, author, extension, size, download")
books = []


def search_books(query) -> list:

    lang_filter = {"Language": "English"}
    file_filter = ("epub", "pdf")

    search = LibgenSearch()

    # Filter twice, first using libgen for language, then using our own for file type.
    results = search.search_title_filtered(query, lang_filter)
    results = [r for r in results if r["Extension"] in (file_filter)]

    with Progress(transient=True) as progress:
        # Capture number of results as total_work so progress updates are accurate.
        total_work = len(results)
        task = progress.add_task("Working...", total=total_work)

        for book_data in results:
            resolved = search.resolve_download_links(book_data)["GET"]
            tinyurl = Shortener().tinyurl.short(resolved)
            book_data["Download"] = tinyurl

            book_data = {
                # Make keys lowercase so book_data['Author'] becomes Book.author.
                key.lower(): value
                for key, value in book_data.items()
                # Get relevant keys from Book._fields.
                if key.lower() in set(Book._fields)
            }

            # Create new Book objects and add to list.
            book = Book(**book_data)
            books.append(book)

            # Update progress after each book.
            progress.update(task, advance=1)

    # Sort list so rich table shows most-recent first.
    books.sort(key=lambda book: book.year, reverse=True)

    return books


def display_results(results) -> None:
    # https://rich.readthedocs.io/en/stable/appendix/colors.html
    table = Table(title="", box=box.SIMPLE_HEAD)

    table.add_column("Title", style="bright_cyan")
    table.add_column("Year", style="bright_magenta")
    table.add_column("Author", style="yellow")
    table.add_column("Ext", style="green")
    table.add_column("Size", style="dim", justify="right")
    table.add_column("Download", style="blue")

    for book in results:
        table.add_row(
            book.title,
            book.year,
            book.author,
            book.extension,
            book.size,
            book.download,
        )

    console = Console()
    console.print(table)
