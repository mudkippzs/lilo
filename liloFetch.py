
from goose import Goose

from collections import defaultdict
from string import punctuation
from heapq import nlargest
from pymessenger import Bot, Element

import nltk
import pprint
import praw
import logging
import tldextract
import random

logging.raiseExceptions = False

class rAPI_Service():

    reddit_service = None

    def __init__(self):
        self.reddit_service = self.connect()
        return None

    def connect(self):
        reddit = praw.Reddit(client_id='J9ccJUbL7QSHaA',
                     client_secret='vVSFAE1gyzJW4_VL_cXQPY17CSc',
                     password='password1!',
                     user_agent='testscript by /u/spiceminerjoe',
                     username='spiceminerjoe')
        return reddit

    def get_api_user(self):
        if self.reddit_service is None:
            self.connect()

        return self.reddit_service.user.me()

    def check_articles_are_selfPost(self, articles):
        sub_is_self_posts = False
        for article in articles:
            if article.is_self is False:
                sub_is_self_posts = False
            else:
                sub_is_self_posts = True

        return sub_is_self_posts

    def check_sub_exists(self, sub):
        real_sub = False
        if self.reddit_service is None:
            self.connect()
        try:
            subreddit = self.reddit_service.subreddit(sub)
            articles = [article for article in subreddit.hot(limit=25)]
            sampleArticle = articles[random.randint(0,len(articles) - 1)]
            count = len(articles)
            selfPost_sub = self.check_articles_are_selfPost(articles)

            if count >= 10 and selfPost_sub is False:
                print("[i] Sub Exists:\t" + sub)
                real_sub = True
            else:
                print("[X] Sub Doesnt Exist:\t" + sub)
                real_sub = False

        except Exception as e:
            print("[X] Sub Doesnt Exist:\t" + sub)
            real_sub = False

        return real_sub

    def sample_sub(self, sub, filter, lim):
        subcontent = None

        if self.reddit_service is None:
            self.connect()

        if filter == 'hot':
            sub_content = self.reddit_service.subreddit(sub).hot(limit=lim)
        elif filter == 'top':
            sub_content = self.reddit_service.subreddit(sub).top(limit=lim)
        else:
            sub_content = self.reddit_service.subreddit(sub).new(limit=lim)

        if sub_content is not None:
            try:
                for post in sub_content:
                    if len(post.title) > 0:
                        return sub_content
                    else:
                        return False
            except:
                return False

    def sample_article(self, sub):

        article_Service = articleService()

        if self.reddit_service is None:
            self.connect()

        try:
            subreddit = self.reddit_service.subreddit(sub)
            articles = [article for article in subreddit.hot(limit=25)]
            sampleArticle = articles[random.randint(0,len(articles) - 1)]
            return sampleArticle
        except Exception as e:
            print("Exception\t::\t" + str(e))
            return False

    def goosify_rapi_article(self, article):

        goose = Goose()
        gooseArticle = False

        if self.reddit_service is None:
            self.connect()

        try:
            gooseArticle = goose.extract(url=article.url)
        except:
            return False

        return gooseArticle


class FrequencySummarizer:
  def __init__(self, min_cut=0.1, max_cut=0.9):
    """
     Initilize the text summarizer.
     Words that have a frequency term lower than min_cut
     or higer than max_cut will be ignored.
    """
    self._min_cut = min_cut
    self._max_cut = max_cut
    self._stopwords = set(nltk.corpus.stopwords.words('english') + list(punctuation))

  def _compute_frequencies(self, word_sent):
    """
      Compute the frequency of each of word.
      Input:
       word_sent, a list of sentences already tokenized.
      Output:
       freq, a dictionary where freq[w] is the frequency of w.
    """
    freq = defaultdict(int)
    for s in word_sent:
      for word in s:
        if word not in self._stopwords:
          freq[word] += 1
    # frequencies normalization and fitering
    m = float(max(freq.values()))
    for w in freq.keys():
      freq[w] = freq[w]/m
      if freq[w] >= self._max_cut or freq[w] <= self._min_cut:
        del freq[w]
    return freq

  def summarize(self, text, n):
    """
      Return a list of n sentences
      which represent the summary of text.
    """
    sents = nltk.tokenize.sent_tokenize(text)
    word_sent = [nltk.tokenize.word_tokenize(s.lower()) for s in sents]
    self._freq = self._compute_frequencies(word_sent)
    ranking = defaultdict(int)
    for i,sent in enumerate(word_sent):
      for w in sent:
        if w in self._freq:
          ranking[i] += self._freq[w]
    sents_idx = self._rank(ranking, n)
    return [sents[j] for j in sents_idx]

  def _rank(self, ranking, n):
    """ return the first n sentences with highest ranking """
    return nlargest(n, ranking, key=ranking.get)


class articleService():

    image_domains = ['imgur','i.redd']
    video_domains = ['youtube','v.redd','youtu']
    article_domains = ['bbc']
    filter_domains = ['reddit','twitter','facebook']

    def __init__(self):

        return None

    def summarize_article(self, article):
        fs = FrequencySummarizer()
        for s in fs.summarize(article, 2):
           article = s
        return article

    def format_article(self, microarticle, type):
        microarticle_formatted = False
        rapi = rAPI_Service()
        article_Service = articleService()

        article_title = microarticle.title.title()
        article_url = microarticle.url
        extracted_article = rapi.goosify_rapi_article(microarticle)
        try:
            thumb = extracted_article.top_image.src
        except:
            thumb = microarticle.thumbnail

        elements = []

        if type == 'article':
            try:
                article_summary = str(article_Service.summarize_article(extracted_article.cleaned_text))
                print("[i] Article Summary: ")
                print(article_summary)
            except Exception as e:
                print("Cant get summary::\t" + str(e))
                article_summary = "Fetched by Lilo!"
            element = Element(title=article_title, image_url=thumb, subtitle=article_summary, item_url=article_url)

        elif type == 'image':
            element = Element(title=article_title, image_url=thumb, subtitle="Click to view", item_url=article_url)


        elif type == 'video':
            element = Element(title=article_title, image_url=thumb, subtitle="Click to view", item_url=article_url)

        print("TYPE\t::\t" + str(type))
        elements.append(element)

        return elements

    def type_check(self, microarticle):
        try:
            link = microarticle.url
        except:
            link = "https://reddit.com"

        domain_extracted = tldextract.extract(link)
        domain = domain_extracted.domain
        subdomain = domain_extracted.subdomain
        if domain == 'redd':
            domain = subdomain + "." + domain

        if domain in self.filter_domains:
            return False

        elif domain in self.image_domains:
            return 'image'

        elif domain in self.video_domains:
            return 'video'

        elif domain in self.article_domains:
            return 'article'
        else:
            if microarticle.is_self is True:
                return 'filtered'
            else:
                return 'article'

        # print(str(type) + " - " + link)
        return False

    def get_tokens(self, str):

        tokens = []
        tokens = nltk.tokenize.word_tokenize(str)

        return tokens
