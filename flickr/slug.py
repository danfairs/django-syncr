from flickr.models import Photo
from datetime import datetime

def get_unique_slug_for_photo(taken_date, proposed_slug):
    l=1
    calculate_slug = proposed_slug    
    while check_slug_photo(taken_date, propsed_slug):    
        propsed_slug = calculate_slug + '-' + str(l)
        l = l+1
    return propsed_slug    
        
def check_slug_photo(taken_date, proposed_slug):
    if Photo.objects.filter(pub_date__year=taken_date.year, pub_date__month=taken_date.month, pub_date__day=taken_date.day).filter(slug=proposed_slug):
        return True
    else:
        return False