import re

from django.utils.safestring import mark_safe
from django import template

register = template.Library()

hashtag_pattern = re.compile(r"(?P<start>.?)#(?P<hashtag>[A-Za-z_]+)(?P<end>.?)")
user_pattern = re.compile(r"(?P<start>.?)@(?P<user>[A-Za-z0-9_]+)(?P<end>.?)") 

@register.filter(name='twitterfy')
def twitterfy(tweet):
    
    # find hashtags, replace with link to search
    link = r'\g<start>#<a href="http://search.twitter.com/search?q=\g<hashtag>"  title="#\g<hashtag> search Twitter">\g<hashtag></a>\g<end>'
    text = hashtag_pattern.sub(link,tweet)
    
    # find usernames, replace with link to profile
    link = r'\g<start>@<a href="http://twitter.com/\g<user>"  title="#\g<user> on Twitter">\g<user></a>\g<end>'
    text = user_pattern.sub(link,tweet)
    
    return mark_safe(text)
