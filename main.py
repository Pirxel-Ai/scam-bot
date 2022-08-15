import emoji
import tweepy

from difflib import SequenceMatcher
from itertools import chain, combinations
import itertools
import numpy as np
import time
from src.utils import read_config
from src.fetch_data import query_datasets
from flask import Flask
import os


config = read_config('settings/config.ini')

app = Flask(__name__)


# Authenticate to Twitter
bearer_token = config['PirxBot']['BEARER_TOKEN']
consumer_key = config['PirxBot']['API_KEY']
consumer_secret_key = config['PirxBot']['API_SECRET']
access_token = config['PirxBot']['ACCES_TOKEN']
access_token_secret = config['PirxBot']['ACCES_TOKEN_SECRET']


auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication Successful")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
except:
    print("Authentication Error")
    
    
WHITELIST = ['MercadoPagoMex', 'Airbnbdesign', 'bookingdesign', 'SkyscannerNow']

QUERY = """
        SELECT tweets.*, 
        candidates.target,
        candidates.match_type,
        candidates.id_str,
        candidates.name,
        candidates.screen_name,
        candidates.location,
        candidates.description,
        candidates.url,
        candidates.protected,
        candidates.followers_count,
        candidates.friends_count,
        candidates.listed_count,
        candidates.created_at as user_created_at,
        candidates.favourites_count,
        candidates.verified,
        candidates.statuses_count,
        candidates.profile_image_url,
        FROM `deeplogo.Streaming.tweets` as tweets
        left join `deeplogo.Fraud.candidates` as candidates
        on tweets.author_id = candidates.id_str
        where candidates.id_str is not null
        and candidates.screen_name != candidates.target
"""

QUERY = """
        SELECT tweets.*, 
        candidates.target,
        candidates.match_type,
        candidates.id_str,
        candidates.name,
        candidates.screen_name,
        candidates.location,
        candidates.description,
        candidates.url,
        candidates.protected,
        candidates.followers_count,
        candidates.friends_count,
        candidates.listed_count,
        candidates.created_at as user_created_at,
        candidates.favourites_count,
        candidates.verified,
        candidates.statuses_count,
        candidates.profile_image_url,
        FROM `deeplogo.Streaming.tweets` as tweets
        left join `deeplogo.Fraud.candidates` as candidates
        on tweets.author_id = candidates.id_str
        where candidates.id_str is not null
        and candidates.screen_name != candidates.target
"""

def build_text(fake_user, target_user, victim_user, lang='es'):
    if len(victim_user)==0:
        return None
    else:
        victim_user=victim_user[0]
    if lang == 'en':
        text = f':warning: @{victim_user}: Beware of @{fake_user}! It may be a fake user trying to impersonate on behalf of @{target_user}.'
    elif lang == 'es':
        text = f':warning: @{victim_user}: Ten cuidado con @{fake_user}! Pareciera ser un usuario falso que intenta hacerse pasar por @{target_user}.'
    else:
        text = ''
    text = emoji.emojize(text)
    return text

def send_alert(tweet_id, text):
    try:
        r = api.update_status(text, in_reply_to_status_id=tweet_id)
        print('alert sent')
        return r._json
    except BaseException as e:
        print(e)
        if str(e) == '403 Forbidden\n261 - Application cannot perform write actions. Contact Twitter Platform Operations through https://help.twitter.com/forms/platform.':
            return 'duplicate'



def get_user_timeline(user_id, count=20):
    try:
        r = api.user_timeline(user_id=int(user_id), count=count)
        tweets = [x._json for x in r]
        return tweets
    except:
        return None
    
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def all_pairs(mainlist):
    return itertools.combinations(mainlist, 2)

def tweets_intra_similarity(list_tweets):
    return np.mean([similar(*subset) for subset in all_pairs(list_tweets)])


@app.route("/")
def stream_and_insert():
  while True:

        rows = [dict(x) for x in query_datasets(QUERY)]

        own_tweets = []
        
        for status in tweepy.Cursor(api.user_timeline).items():
            own_tweets.append(status)

        reported = [x._json['id_str'] for x in own_tweets]
        print(f'Alerted so far {len(reported)} victims')


        for tweet in rows:

            if tweet['id'] in reported:
                print('already reported')
                continue

            tweet_id = tweet['id']
            fake_user = tweet['screen_name']
            target_user = tweet['target']
            mentions= [x['username'] for x in tweet['entities']['mentions']]
            victim_user = [user for user in mentions if user not in [fake_user, target_user]]
            lang = tweet['lang']

            # build text
            text = build_text(fake_user, target_user, victim_user, lang)

            # send alert
            status = send_alert(tweet_id, text)
            print(f'Alert sent: {text}')
            time.sleep(60)
            reported.append(tweet['id'])
            

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))