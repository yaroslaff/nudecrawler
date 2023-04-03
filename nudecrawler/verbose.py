verbose = False

def get_verbose():
    return verbose

def printv(*args):
    if not verbose:
        return
    print(f"...", *args)