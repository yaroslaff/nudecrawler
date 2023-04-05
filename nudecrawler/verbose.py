import inspect
import os

verbose = False

def get_verbose():
    return verbose

def printv(*args):
    if not verbose:
        return
    
    if False:
        frame = inspect.stack()[1]
        location = os.path.basename(frame.filename) + ':' + str(frame.lineno)
        print(f"...", f"({location})", *args)
    else:
        print(f"...", *args)
    