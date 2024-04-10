from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import os
from datetime import datetime, timezone
import praw


uri = "mongodb+srv://PrismChatbotDBUser:" + os.environ["PRISMCHATBOT_CLUSTER_PASSWORD"] +  "@prismchatbotcluster0.ytanous.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    # print("Pinged your deployment. You successfully connected to MongoDB!")
    db = client['RedditDB']
    submissions_collection = db['submissions']
    comments_collection = db['comments']
    settings_collection = db['settings']
except Exception as e:
    print(e)


def insert_reply_to_comment(user_comment, bot_comment, item_information):
    bot_comment_datetime = datetime.now(timezone.utc)
    comments_collection.insert_one({"_id" : user_comment.id, "user_comment_body" : user_comment.body, "links" : item_information["links"], "command" : item_information["command"],
                                    "model" : item_information["model"] , "custom_prompt" : item_information["custom_prompt"], "user_comment_datetime" : item_information["user_comment_datetime"],
                                    "submission_id" : user_comment.submission.id, "submission_url":user_comment.submission.url, "submission_title" : user_comment.submission.title,
                                    "bot_comment_body": bot_comment.body, "bot_comment_id": bot_comment.id, "bot_comment_datetime": bot_comment_datetime})

def insert_response_to_submission(submission, response, response_type):
    submissions_collection.insert_one({"response_type":response_type, "submission_url":submission.url, "submission_permalink":submission.permalink, "submission_title": submission.title, 
                                       "subreddit_display_name":submission.subreddit.display_name, "response_body" : response.body, "response_created_utc" : response.created_utc})

def get_submission(submission):
    permalink = submission.permalink
    return submissions_collection.find_one({"submission_permalink": permalink})

def get_comment(comment_id):
    return comments_collection.find_one({"_id": comment_id})

def get_settings():
    return settings_collection.find_one({"subreddits": {"$exists": True}})


              
# reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
#                      client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
#                      user_agent="Prism (by u/pickle269)",
#                      username="pickle269",
#                      password=os.getenv('REDDIT_PASSWORD'))
# submission = reddit.submission("18ajefm")
# comment = reddit.comment("kbzvu6x")
# response_type = "summarize_article"

# insert_response_to_submission(submission, comment, response_type)