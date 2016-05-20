"""
    TODO
"""

from pprint import pprint
import xapian
import os.path, re, sys
from MoinMoin import config, wikiutil, Page

config.search_db_dir = os.path.join(config.data_dir, 'xapian_db')
config.search_db_language = "english"

def split_text(text):
    return re.finditer(r"\w+", text)
    
def file_content(path):
    file = open(path, "r")
    content = file.read()
    file.close()
    return content

def index_pages():
    db = xapian.WritableDatabase(xapian.open(config.search_db_dir,
                                             xapian.DB_CREATE_OR_OPEN))
    try:
        for page_name in request.rootpage.getPageList(): # missing request
            page = Page.Page(request, page_name) # XXX missing request
            update_page(page, db)
            db.flush()
    finally:
        db.__del__()

def _index_page(page):
    document = xapian.Document()
    document.set_data(page.page_name.encode(config.charset))
    stemmer = xapian.Stem(config.search_db_language)
    words = split_text(page.get_raw_body().lower())
    count = 0
    for wordmatch in words:
        count += 1
        word = wordmatch.group().encode(config.charset)
        document.add_posting('R' + stemmer.stem_word(word), count)
    return document

def add_page(page, db):
    id = db.add_document(_index_page(page))
    id_file = page.getPagePath("xapian.id", check_create=0, isfile=1)
    f = open(id_file, 'w')
    f.write(`id`)
    f.close()
    print "new id: %s <br>" % id

def update_page(page, db):
    id_file = page.getPagePath("xapian.id", check_create=0, isfile=1)
    try:
        f = open(id_file, 'w')
        id = f.read()
        f.close()
        docid = int(id)
    except:
        add_page(page, db)
        return
    print "update id: %s <br>" % docid
    if wikiutil.timestamp2version(os.path.getmtime(id_file)) < page.mtime_usecs():
        db.replace_document(docid, _index_page(page))


def run_query(query, db):
    enquire = xapian.Enquire(db)
    parser = xapian.QueryParser()
    query = parser.parse_query(query)
    print query.get_description()
    enquire.set_query(query)
    return enquire.get_mset(0, 10)

def main():
    print "Begin"
    db = xapian.WritableDatabase(xapian.open('test.db',
                                             xapian.DB_CREATE_OR_OPEN))

    index_data(db)
    #del db

    #mset = run_query(sys.argv[1], db)
    #print mset.get_matches_estimated()
    #iterator = mset.begin()
    #while iterator != mset.end():
    #    print iterator.get_document().get_data()
    #    iterator.next()
    #for i in xrange(1,170):
    #    doc = db.get_document(i)
    #    print doc.get_data()

