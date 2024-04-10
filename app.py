import praw
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from ContentSummarizer import ContentSummarizer
import mongodb_client as mongo_client
import random

# Flask App Initialization
app = Flask(__name__)

# Initialize PRAW and ContentSummarizer
reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                     client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                     user_agent="Prism (by u/pickle269)",
                     username="pickle269",
                     password=os.getenv('REDDIT_PASSWORD'))
content_summarizer = ContentSummarizer()


settings = mongo_client.get_settings()
SUBREDDITS = settings["subreddits"]
LIKES_THRESHOLD = settings["likes_threshold"]  
COMMENTS_THRESHOLD = settings["comments_threshold"]

def check_and_summarize_posts():
    """Function to check posts and summarize if they meet the threshold."""
    subreddit = random.choice(SUBREDDITS)
    for submission in reddit.subreddit(subreddit).hot(limit=10):  # Fetch recent 10 posts
        try:
            submission_in_db = mongo_client.get_submission(submission)
            if submission_in_db is None or submission_in_db["response_type"] != "summarize_article":
                if submission.is_self is not True and submission.score > LIKES_THRESHOLD:
                    # Summarize the post content
                    summary = content_summarizer.summarize_article_from_url(submission.title, submission.url)
                    comment = submission.reply(summary)
                    mongo_client.insert_response_to_submission(submission, comment, "summarize_article")
                    print("summarized article")
            else:
                "already summarized article"

            if submission_in_db is None or submission_in_db["response_type"] != "summarize_top_comments": 
                if submission.num_comments > COMMENTS_THRESHOLD:
                    # Summarize top comments
                    top_comments = [comment.body for comment in submission.comments if isinstance(comment, praw.models.Comment)]
                    summary = content_summarizer.summarize_top_comments(submission.title, " ".join(top_comments))
                    comment = submission.reply(summary)
                    mongo_client.insert_response_to_submission(submission, comment, "summarize_top_comments")
                    print("summarized top comments")
            else:
                "already summarized top comments"
        except Exception as e:
            print(f"Error processing submission {submission.id}: {e}")

# Flask Routes
@app.route('/')
def index():
    return "Reddit Bot is running!"

@app.route('/trigger', methods=['GET','POST'])
def trigger_bot():
    try:
        check_and_summarize_posts()
        return jsonify({"status": "success", "message": "Bot triggered successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "success", "message": "Bot is operational."}), 200

# Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_summarize_posts, 'interval', minutes=20)
scheduler.start()

if __name__ == '__main__':
    app.run(threaded=True, debug=True, port=8000)
