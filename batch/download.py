from datetime import datetime
import argparse
from loguru import logger
import pickle
from typing import Tuple, List
import os

# # Add the library
import sys
sys.path.append(".")

from fake_news_detector import FakeNewsDetector
from fake_news_detector import utils, debug

URL_FILENAME_MAX = 80

RESULTS_PATH = "batch/results/{name}/"

ANALYSIS_EXT = ".ays"
PIPE_EXT = ".pipe"

SUCCESS_PATH = "success/"
ERROR_PATH = "error/"
REFUSAL_PATH = "refusal/"
EXCEPTION_PATH = "exception/"

success_count = 0
error_count = 0
refusal_count = 0
exception_count = 0
skip_count = 0

TXT_BASE = """\
Batch Analysis Results

Success: {success}
Error: {error}
Refusal: {refusal}
Exception: {exception}
Skip: {skip}

Total: {total}"""

fnd = None

def limit_path(path: str, max_length: int = URL_FILENAME_MAX) -> str:
    """
    Limit the path to a maximum length, truncating if necessary.
    """
    if len(path) > max_length:
        return path[:max_length]
    return path

def search_url(url: str) -> bool:
    for dir in [SUCCESS_PATH, ERROR_PATH, REFUSAL_PATH, EXCEPTION_PATH]:
        if os.path.exists(os.path.join(RESULTS_PATH, dir, limit_path(utils.url_to_filepath(url)) + PIPE_EXT)):
            return True

def analyze(url: str, position: Tuple[int, int] = None):
    """
    Analyze the news article at the given URL.
    """
    global success_count, error_count, refusal_count, exception_count, fnd,  skip_count
    
    index_str = ""
    if position:
        index_str = f"[{position[0]}/{position[1]}] "
        
    logger.info("-"*50)
    
    url_file = limit_path(utils.url_to_filepath(url))
    
    if search_url(url):
        logger.info(index_str + f"Already analyzed. Skipping: {url}")
        skip_count += 1
        return "skipped"
    
    
    logger.info(index_str + f"Analyzing URL: {url}")
    
    result = None
    fnd = FakeNewsDetector(custom_logger=True)
    try:
        
        result = fnd.run(url)
        
        if result is None:
            logger.warning(index_str + "Stopping...")
            return "interrupted"
    except Exception as e:
        logger.error(index_str + f"Analysis exception: {e}")
    finally:
        if result is None:
            return "interrupted"
        
        pipe = fnd.get_pipe()
        
        final_path = ""
        if pipe.error:
            final_path = os.path.join(RESULTS_PATH, ERROR_PATH)
            logger.info(index_str + f"Analysis failed with error.")
            error_count += 1
            
        elif pipe.refusal:
            final_path = os.path.join(RESULTS_PATH, REFUSAL_PATH)
            logger.info(index_str + f"Analysis failed with refusal.")
            refusal_count += 1
            
        elif pipe.exception:
            final_path = os.path.join(RESULTS_PATH, EXCEPTION_PATH)
            logger.info(index_str + f"Analysis failed with exception.")
            exception_count += 1
            
        else:
            final_path = os.path.join(RESULTS_PATH, SUCCESS_PATH)
            logger.info(index_str + f"Analysis completed successfully.")
            success_count += 1
            
        # Success
        pipe_path = os.path.join(final_path, url_file + PIPE_EXT)
        analysis_path = os.path.join(final_path, url_file + ANALYSIS_EXT)
        
        utils.make_parents(analysis_path)
        
        # Save the pipe
        with open(pipe_path, "wb") as f:
            pickle.dump(pipe, f)
        
        # Save the analysis
        with open(analysis_path, "wb") as f:
            pickle.dump(result, f)
            
        logger.debug(index_str + f"Analysis saved to: {analysis_path}")
        logger.debug(index_str + f"Pipe saved to: {pipe_path}")
        
        return "ok"
    
def analyze_batch(urls):
    """
    Analyze a batch of news articles at the given URLs.
    """
    global success_count, error_count, refusal_count, exception_count
    
    total = len(urls)
    logger.info(f"Starting batch analysis of {total} URLs...")
    
    start_time = datetime.now()
    
    for i, url in enumerate(urls):
        result = analyze(url, position=(i + 1, total))
        
        if result == "interrupted":
            logger.warning("Batch analysis interrupted.")
            break
            
    # Save results to txt
    results_path = RESULTS_PATH + "results.txt"
    with open(results_path, "w") as f:
        f.write(TXT_BASE.format(
            success=success_count,
            error=error_count,
            refusal=refusal_count,
            exception=exception_count,
            total=total,
            skip=skip_count
        ))
        
    elapsed_time = datetime.now() - start_time
    elapsed_time_str = str(elapsed_time).split(".")[0]  # Remove microseconds
        
    logger.success("Finished analyzing batch.")
    logger.info(f"Results saved to: {results_path}")
    logger.info("")
    logger.info(f"Success: {success_count}")
    logger.info(f"Error: {error_count}")
    logger.info(f"Refusal: {refusal_count}")
    logger.info(f"Exception: {exception_count}")
    logger.info(f"Total: {total}")
    logger.info("")
    logger.info(f"Time elapsed: {elapsed_time_str}")

def main():
    global RESULTS_PATH
    
    parser = argparse.ArgumentParser(description="Batch analyze news articles.")
    parser.add_argument("-f", "--file", required=False, help="Path to file containing URLs (one per line)")
    parser.add_argument("-u", "--url", required=False, help="URL or file to analyze")
    parser.add_argument("-n", "--name", required=False, help="Name of the analysis")
    args = parser.parse_args()
    
    if args.name:
        RESULTS_PATH = RESULTS_PATH.format(name=args.name)
    else:
        RESULTS_PATH = RESULTS_PATH.format(time=datetime.now().strftime("%Y%m%d_%H%M%S"))
        
    # Setup logging
    log_file = os.path.join(RESULTS_PATH, "latest.log")
    debug.setup(log_file=log_file)
    
    # Create the folder
    utils.make_parents(RESULTS_PATH)
    logger.info(f"Results will be saved to: {RESULTS_PATH}")
    
    if args.url:
        url = args.url
    
        analyze(url)
    if args.file:
        file = args.file
        
        urls = []
        try:
            with open(file, "r") as f:
                urls = [line.strip().split(",")[0] for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"File not found: {file}")
            return
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            
        if not urls:
            logger.error("No URLs found in the file.")
            return
        
        analyze_batch(urls)
        
if __name__ == "__main__":
    main()