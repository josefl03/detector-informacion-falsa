from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal
from datetime import datetime

@dataclass
class Pipe:
    domain: "Domain"
    domain_reputation: int = None
    
    article_pdf: str = None
    article_html: str = None
    
    article: "Article"  = None
    
    question: str = None
    
    search_results: List["SearchResult"] = None
    search_webpages: List["WebPage"] = None
    search_webpages_filtered: List["WebPage"] = None
    
    conclusion: str = None
    
    verified_percentage: float = 0.0
    unverified_percentage: float = 0.0
    unrelated_percentage: float = 0.0
    
    verified: bool = None
    
    has_author: bool = None
    has_sources: bool = None
    has_ai_images: bool = None
    is_recent: bool = None
    has_grammar_issues: bool = None
    grammar_issues: str = None
    has_bad_reputation: bool = None
    
    phase: str = None
    refusal: str = None
    error: str = None
    exception: str = None
    
    elapsed: int = 0
    
    pdf_input_usage: int = 0
    pdf_output_usage: int = 0
    text_input_usage: int = 0
    text_output_usage: int = 0
    
    def __init__(self, url):
        # Define sub-objects
        self.article = Article(url=url)
        self.domain = Domain()

# ==========

@dataclass
class Domain:
    name: str = None
    ip: str = None
    country: str = None
    region: str = None

# ==========

@dataclass
class SearchResult: # Search result from a search engine
    url: str
    title: str
    #description: str
    date: datetime
    
    #thumbnail: str
    
@dataclass
class EmbeddingsResult:
    url: str
    distance: float

Veredicts = Literal["verified", "unverified", "unrelated"]

@dataclass
class WebPage: # Scraped web page
    url: str
    domain_name: str = None
    title: str = None
    date: datetime = None
    summary: str = None
    summary_embeddings: List[float] = field(default_factory=list)
    
    distance: float = None
    veredict: Veredicts = None

@dataclass
class Article(WebPage): # Article to be analyzed
    author: str = None
    sources: List[str] = field(default_factory=list)
    markdown: str = None
    markdown_embeddings: List[float] = field(default_factory=list)

# ==========

class ArticleClassification(BaseModel):
    is_article: bool

class ConvertedArticle(BaseModel):
    title: str
    date: datetime
    
    markdown: str
    
    author: Optional[str]
    sources: Optional[List[str]]
    
    image_urls: Optional[List[str]]
    
class VeredictClassification(BaseModel):
    veredict: Veredicts

class GrammarClassification(BaseModel):
    where: str
    has_grammar_issues: bool
    
# ==========

@dataclass
class Result:
    error: bool = None
    error_msg: str = None
    
    refusal: bool = None
    refusal_msg: str = None

# ========== Results

@dataclass
class SourceResult:
    url: str
    title: str
    summary: str
    
    distance: float
    veredict: Veredicts
    

@dataclass
class AnalysisResult:
    url: str
    title: str
    markdown: str
    
    search_results: List[SourceResult] = field(default_factory=list)
    
    summary: str = ""
    conclusion: str = ""
    
    domain: str = ""
    ip: str = ""
    ip_country: str = ""
    ip_region: str = ""
    
    verified_percentage: float = 0.0
    unverified_percentage: float = 0.0
    unrelated_percentage: float = 0.0
    
    verified: bool = False
    
    has_author: bool = False
    has_sources: bool = False
    has_ai_images: bool = False
    is_recent: bool = False
    has_grammar_issues: bool = False
    has_bad_reputation: bool = False
    
    phase: str = ""
    refusal: str = ""
    error: str = ""
    exception: str = ""
