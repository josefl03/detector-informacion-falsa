from pydantic import BaseModel
import os
from loguru import logger
import lxml.html.clean
import markitdown
from typing import List, Optional
import io
import re

import fake_news_detector.services.llm as llm
import fake_news_detector.prompts as prompts
import fake_news_detector.debug as debug
import fake_news_detector.utils as utils
from fake_news_detector.datatypes import *
import fake_news_detector.parser as parser

TEXT_MAX = 2200000  # 2.2 million characters

class AIUtil:
    llm: "llm.LLM"
    
    def __init__(self, llm: "llm.LLM"):
        self.llm = llm

# ========== Article Classification
class ArticleClassifier(AIUtil):
    def is_article(self, pdf_b64: str) -> bool:
        """
        Classify the PDF as an article or not.
        """
        logger.debug(f"Classifying article...")
        
        msgs = llm.ChatBuilder()
        msgs.user(
            prompt=prompts.ARTICLE_CLASSIFICATION.user,
            pdf_uri=pdf_b64,
            pdf_name="webpage.pdf",
        )
        
        result = self.llm.call(
            messages=msgs,
            structure=ArticleClassification,
        )
        
        logger.debug(f"Is it an article?: {result.is_article}")
        
        return result.is_article
    
# ========== Article Parsing
class ArticleParser(AIUtil):
    cleaner: lxml.html.clean.Cleaner
    llm: "llm.LLM"
    
    def __init__(self, llm: "llm.LLM"):
        self.html_cleaner = lxml.html.clean.Cleaner(
            style=False,
            scripts=False,
            comments=False,
            links=False,
            meta=False,
            page_structure=False,
            processing_instructions=False,
            embedded=False,
            frames=False,
            forms=False,
            annoying_tags=False,
            remove_unknown_tags=False,
        )
        
        self.llm = llm
        
        self.html_parser = parser.Parser()
            
    def parse(self, html: str, pdf: str) -> ConvertedArticle:
        """
        Parse the HTML content and return a structured article.
        """
        logger.debug(f"Parsing article...")
        
        md = self.html_parser.html_to_md(html)
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.PDF_HTML_TO_STRUCTURED.system)
        msgs.user(
            prompt=md,
            pdf_uri=pdf,
            pdf_name="article.pdf",
        )
        
        result = self.llm.call(
            messages=msgs,
            structure=ConvertedArticle,
        )
        
        return result
    
# ========== Question Generation
class QuestionGenerator(AIUtil):
    def generate(self, context: str) -> str:
        """
        Generate a question based on the context.
        """
        logger.debug(f"Generating question...")
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.QUESTION_GENERATION.system)
        msgs.user(
            prompt=context,
        )
        
        result = self.llm.call(
            messages=msgs,
        )
        
        logger.trace(f"Generated question: {result}")
        
        return result

# ========== Comparison
class Comparer(AIUtil):
    def compare(self, text1: str, text2: str) -> str:
        """
        Compare two texts and return the differences.
        """
        logger.debug(f"Comparing texts...")
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.COMPARISON.system)
        msgs.user(
            prompts.COMPARISON.user.format(
                text1=text1,
                text2=text2,
            )
        )
        
        result = self.llm.call(
            messages=msgs,
            structure=VeredictClassification,
        )
        
        logger.trace(f"Comparison result:\n{result}")
        
        return result.veredict
    
class ArticleSummarizer(AIUtil):
    def summarize(self, md: str) -> str:
        """
        Summarize the given text.
        """
        logger.debug(f"Summarizing article...")
        
        if len(md) > TEXT_MAX:
            logger.warning(f"Text is too long ({len(md)} characters), truncating to 2.5 million characters.")
            md = md[:TEXT_MAX]  # Truncate to 2.5 million characters
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.ARTICLE_SUMMARIZATION.system)
        msgs.user(
            prompt=md,
        )
        
        result = self.llm.call(
            messages=msgs,
        )
        
        logger.trace(f"Article summary:\n{result}")
        
        return result
    
