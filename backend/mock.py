import time
import random
import sys

from fake_news_detector.fake_news_detector import FakeNewsDetector, utils

BASE_FOLDER = "backend/mocks/"
PHASE_MOCKS = [
    "20250612_171808_673_check_domain.pkl",
    "20250612_171814_428_download_article.pkl",
    "20250612_171851_848_parse_article.pkl",
    "20250612_171856_528_process_article.pkl",
    "20250612_171857_763_search.pkl",
    "20250612_172105_570_process_search.pkl",
    "20250612_172105_757_rank_results.pkl",
    "20250612_172118_627_compare_results.pkl",
    "20250612_172131_834_draw_conclusion.pkl",
    "20250612_172137_213_last_checks.pkl",
]

PHASE_MOCKS = [
    #"../../batch/results/fncs200_gemini/success/haynoticia.es_la-palabra-haiga-aceptada-la-rae9999_.pipe",
    "../../batch/results/fncs200_gemini/success/haynoticia.es_movistar-vodafone-orange-bloquearan-los-torrents-partir-mayo_.pipe"
]
PHASES = [
    "check_domain",
    "download_article",
    "parse_article",
    "process_article",
    "search",
    "process_search",
    "rank_results",
    "compare_results",
    "draw_conclusion",
    "last_checks",
    "finished"
]

SIMULATION_TIME = 0 # seconds
#SIMULATION_TIME = random.uniform(1.0, 4.0)

def run_mocks(fnd: FakeNewsDetector, callback: callable):
    """
    Run the mock data for the FakeNewsDetector.
    Args:
        fnd (FakeNewsDetector): The instance of FakeNewsDetector to run the mocks on.
        callback (callable): The callback function to call after each phase.
    """
    # for phase in PHASE_MOCKS:
    #     run_mock(fnd, callback, phase)
    #     time.sleep(SIMULATION_TIME)
    
    for phase in PHASES:
        run_mock(fnd, callback, obj=PHASE_MOCKS[0], phase=phase)
        time.sleep(SIMULATION_TIME)
        
    # run final phase
    #run_mock(fnd, callback, "finished")
    #run_mock(fnd, callback, obj=PHASE_MOCKS[0], phase="finished")

def run_mock(fnd: FakeNewsDetector, callback: callable, obj: str, phase=None):
    """
    Run the mock data for the FakeNewsDetector.
    
    Args:
        fnd (FakeNewsDetector): The instance of FakeNewsDetector to run the mocks on.
        callback (callable): The callback function to call after each phase.
    """
    if phase != "finished":
        pipe = utils.load_obj(BASE_FOLDER + obj)
        pipe.phase = phase
        pipe.verified = True
        fnd.set_pipe(pipe)
    else:
        fnd.pipe.phase = "finished"
        pipe = fnd.get_pipe()
    
    analysis = fnd.pipe_to_analysis(pipe)
    analysis_json = fnd.serialize_analysis(analysis)
    
    callback(analysis_json)
    
if __name__ == "__main__":
    # Example usage
    fnd = FakeNewsDetector()
    
    def mock_callback(data):
        print(f"Mock callback received data: {data[:200].replace('\n', '')}...")  # Print first 50 characters
    
    run_mocks(fnd, mock_callback)