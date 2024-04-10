import praw
from praw.models import Comment
from ContentSummarizer import ContentSummarizer 
from mongodb_client import get_comment, insert_reply_to_comment
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback 
import re

REDDIT_USERNAME = "u/prismchatbot"


def get_data_from_comment(item):
    if "summarize article" in item.body.lower():
        command = "summarize_article"
    elif "compare" in item.body.lower():
        command = "compare"
    elif "summarize comments" in item.body.lower():
        command = "summarize_comments"
    else:  
        return {"command" : None}
    
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
            comment_text = "User" + str(i) + "'s comment:" + comment.body
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
    return item_information

def main():
    
    reddit = praw.Reddit(
        client_id="giv8-P92BYosjv8sz_8nCQ",
        client_secret="LyGvv6euIxzSCrYMPPHCPnZ3z6qVSA",
        user_agent="Prism Chatbot (by u/PrismChatbot)", 
        password="PrincetonThesis2023$",
        username="PrismChatbot"
    )
    try:
        print("Starting bot...")
        for item in reddit.inbox.stream(skip_existing=True): 
            # Check if someone tagged our bot
            try:
                if isinstance(item, Comment) and REDDIT_USERNAME in item.body.lower():
                    
                    item_information = get_data_from_comment(item)

                    
                    response = ""
                    summarizer = ContentSummarizer(model=item_information["model"])
                    stripped_body = item.body.lower().replace(REDDIT_USERNAME, "").strip()

                    #  User did not tag bot properly
                    if item_information["command"] == None:
                        response = "PrismChatbot responds to 1) 'summarize article' to summarize from the post or one you give, 2) 'summarize comments' to summarize the post's comments, or 2) 'compare' to compare two articles from the post and/or one(s) you give."
                    
                    # Summarize 1 link -- either a given one or the submission
                    elif item_information["command"] == "summarize_article":
                        if len(item_information["links"]) == 1:
                            try:
                                response = summarizer.summarize_article_from_url(item_information["title"], item_information["links"][0], item_information["custom_prompt"])
                            except Exception as e:
                                response = str(e)
                                traceback.print_exc()
                        else:
                            response = "PrismChatbot can only summarize one article!"
                    
                    # Compare 2 links -- either 2 given ones or the submission and a given one
                    elif item_information["command"] == "compare":
                        if len(item_information["links"]) == 2:
                            try:
                                response = summarizer.compare_articles_from_urls(item_information["title"], item_information["links"], item_information["custom_prompt"])
                            except Exception as e:
                                response = str(e)
                                traceback.print_exc()
                        else:
                            response = "PrismChatbot can only compare two articles!"
                    
                    elif item_information["command"] == "summarize_comments":
                        try:
                            response = summarizer.summarize_comments(item_information["title"], item_information["comments_text"], item_information["custom_prompt"])
                        except Exception as e:
                            response = str(e)
                            traceback.print_exc()
                    
                    reply = item.reply(response)
                    reddit.redditor(str(item.author.name)).message(subject="Your Summary from u/PrismChatbot", message=response)
                    insert_reply_to_comment(item, reply, item_information)
                    print("Replied to comment.")
                
                else:
                    print(f"Other inbox item: {item}", type(item))
            except Exception as e:
                print(e)
        
    except KeyboardInterrupt:
        print(" Bot stopped by user.")


if __name__ == "__main__":
    main()