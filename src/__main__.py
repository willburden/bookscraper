from bookscraper.pages import CataloguePage

page = CataloguePage("https://books.toscrape.com/catalogue/page-2.html")
print(page.categories)
print(page.books)
print(page.num_results)
print(page.first_shown_result)
print(page.last_shown_result)
print(page.num_pages)
print(page.current_page_num)
print(page.previous_page)
print(page.next_page)