class WebPageSummarizer(AIUtil):
    def __init__(self, llm: "llm.LLM"):
        super().__init__(llm)
        self.html_parser = parser.Parser()
        
    def summarize(self, text: str) -> str:
        """
        Summarize the given text.
        """
        logger.debug(f"Summarizing webpage...")
        
        md = self.html_parser.html_to_md(text)
        
        logger.trace(f"Converted HTML to Markdown:\n{md}")
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.WEBPAGE_SUMMARIZATION.system)
        msgs.user(
            prompt=text,
        )
        
        result = self.llm.call(
            messages=msgs,
        )
        
        logger.trace(f"WebPage summary:\n{result}")
        
        return result
    
class ConclusionGenerator(AIUtil):
    def generate(self, article: str, top_sources: List[WebPage]) -> str:
        """
        Generate a conclusion based on the given text.
        """
        logger.debug(f"Generating conclusion...")
        
        sources = ""
        for i, source in enumerate(top_sources):
            sources += f"[{i+1}] {source.domain_name}\n"
            sources += f"{source.summary}\n\n"
        
        # Add system and user messages
        msgs = llm.ChatBuilder()
        msgs.system(prompts.CONCLUSION_GENERATION.system)
        msgs.user(
            prompt=prompts.CONCLUSION_GENERATION.user[0].format(
                article=article,
                sources=sources,
                temperature=prompts.CONCLUSION_GENERATION.temperature
            )
        )
        
        
        long_conclusion = self.llm.call(
            messages=msgs,
        )
        
        logger.trace(f"Conclusion (long):\n{long_conclusion}")
        
        # Add response as assistant message
        msgs.assistant(long_conclusion)
        msgs.user(
            prompt=prompts.CONCLUSION_GENERATION.user[1],
        )
        
        short_conclusion_raw = self.llm.call(
            messages=msgs,
            temperature=prompts.CONCLUSION_GENERATION.temperature
        )
        
        # Replace source placeholders with actual URLs
        short_conclusion = self.replace_sources(short_conclusion_raw, top_sources)  
        
        logger.trace(f"Conclusion (short):\n{short_conclusion}")
        
        return short_conclusion
    
    def replace_sources(self, article: str, sources: list[WebPage]) -> str:
        """
        Replace source placeholders [0], [1], ... in the text with actual source URLs in Markdown format.

        Args:
            txt (str): The text containing source placeholders.
            sources (list[str]): List of source URLs to replace placeholders.

        Returns:
            str: The text with source placeholders replaced by actual URLs.
        """
        def replace_placeholder(match):
            logger.debug(f"Found reference: {match.group(0)} at {match.span(0)[0]}-{match.span(0)[1]}")
            
            index = int(match.group(1))
            if index < len(sources):
                alt = sources[index].domain_name
                href = sources[index].url
                
                logger.debug(f"Replacing with: [{alt}]({href})")
                
                return f"[{alt}]({href})"
            
            return "" # Placeholder not found in sources
        
        pattern = re.compile(r'\[(\d+)\]')
        refs = len(pattern.findall(article))
        logger.debug(f"Found {refs} references in the conclusion.")
        
        res = pattern.sub(replace_placeholder, article)
        
        return res
    
class GrammarClassifier(AIUtil):
    def classify(self, text: str) -> GrammarClassification:
        """
        Classify the text for grammar issues.
        """
        logger.debug(f"Classifying if grammar issues... Text length: {len(text)}")
        
        if len(text) > TEXT_MAX:
            logger.warning(f"Text is too long ({len(text)} characters), truncating to 2.5 million characters.")
            text = text[:TEXT_MAX]  # Truncate to 2.5 million characters
        
        msgs = llm.ChatBuilder()
        msgs.system(prompts.GRAMMAR_CLASSIFICATION.system)
        msgs.user(
            prompt=text,
        )
        
        result = self.llm.call(
            messages=msgs,
            structure=GrammarClassification,
            temperature=prompts.GRAMMAR_CLASSIFICATION.temperature,
        )
        
        logger.trace(f"Has grammar issues?: {result.has_grammar_issues}")
        if result.has_grammar_issues:
            logger.trace(f"Grammar issues found: {result.where}")
        
        return result
        
if __name__ == "__main__":
    debug.setup()
    
    client = llm.OpenAI(llm.OPENAI_GPT41)
    
    def test_parser():
        parser = ArticleParser(client)
        
        html = utils.load("dummy/noticia.html")
        pdf = utils.load_b64("dummy/noticia.pdf")
        
        result = parser.parse(html, pdf)
        
        print(result)
    test_parser()