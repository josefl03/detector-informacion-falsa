from loguru import logger

import fake_news_detector.debug as debug

def phase(id: str, monitor: bool = False):
    """
    Decorator to mark a function as a phase in the pipeline.
    
    Args:
        id (str): The ID of the phase.
        monitor (bool): Send data periodically to the server. Defaults to False.
    
    Returns:
        function: The decorated function.
    """
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Return if a phase already returned a value
            
            if len(args) != 2:
                logger.error(f"Phase {id} received {len(args)} arguments, expected 1")
            
            obj = args[0]
            pipe = args[1] # pipe arg
            
            logger.info(f"Starting phase: {id}")
            
            pipe.phase = id
            
            # Execute the function
            ret = func(*args, **kwargs)

            # Save the pipe state
            if id != "init":
                debug.save_pipe(pipe, name=id)
            
            # Check if the phase returned something
            if ret:
                logger.error(f"Phase {id} returned a value")
                
            # Send data and phase to the callback (if any)
            obj.run_callback()
        wrapper.phase_id = id
        return wrapper
    return decorator