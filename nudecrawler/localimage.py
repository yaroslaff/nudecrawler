from PIL import Image, UnidentifiedImageError
from .exceptions import BoringImage, ProblemImage

def basic_check(path, min_w, min_h):
    """ check image and raise exception """
    
    if not (min_w or min_h):        
        return
    
    try:
        img = Image.open(path)
    except UnidentifiedImageError:
        raise ProblemImage('Incorrect image')
    w, h = img.size

    if min_w and w<min_w:
        raise BoringImage(f'Image {w}x{h} is too small (min_w: {min_w})')

    if min_h and w<min_h:
        raise BoringImage(f'Image {w}x{h} is too small (min_h: {min_h})')
    
