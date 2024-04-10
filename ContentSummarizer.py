import os
import openai
import requests
from bs4 import BeautifulSoup
import traceback
import datetime
from praw.models import MoreComments

openai.api_key = os.getenv("THESIS_OPENAI_API_KEY")

class ContentSummarizer:
    def __init__(self, model="gpt-4", system_prompt="You are Prism (u/PrismChatbot on Reddit), a chatbot that helps social media users navigate news and public discourse by providing summaries and unbiased analysis of articles and comments."):
        self.model=model
        self.system_prompt = system_prompt
    
    def summarize_top_comments(self, title, comments_text, custom_prompt=""):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": 
                 f"""Briefly summarize the following top Reddit comments concerning the given article. 
                    Note the main, important viewpoints/arguments in plain text. Keep your response to less than 150 words. 
                    Number the key points and provide a short label for each one. {custom_prompt}
                    Article title: {title}.

                    Comments: {comments_text},

                    [End of Comments]
                    Now, summarize the comments in a structured way, in plain text. Keep your response to less than 150 words. 
                    """
                }
            ]
        )

        start_disclaimer = "AI-written summary of the top comments by the Prism Project: "
        end_disclaimer = " Prism is built by student researchers aiming to help improve social media news and dialogue consumption. Check out our website: https://prismchatbot.framer.ai for more information!"
        return start_disclaimer + response['choices'][0]['message']['content'] + end_disclaimer

        
    def summarize_article_from_url(self, title, url, custom_prompt=""):

        website_data = self._get_website_data([url])
        if not isinstance(website_data[0], dict):
            raise Exception(f"Could not parse this url: {url}")

        metadata = website_data[0]["metadata"]
        article_text = website_data[0]["article_text"]
        custom_prompt = custom_prompt

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": 
                    f"""Briefly summarize the following article in three concise sentences. {custom_prompt}
                    If the following title is misleading, mention why it might be misleading, 
                    but if it is NOT misleading, DO NOT say anything about the title, and ONLY summarize the article.
                    Title: {title}. 
                    Article Text: {article_text}"""},
            ]
        )

        start_disclaimer = "AI-written summary of this article by Prism: "
        end_disclaimer = " Prism is built by student researchers aiming to help improve social media news and dialogue consumption. Check out our website: https://prismchatbot.framer.ai for more information!"
        return start_disclaimer + response['choices'][0]['message']['content'] + end_disclaimer
    
    def compare_articles_from_urls(self, titles, urls, custom_prompt=""):
        website_data = self._get_website_data(urls)
        if len(website_data) != 2:
            raise Exception("URL_ACCESS_DENIED")
        title = titles[0]
        article_text = website_data[0]["article_text"]
        title2 = titles[1]
        article_text2 = website_data[1]["article_text"]
        custom_prompt = custom_prompt

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": 
                    f"""Compare the following two articles. 
                    Note points of factual agreement, points of factual disagreement, 
                    and differences in viewpoint/emphasis/framing. {custom_prompt}
                    Article 1: {title}. Article 2: {title2}. 
                    Article 1 Text: {article_text}. Article 2 Text: {article_text2}"""
                },
            ]
        )

        return response['choices'][0]['message']['content']
    


    def _get_website_data(self, urls):
        data = [] 
        for url in urls:
            try:
                # Send an HTTP request to the URL
                response = requests.get(url)
                response.raise_for_status()

                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')

                metadata = self._build_metadata(soup, url)
                
                # Find and collect all the text in paragraph tags
                paragraphs = soup.find_all('p')
                article_text = '\n'.join([para.text for para in paragraphs])

                website_data = {"article_text": article_text, "metadata": metadata}
                data.append(website_data)
            except requests.RequestException as e:
                return f"An error occurred: {e}", ""
        
        return data



    def _build_metadata(self, soup, url):
        """Build metadata from BeautifulSoup output."""
        metadata = {"source": url}
        if title := soup.find("title"):
            metadata["title"] = title.get_text()
        if description := soup.find("meta", attrs={"name": "description"}):
            metadata["description"] = description.get("content", "No description found.")
        if html := soup.find("html"):
            metadata["language"] = html.get("lang", "No language found.")
        return metadata


summarizer = ContentSummarizer()
data = summarizer._get_website_data(["https://www.washingtonpost.com/climate-environment/2023/09/19/electric-cars-better-environment-fossil-fuels/", ""])