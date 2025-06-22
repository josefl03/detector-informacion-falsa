from datetime import datetime, timezone, timedelta

import fake_news_detector.utils as utils

MOCK_BASE = "dummy/mock/"

ARTICLE_URL = "https://www.example.com/article"
ARTICLE_TITLE = "Example Article Title"

ARTICLE_TITLE = "Una explosión provoca un incendio en una nave de productos químicos en la localidad sevillana de Alcalá de Guadaíra"
ARTICLE_DATE = datetime(1405, 5, 14, 15, 20, tzinfo=timezone(timedelta(hours=2)))
ARTICLE_AUTHOR = "Eva Saiz"
ARTICLE_SOURCES = [
    "https://elpais.com/espana/2025-05-14/una-explosion-provoca-un-incendio-en-una-nave-de-productos-quimicos-en-la-localidad-sevillana-de-alcala-de-guadaira.html"
]

def set_mocks(obj):
    def mock_download_article(pipe):
        pipe.article.url = ARTICLE_URL
        pipe.article.title = ARTICLE_TITLE
        
        pipe.article_html = utils.load(MOCK_BASE + "article.html")
        pipe.article_pdf = utils.load_b64(MOCK_BASE + "article.pdf")
    obj.mock_download_article = mock_download_article
    
    def mock_parse_article(pipe):
        pipe.article.title = ARTICLE_TITLE
        pipe.article.date = ARTICLE_DATE
        
        pipe.article.markdown = utils.load(MOCK_BASE + "article.md")
        
        pipe.article.author = ARTICLE_AUTHOR
        pipe.article.sources = ARTICLE_SOURCES
    obj.mock_parse_article = mock_parse_article
    
    def mock_process_article(pipe):
        pipe.question = utils.load(MOCK_BASE + "article_question.txt")
        pipe.article.summary = utils.load(MOCK_BASE + "article_summary.md")
        pipe.article.summary_embeddings = utils.load_obj(MOCK_BASE + "summary_embeddings.pkl")
        pipe.article.markdown_embeddings = utils.load_obj(MOCK_BASE + "markdown_embeddings.pkl")
    obj.mock_process_article = mock_process_article
    
    def mock_search(pipe):
        pipe.search_results = utils.load_obj(MOCK_BASE + "search_results.pkl")
    obj.mock_search = mock_search