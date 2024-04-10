import praw
from praw.models import Comment
from ContentSummarizer import ArticleSummarizer 
from mongodb_client import get_comment, insert_reply_to_comment
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback 
import re
import ast

def extract_links_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    prismchatbot_pattern = re.compile(r'/u/prismchatbot', re.IGNORECASE)
    return [a['href'] for a in soup.find_all('a', href=True) if not prismchatbot_pattern.search(a['href'].lower())]


REDDIT_USERNAME = "u/prismchatbot"
reddit = praw.Reddit(
    client_id="giv8-P92BYosjv8sz_8nCQ",
    client_secret="LyGvv6euIxzSCrYMPPHCPnZ3z6qVSA",
    user_agent="Prism Chatbot (by u/PrismChatbot)", 
    password="PrincetonThesis2023$",
    username="PrismChatbot"
)

for message in reddit.inbox.messages(limit=5):
    print(message.subject)
