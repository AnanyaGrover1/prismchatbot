import requests
import json

def get_top_posts(n=10):
    # Get the ids of the top stories
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    response.raise_for_status()  # Check if the request was successful
    top_stories_ids = response.json()

    # Get the details of the top 10 stories
    top_stories = []
    for story_id in top_stories_ids[:n]:
        response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
        response.raise_for_status()  # Check if the request was successful
        story_data = response.json()
        top_stories.append(story_data)
    
    return top_stories

def fetch_comment(comment_id):
    response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{comment_id}.json')
    response.raise_for_status()
    comment_data = response.json()
    if comment_data is None:
        print(f'Warning: No data returned for comment ID {comment_id}')
        return {}
    return comment_data

def search_comments_for_keyword(comment, keyword):
    if comment and 'text' in comment and keyword.lower() in comment['text'].lower():
        print(f'Comment ID: {comment["id"]}, Text: {comment["text"]}')

    if comment and 'kids' in comment:  # If the comment has replies
        for kid_id in comment['kids']:
            kid_comment = fetch_comment(kid_id)
            search_comments_for_keyword(kid_comment, keyword)

def find_keyword_in_posts(posts, keyword):
    for post in posts:
        if 'kids' in post:  # If the post has comments
            for comment_id in post['kids']:
                comment = fetch_comment(comment_id)
                search_comments_for_keyword(comment, keyword)


# Get the top 10 Hacker News posts
top_10_posts = get_top_posts(5)

# Print the title and URL of each post
for i, post in enumerate(top_10_posts, 1):
    print(f"{i}. {post['title']} (URL: {post['url']})")


# We would put our bot's @ here
keyword = "job automation"
find_keyword_in_posts(top_10_posts, keyword)
