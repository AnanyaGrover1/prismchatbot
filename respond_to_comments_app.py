import praw
from praw.models import Comment
from ContentSummarizer import ContentSummarizer 
from mongodb_client import get_comment, insert_reply_to_comment
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback 
import re
from flask import Flask
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask

executor = ThreadPoolExecutor(1)  # Create a thread pool with a single thread
future = None
app = Flask(__name__)
REDDIT_USERNAME = "u/prismchatbot"



def get_data_from_comment(item):
    print("Processing comment...")
    if "summarize article" in item.body.lower():
        command = "summarize_article"
    elif "compare" in item.body.lower():
        command = "compare"
    elif "summarize comments" in item.body.lower():
        command = "summarize_comments"
    else:  
        command = None
    
    custom_prompt = item.body.lower().replace(REDDIT_USERNAME, "")
    
    # model
    if "gpt-3.5-turbo" in item.body.lower():
        model = "gpt-3.5-turbo"
        TOKEN_LIMIT = 6000
    elif "gpt-3.5-turbo-16k" in item.body.lower():
        model = "gpt-3.5-turbo-16k"
        TOKEN_LIMIT = 14000
    elif "gpt-4" in item.body.lower():
        model = "gpt-4"
        TOKEN_LIMIT = 6000
    else:
        model = "gpt-4-1106-preview"
        TOKEN_LIMIT = 6000
    
    # parse submission/comment for Summarize Article or Compare Article Task
    if command == "summarize_article" or command == "compare":
        soup = BeautifulSoup(item.body_html, 'html.parser')
        prismchatbot_pattern = re.compile(r'/u/prismchatbot', re.IGNORECASE)
        links = [a['href'] for a in soup.find_all('a', href=True) if not prismchatbot_pattern.search(a['href'].lower())]

        if len(links) == 0:
            links = [item.submission.url]
        else:
            if command == "compare" and len(links) == 1:
                links = [item.submission.url, links[0]]

    else:
        links = []
    
    # parse top comments for Summarize Comments Task
    if command == "summarize_comments":
        print("Processing comments for summarize_comments...")
        item.submission.comments.replace_more(limit=0)
        comments = item.submission.comments.list()
        count_token_estimate = 0
        comments_text = ""
        for i, comment in enumerate(comments):
            username = "User" + str(i)
            if comment is not None and comment.author is not None:
                username = comment.author.name
            comment_text = "Redditor: " + username + "'s comment:" + comment.body
            if count_token_estimate + len(comment_text) <= TOKEN_LIMIT:
                comments_text += '\n' + comment_text
                count_token_estimate += (len(comment_text) / 5)
    else:
        comments_text = ""


    # process_time
    user_comment_datetime = datetime.now(timezone.utc)

    # title
    title = item.submission.title
    
    item_information = {"title": title, "command" : command, "model": model, "custom_prompt": custom_prompt, "links": links, "user_comment_datetime" :user_comment_datetime, "comments_text" : comments_text}
    print(item_information)
    return item_information

def reddit_poller():
    reddit = praw.Reddit(
        client_id="giv8-P92BYosjv8sz_8nCQ",
        client_secret="LyGvv6euIxzSCrYMPPHCPnZ3z6qVSA",
        user_agent="Prism (by u/PrismChatbot)", 
        password="PrincetonThesis2023$",
        username="PrismChatbot"
    )
    try:
        print("Starting bot...")
        for item in reddit.inbox.stream(skip_existing=True): 
            try:
                if isinstance(item, Comment) and REDDIT_USERNAME in item.body.lower():
                    print("received comment")
                    item_information = get_data_from_comment(item)
                    response = ""
                    summarizer = ContentSummarizer(model=item_information["model"])
                    stripped_body = item.body.lower().replace(REDDIT_USERNAME, "").strip()

                    #  User did not tag bot properly
                    if item_information["command"] == None:
                        response = "Prism responds to 1) 'summarize article' to summarize from the post or one you give, 2) 'summarize comments' to summarize the post's comments, or 3) 'compare' to compare two articles from the post and/or one(s) you give."
                        reply = item.reply(response)
                        reddit.redditor(str(item.author.name)).message(subject="Your Summary from u/PrismChatbot", message=response)
                        insert_reply_to_comment(item, reply, item_information)
                        print("Replied to comment.")
                        continue
                    # Summarize 1 link -- either a given one or the submission
                    elif item_information["command"] == "summarize_article":
                        if len(item_information["links"]) == 1:
                            try:
                                response = summarizer.summarize_article_from_url(item_information["title"], item_information["links"][0], item_information["custom_prompt"])
                            except Exception as e:
                                response = str(e)
                                traceback.print_exc()
                        else:
                            response = "Prism can only summarize one article!"
                    
                    # Compare 2 links -- either 2 given ones or the submission and a given one
                    elif item_information["command"] == "compare":
                        if len(item_information["links"]) == 2:
                            try:
                                response = summarizer.compare_articles_from_urls(item_information["title"], item_information["links"], item_information["custom_prompt"])
                            except Exception as e:
                                response = str(e)
                                traceback.print_exc()
                        else:
                            response = "Prism can only compare two articles!"
                    
                    elif item_information["command"] == "summarize_comments":
                        try:
                            response = summarizer.summarize_comments(item_information["title"], item_information["comments_text"], item_information["custom_prompt"])
                        except Exception as e:
                            response = str(e)
                            traceback.print_exc()
                    
                    response += "\n" + "Prism is built by student researchers aiming to help make social media news and dialogue consumption more positive. Check out our website:" + "https://prismchatbot.framer.ai/ " + "for more information!"
                    reply = item.reply(response)
                    reddit.redditor(str(item.author.name)).message(subject="Your Summary from u/PrismChatbot", message=response)
                    insert_reply_to_comment(item, reply, item_information)
                    print("Replied to comment.")
                else:
                    print(f"Other inbox item: {item}", type(item))
            except Exception as e:
                print(e)
        
    except KeyboardInterrupt:
        print("Bot stopped by user.")

def start_polling():
    global future
    if future is None or future.done():
        future = executor.submit(reddit_poller)
    else:
        print("Polling thread already running.")


def stop_polling():
    global future
    if future is not None and not future.done():
        future.cancel()
        print("Polling thread cancelled.")
    else:
        print("No active polling thread to cancel.")


@app.route('/start')
def start():
    start_polling()
    return "Started polling Reddit inbox stream."

@app.route('/stop')
def stop():
    stop_polling()
    return "Stopped polling Reddit inbox stream."

if __name__ == "__main__":
    app.run(debug=True)
