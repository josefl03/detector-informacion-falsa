from loguru import logger
import os
from datetime import datetime, timezone
import sys
import traceback
import time

from fake_news_detector.datatypes import *
import fake_news_detector.scraper as scraper
import fake_news_detector.services.web.scrape as scrape
import fake_news_detector.ai as ai
from fake_news_detector.phases import phase
import fake_news_detector.services.llm as llm
import fake_news_detector.services.search as search
import fake_news_detector.services.domain.geolocation as geolocation
import fake_news_detector.services.domain.reputation as reputation
import fake_news_detector.engines as engines
import fake_news_detector.utils as utils
from fake_news_detector.mocks import *
import fake_news_detector.debug as debug
import fake_news_detector.services.db as db
import fake_news_detector.services.embeddings_db as embeddings_db
import fake_news_detector.exceptions as exceptions

DISTANCE_THRESHOLD = 0.4 # 1: very similar, 0: no similarity, -1: very different

RAG_MAX_SOURCES_PER_TYPE = 5

RECENT_THRESHOLD = 1  # days

class FakeNewsDetector:
    pipe: Pipe = None
    callback: callable = None
    running: bool = False
    interrupted: bool = False
    
    scraper: "scraper.Scraper"
    
    domain_geolocation: "geolocation.DomainGeolocation"
    domain_reputation: "reputation.DomainReputatuion"
    
    embeddings: "llm.LLM"
    llm_pdf: "llm.LLM"
    llm_text: "llm.LLM"
    
    article_classifier: "ai.ArticleClassifier"
    article_parser: "ai.ArticleParser"
    article_summarizer: "ai.ArticleSummarizer"
    webpage_summarizer: "ai.WebPageSummarizer"
    question_generator: "ai.QuestionGenerator"
    comparer: "ai.Comparer"
    conclusion_generator: "ai.ConclusionGenerator"
    grammar_classifier: "ai.GrammarClassifier"
    
    
    def __init__(self, custom_logger: bool = False):
        if not custom_logger:
            debug.setup()
    
    @logger.catch(reraise=True)
    def run(self, url: str, mock=False):
        """
        Start the fake news detection process.
        
        :param url: The URL of the article to analyze.
        :return: Result object containing the analysis results.
        """
        
        # ---------
        self.running = True
        self.interrupted = False
        ex = None
        
        start = datetime.now(timezone.utc)
        
        self.pipe = Pipe(url) # New pipe
        
        #mock = True
        if mock:
            # Use a mocked pipe for testing
            #self.pipe = debug.load_pipe("20250614_175519_675_last_checks.pkl")
            pass
        
        try:
            self.init(self.pipe)
            
            # ---------
            self.check_domain(self.pipe)
            self.download_article(self.pipe)
            self.parse_article(self.pipe)
            self.process_article(self.pipe)
            self.search(self.pipe)
            self.process_search(self.pipe)
            self.rank_results(self.pipe)
            self.compare_results(self.pipe)
            self.draw_conclusion(self.pipe)
            self.last_checks(self.pipe)
            # ---------
            
            logger.success("Detection completed successfully.")
            
            # Set the state to finished
            self.pipe.phase = "finished"
            
        except exceptions.RefusalException as e:
            self.pipe.refusal = str(e)
            logger.error(f"Refusal: {e}")
        except exceptions.ErrorException as e:
            self.pipe.error = str(e)
            logger.error(f"Error: {e}")
        except KeyboardInterrupt:
            logger.warning(f"Interrupted.")
            self.interrupted = True
            return None
        except Exception as e:
            e_str = str(traceback.format_exc())
            
            self.pipe.exception = f"Unexpected Exception: {e_str}"
            logger.error(f"Unexpected Exception: {e_str}")
            
            ex, tb = e, sys.exc_info()[2]
        finally:
            # Raise any exception
            # if ex:
            #     raise ex.with_traceback(tb)
        
            if self.interrupted:
                return None
            
            self.running = False
            
            # Calculate elapsed time
            now = datetime.now(timezone.utc)
            now_str = utils.format_datetime(now)
            
            elapsed = now - start
            self.pipe.elapsed = elapsed.total_seconds()
            
            # Convert the pipe to AnalysisResult
            analysis = self.pipe_to_analysis(self.pipe)  # Convert the pipe to AnalysisResult
            
            # Save the analysis to a file
            utils.save_obj(f"logs/analysis/{now_str}_analysis.pkl", analysis)
            
            logger.success(f"Analysis finished. Time taken: {elapsed}")
            
            # Report the final status (if callback is set)
            self.run_callback()
        
            return analysis
    
    @phase(id="init")
    def init(self, pipe: Pipe):
        # Initialize web stuff
        self.scraper = scraper.Scraper([
            scrape.RequestsScraper(),
            scrape.PlaywrightScraper(),
        ])
        
        # Initialize domain stuff
        self.domain_geolocation = geolocation.IpInfoGeolocation()
        
        self.domain_reputation = reputation.VirusTotalReputation()
        
        # Initialize LLM stuff
        self.embeddings = llm.GenericLLM.choose(os.getenv("EMBEDDINGS_MODEL"), os.getenv("EMBEDDINGS_SERVICE"))
        
        self.llm_pdf = llm.GenericLLM.choose(os.getenv("PDF_MODEL"), os.getenv("PDF_SERVICE")) # LLM with PDF capabilities
        self.llm_text = llm.GenericLLM.choose(os.getenv("TEXT_MODEL"), os.getenv("TEXT_SERVICE")) # Text-only capabilities (including structured outputs)
        
        self.article_classifier = ai.ArticleClassifier(llm=self.llm_pdf)
        self.article_parser = ai.ArticleParser(llm=self.llm_pdf)
        self.article_summarizer = ai.ArticleSummarizer(llm=self.llm_pdf)
        self.webpage_summarizer = ai.WebPageSummarizer(llm=self.llm_pdf)
        self.question_generator = ai.QuestionGenerator(llm=self.llm_text)
        self.comparer = ai.Comparer(llm=self.llm_pdf)
        self.conclusion_generator = ai.ConclusionGenerator(llm=self.llm_pdf)
        self.grammar_classifier = ai.GrammarClassifier(llm=self.llm_pdf) # llm_text?
        
        # Initialize search engines
        self.search_engines = engines.MultiSearchEngine([
            search.BraveSearchEngine(),
        ])
        
        # Initialize database
        self.db = db.MongoDatabase()
        self.embeddings_db = embeddings_db.FaissEmbeddingsDatabase()
        
        logger.debug(f"Everything initialized successfully.")
    
    @phase(id="check_domain", monitor=True)
    def check_domain(self, pipe: Pipe):
        logger.info(f"Analyzing: {pipe.article.url}")
        
        # Check if the URL is valid
        if not utils.is_valid_url(pipe.article.url):
            raise exceptions.RefusalException("Invalid URL provided.")
            
        logger.debug(f"URL is valid")
            
        # Get domain's IP
        pipe.domain.name = utils.get_domain(pipe.article.url)
        pipe.domain.ip = utils.domain_to_ip(pipe.domain.name)
        
        logger.info(f"Domain IP: {pipe.domain.ip}")
        
        # Get geolocation data for the domain
        country, region = self.domain_geolocation.locate(pipe.domain.ip)
        
        pipe.domain.country = country
        pipe.domain.region = region
        
        logger.info(f"Domain geolocation: {pipe.domain.country}, {pipe.domain.region}")
        
        # Get domain's reputation
        pipe.domain_reputation = self.domain_reputation.get_reputation(
            pipe.domain.name
        )
        
        logger.info(f"Domain reputation: {pipe.domain_reputation}")
    
    @phase(id="download_article")
    def download_article(self, pipe: Pipe):
        # Clean URL params
        pipe.article.url = utils.clean_url(pipe.article.url)
        
        logger.info(f"Cleaned URL: {pipe.article.url}")
        
        # Download the PDF
        scrape_result = self.scraper.scrape(
            pipe.article.url,
            format=scraper.Format.PDF|scraper.Format.HTML
        )
        
        if not scrape_result:
            raise exceptions.ErrorException("Failed to download the article.")
        
        pipe.article.title = scrape_result.title
        assert pipe.article.title, "No title found in the article."
        pipe.article_html = scrape_result.html
        assert pipe.article_html, "No HTML content found in the article."
        
        
        
        pipe.article_pdf = scrape_result.pdf
        assert pipe.article_pdf, "No PDF content found in the article."
    
    @phase(id="parse_article")
    def parse_article(self, pipe: Pipe):
        # Check if it's an article
        article = self.article_classifier.is_article(pipe.article_pdf)
        
        if not article:
            raise exceptions.RefusalException("The PDF is not an article.")
            return
            
        # Parse the PDF content
        article = self.article_parser.parse(
            html = pipe.article_html,
            pdf = pipe.article_pdf,
        )
        
        pipe.article.title = article.title
        pipe.article.date = article.date
        
        pipe.article.markdown = article.markdown
        
        pipe.article.author = article.author
        pipe.article.sources = article.sources
        
        # Remove the same URL from sources
        if pipe.article.url in pipe.article.sources:
            pipe.article.sources.remove(pipe.article.url)
    
    @phase(id="process_article", monitor=True)
    def process_article(self, pipe: Pipe):
        # Convert article's body to a question
        pipe.question = self.question_generator.generate(
            pipe.article.markdown
        )
        
        # Summarize the article
        pipe.article.summary = self.article_summarizer.summarize(
            pipe.article.markdown
        )
        
        # Generate embeddings for the article's summary
        pipe.article.summary_embeddings = self.embeddings.get_embeddings(
            pipe.article.summary
        )
        
        # Generate embeddings for the article's markdown
        pipe.article.markdown_embeddings = self.embeddings.get_embeddings(
            pipe.article.markdown
        )
    
    @phase(id="search")
    def search(self, pipe: Pipe):
        logger.info(f"Searching for: {pipe.question}")
        
        # Search the question using multiple search engines
        pipe.search_results = self.search_engines.multi_search(pipe.question)
        
        if not pipe.search_results or len(pipe.search_results) == 0:
            raise exceptions.RefusalException("No sources found for the given article's topic.")
        
    @phase(id="process_search", monitor=True)
    def process_search(self, pipe: Pipe):
        logger.info(f"Processing {len(pipe.search_results)} search results.")
        
        pipe.search_webpages = []
        
        # Process search results
        for i, search_result in enumerate(pipe.search_results):
            # Clean the URL
            url = utils.clean_url(search_result.url)
            search_result.url = url
            
            logger.info(f"[{i}] Processing search result: {search_result.url}")
            
            # Search in cache
            wp = self.db.get_webpage(
                url=search_result.url,
            )
            
            if wp:
                # Found in cache, skip processing
                pipe.search_webpages.append(wp)
            
                # Save the embeddings to the embeddings database
                self.embeddings_db.add(url, wp.summary_embeddings)
                
                self.run_callback()
                continue
            
            # Not found. Process the search result
            search_result.domain_name = utils.get_domain(search_result.url)
            
            # Download the page content
            scrape_result = self.scraper.scrape(search_result.url, format=scraper.Format.HTML)
            
            if not scrape_result:
                logger.warning(f"Skipping...")
                continue
            
            html = scrape_result.html
            
            # Generate summary for the search result
            summary = self.webpage_summarizer.summarize(html)
            
            # Generate embeddings for the search result summary
            summary_embeddings = self.embeddings.get_embeddings(
                summary
            )
            
            wp = WebPage(
                    url=search_result.url,
                    title=search_result.title,
                    date=search_result.date,
                    domain_name=search_result.domain_name,
                    summary=summary,
                    summary_embeddings=summary_embeddings
                )
            
            # Save the webpage to the database
            self.db.add_webpage(webpage=wp)
            
            # Save the embeddings to the embeddings database
            self.embeddings_db.add(url, summary_embeddings)
            
            pipe.search_webpages.append(wp)
            
            self.run_callback()
            
    @phase(id="rank_results")
    def rank_results(self, pipe: Pipe):
        # Calculate distances between the article and search results
        
        logger.debug("Calculating distances...")
        for i, webpage in enumerate(pipe.search_webpages):
            # Calculate distance between article and search result
            webpage.distance = utils.cosine_similarity(
                pipe.article.summary_embeddings,
                webpage.summary_embeddings
            )
            
            logger.debug(f"[{i}] Distance for {webpage.url}: {webpage.distance}")
            
        logger.debug(f"Dropping results below the {DISTANCE_THRESHOLD} threshold...")
        
        # Drop the ones below a certain threshold        
        pipe.search_webpages_filtered = [
            webpage for webpage in pipe.search_webpages
            if abs(webpage.distance) >= DISTANCE_THRESHOLD
        ]
        
        n_pre = len(pipe.search_webpages)
        n_post = len(pipe.search_webpages_filtered)
        
        logger.debug(f"Dropped {n_pre - n_post} results. {n_post} remaining.")
        
        logger.debug(f"Sorting...")
        
        # Sort search results by distance
        pipe.search_webpages_filtered.sort(key=lambda x: x.distance)
        
        logger.debug(f"Top results:")
        # Log the top search results
        for webpage in range(0, min(5, len(pipe.search_webpages_filtered))):
            logger.debug(f"[{webpage}] {utils.short(pipe.search_webpages_filtered[webpage].url)} - Distance: {pipe.search_webpages_filtered[webpage].distance}")

    @phase(id="compare_results")
    def compare_results(self, pipe: Pipe):
        for i, webpage in enumerate(pipe.search_webpages):
            # Compare the article with each search result
            veredict = self.comparer.compare(
                pipe.article.markdown,
                webpage.summary
            )
            
            webpage.veredict = veredict
            
            logger.debug(f"[{i}] Comparison with {utils.short(webpage.url)}: {webpage.veredict}")
    
    @phase(id="draw_conclusion")
    def draw_conclusion(self, pipe: Pipe):
        # Calculate the total number
        verified_sources = [w for w in pipe.search_webpages_filtered if w.veredict == "verified"]
        unverified_sources = [w for w in pipe.search_webpages_filtered if w.veredict == "unverified"]
        unrelated_sources = [w for w in pipe.search_webpages_filtered if w.veredict == "unrelated"]
        
        verified_sources_count = len(verified_sources)
        unverified_sources_count = len(unverified_sources)
        unrelated_sources_count = len(unrelated_sources)
        
        total_sources = verified_sources_count + unverified_sources_count + unrelated_sources_count
        
        # Calculate the percentages
        verified_sources_percentage = (verified_sources_count / total_sources) if total_sources > 0 else 0
        unverified_sources_percentage = (unverified_sources_count / total_sources) if total_sources > 0 else 0
        unrelated_sources_percentage = (unrelated_sources_count / total_sources) if total_sources > 0 else 0
        
        # Set the percentages in the pipe
        pipe.verified_percentage = verified_sources_percentage
        pipe.unverified_percentage = unverified_sources_percentage
        pipe.unrelated_percentage = unrelated_sources_percentage
        
        logger.info(f"Verified sources: {verified_sources_count} ({verified_sources_percentage*100:.2f}%)")
        logger.info(f"Unverified sources: {unverified_sources_count} ({unverified_sources_percentage*100:.2f}%)")
        logger.info(f"Unrelated sources: {unrelated_sources_count} ({unrelated_sources_percentage*100:.2f}%)")
        
        # Get the most relevant sources
        top_sources = utils.limit(verified_sources, RAG_MAX_SOURCES_PER_TYPE) + utils.limit(unverified_sources, RAG_MAX_SOURCES_PER_TYPE)
        
        # Generate a conclusion based on the article and the search results
        conclusion = self.conclusion_generator.generate(
            pipe.article.summary,
            top_sources=top_sources
        )
        pipe.conclusion = conclusion
        
        if verified_sources_count > unverified_sources_count:
            pipe.verified = True
        else:
            pipe.verified = False
            
        logger.info(f"Article is: {pipe.verified}")
        
        logger.debug(f"Finished drawing the conclusion.")
    
    @phase(id="last_checks")
    def last_checks(self, pipe: Pipe):
        # Check for author
        if pipe.article.author:
            pipe.has_author = True
        else:
            logger.debug("The article does not have an author.")
            pipe.has_author = False
            
        # Check for sources
        if pipe.article.sources:
            pipe.has_sources = True
        else:
            logger.debug("The article does not have sources.")
            pipe.has_sources = False
            
        # TODO: Check for AI images
        pipe.has_ai_images = None
        
        # Compare the article's date with the current date
        current_date = datetime.now(timezone.utc)
        pipe.is_recent = (current_date - pipe.article.date).days <= RECENT_THRESHOLD
        if pipe.is_recent:
            logger.debug(f"Article is recent: {pipe.is_recent} (Threshold: {RECENT_THRESHOLD} days)")
        
        # Check for grammar issues
        grammar_issues = self.grammar_classifier.classify(
            pipe.article_html
        )
        pipe.has_grammar_issues = grammar_issues.has_grammar_issues
        pipe.grammar_issues = grammar_issues.where
        
        if pipe.has_grammar_issues:
            logger.debug(f"Article has grammar issues: {pipe.has_grammar_issues}")
            logger.debug(f"Grammar issues found in: {pipe.grammar_issues}")
        
        # Check the domain's reputation
        pipe.has_bad_reputation = pipe.domain_reputation <= -3
        
        # Get total token usage
        pdf_input_usage, pdf_output_usage = self.llm_pdf.get_usage()
        text_input_usage, text_output_usage = self.llm_text.get_usage()
        
        pipe.pdf_input_usage = pdf_input_usage
        pipe.pdf_output_usage = pdf_output_usage
        pipe.text_input_usage = text_input_usage
        pipe.text_output_usage = text_output_usage
        
        logger.debug(f"Multimodal model {self.llm_pdf.get_model()} used {pdf_input_usage} input tokens and {pdf_output_usage} output tokens.")
        logger.debug(f"Text-only model {self.llm_text.get_model()} used {text_input_usage} input tokens and {text_output_usage} output tokens.")
        
    def pipe_to_analysis(self, pipe: Pipe) -> AnalysisResult:
        assert pipe.phase, "The pipe phase is not set. Please run the detection process first."
        
        source_results = [
            SourceResult(
                url=webpage.url,
                title=webpage.title,
                summary=webpage.summary,
                
                veredict=webpage.veredict,
                distance=webpage.distance
            ) for webpage in pipe.search_webpages
        ] if pipe.search_webpages else None
        
        # Convert the pipe to AnalysisResult
        result = AnalysisResult(
            url = pipe.article.url,
            title=pipe.article.title,
            markdown=pipe.article.markdown,
            
            search_results=source_results,
            
            summary = pipe.article.summary,
            conclusion=pipe.conclusion,
            
            domain=pipe.domain.name,
            ip=pipe.domain.ip,
            ip_country=pipe.domain.country,
            ip_region=pipe.domain.region,
            
            verified_percentage=pipe.verified_percentage,
            unverified_percentage=pipe.unverified_percentage,
            unrelated_percentage=pipe.unrelated_percentage,
            
            verified=pipe.verified,
            
            has_author=pipe.has_author,
            has_sources=pipe.has_sources,
            has_ai_images=False,  # TODO: Implement AI image detection,
            is_recent=pipe.is_recent,
            has_grammar_issues=pipe.has_grammar_issues,
            has_bad_reputation=pipe.has_bad_reputation,
            
            phase=pipe.phase,
            error=pipe.error if hasattr(pipe, 'error') else None,
            refusal=pipe.refusal if hasattr(pipe, 'refusal') else None,
            exception=pipe.exception if hasattr(pipe, 'exception') else None,
        )
        
        return result
            
    def serialize_analysis(self, result: AnalysisResult) -> str:
        """
        Convert the analysis to a dict.
        """
        return utils.dataclass_to_dict(result)
    
    def get_serialized_analysis(self, pipe: Pipe) -> AnalysisResult:
        """
        Convert the pipe to an AnalysisResult object and return a dict.
        
        :param pipe: The Pipe object containing the analysis data.
        :return: A dict representation of the analysis.
        """
        analysis  = self.pipe_to_analysis(pipe)
        return self.serialize_analysis(analysis)
    
    def is_running(self) -> bool:
        """
        Check if the detector is running.
        
        :return: True if the detector is running, False otherwise.
        """
        return self.running
    
    def register_callback(self, callback: callable):
        """
        Set a callback function to be called when the detection is finished.
        
        :param callback: The callback function to set.
        """
        self.callback = callback
        
    def run_callback(self):
        """
        Run the callback function with the serialized pipe.
        """
        if self.callback:
            if self.pipe:
                serialized_analysis = self.get_serialized_analysis(self.pipe)
                self.callback(serialized_analysis)
                
            self.callback(None)  
            
    def get_pipe(self) -> Pipe:
        """
        Get the current pipe.
        
        :return: The current Pipe object.
        """
        return self.pipe
    
    def set_pipe(self, pipe: Pipe):
        """
        Set the current pipe.
        
        :param pipe: The Pipe object to set.
        """
        self.pipe = pipe
    
if __name__ == "__main__":
    
    debug.setup()
    
    # Initialize the fake news detector
    fnd = FakeNewsDetector()
    
    url = "https://elpais.com/espana/2025-05-14/una-explosion-provoca-un-incendio-en-una-nave-de-productos-quimicos-en-la-localidad-sevillana-de-alcala-de-guadaira.html"
    
    analysis = fnd.run(url, mock = True)
    # Print the analysis result
    print(fnd.serialize_analysis(analysis))