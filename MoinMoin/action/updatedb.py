
from MoinMoin import Xapian, Page, wikiutil

def execute(pagename, request):
    request.http_headers()
    wikiutil.send_title(request, "Updating DB")
    Xapian.index_pages()
    wikiutil.send_footer(request, '')

