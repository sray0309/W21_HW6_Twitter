#########################################
##### Name:       rui sun           #####
##### Uniqname:      rayss          #####
#########################################

from requests_oauthlib import OAuth1
import json
import requests
import csv

import hw6_secrets_starter as secrets # file that contains your OAuth credentials

CACHE_FILENAME = "twitter_cache.json"
CACHE_DICT = {}

client_key = secrets.TWITTER_API_KEY
client_secret = secrets.TWITTER_API_SECRET
access_token = secrets.TWITTER_ACCESS_TOKEN
access_token_secret = secrets.TWITTER_ACCESS_TOKEN_SECRET

oauth = OAuth1(client_key,
            client_secret=client_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret)

def open_stop_word():
    with open('stop-word-list.csv', newline='') as csvfile:
        stop_word = list(csv.reader(csvfile, delimiter=','))
    stop_word = stop_word[0]
    result = []
    for word in stop_word:
        result.append(word.strip())
    result.append('rt')

    return result

def test_oauth():
    ''' Helper function that returns an HTTP 200 OK response code and a 
    representation of the requesting user if authentication was 
    successful; returns a 401 status code and an error message if 
    not. Only use this method to test if supplied user credentials are 
    valid. Not used to achieve the goal of this assignment.'''

    url = "https://api.twitter.com/1.1/account/verify_credentials.json"
    auth = OAuth1(client_key, client_secret, access_token, access_token_secret)
    authentication_state = requests.get(url, auth=auth)#.json()
    return authentication_state


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params

    AUTOGRADER NOTES: To correctly test this using the autograder, use an underscore ("_") 
    to join your baseurl with the params and all the key-value pairs from params
    E.g., baseurl_key1_value1
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    s = baseurl
    for key, val in params.items():
        s = s + '_' + str(key).lower() + '_' + str(val).lower()
    
    return s

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    response = requests.get(baseurl, 
                        params=params, 
                        auth=oauth)

    results = response.json()
    return results
    
def make_request_with_cache(baseurl, hashtag, count):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    AUTOGRADER NOTES: To test your use of caching in the autograder, please do the following:
    If the result is in your cache, print "fetching cached data"
    If you request a new result using make_request(), print "making new request"

    Do no include the print statements in your return statement. Just print them as appropriate.
    This, of course, does not ensure that you correctly retrieved that data from your cache, 
    but it will help us to see if you are appropriately attempting to use the cache.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search for
    count: integer
        The number of results you request from Twitter
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    params = {'q': hashtag, 'count': count}
    request_key = construct_unique_key(baseurl, params)
    results = open_cache()
    for key, val in results.items():
        if key == 'request_key' and val == request_key:
            print('fetching cached data')
            return results

    results = make_request(baseurl, params)
    print("making new request")
    results['request_key'] = request_key
    save_cache(results)
    return results
    


def find_most_common_cooccurring_hashtag(tweet_data, hashtag_to_ignore):
    ''' Finds the hashtag that most commonly co-occurs with the hashtag
    queried in make_request_with_cache().

    Parameters
    ----------
    tweet_data: dict
        Twitter data as a dictionary for a specific query
    hashtag_to_ignore: string
        the same hashtag that is queried in make_request_with_cache() 
        (e.g. "#MarchMadness2021")

    Returns
    -------
    list
        the top 3 ihashtag that co-occurs with the hashtag 
        queried in make_request_with_cache()

    '''
    results = tweet_data['statuses']
    hashtags = {}
    for result in results:
        if result['entities']['hashtags'] != None:
            for hashtag in result['entities']['hashtags']:
                if ((hashtag_to_ignore[1:].lower() in hashtag['text'].lower()) or (hashtag['text'].lower() in hashtag_to_ignore[1:].lower())):
                    pass
                else:
                    if hashtag['text'].lower() in list(hashtags.keys()):
                        hashtags[hashtag['text'].lower()] += 1
                    else:
                        hashtags[hashtag['text'].lower()] = 1

    cooccur_hashtag = []
    for i in range(3):
        num = 0
        for key, val in hashtags.items():
            if val > num:
                num = val
                top_hashtag = key
        if num == 0:
            break
        cooccur_hashtag.append('#'+top_hashtag)
        del hashtags[top_hashtag]

    return cooccur_hashtag

def find_most_common_occurring_words(tweet_data):
    results = tweet_data['statuses']
    words_dict = {}
    stop_word = open_stop_word()
    for result in results:
        if result['text'] != None:
            words = result['text'].split(' ')
            for word in words:
                if word == '':
                    continue
                if (word.lower() in stop_word) or word[0] == '#':
                    pass
                else:
                    if word.lower() in list(words_dict.keys()):
                        words_dict[word.lower()] += 1
                    else:
                        words_dict[word.lower()] = 1


    cooccur_words = {}
    for i in range(10):
        num = 0
        for key, val in words_dict.items():
            if val > num:
                num = val
                top_word = key
        if num == 0:
            break
        cooccur_words[top_word] = num
        del words_dict[top_word]

    return cooccur_words
    

if __name__ == "__main__":
    if not client_key or not client_secret:
        print("You need to fill in CLIENT_KEY and CLIENT_SECRET in secret_data.py.")
        exit()
    if not access_token or not access_token_secret:
        print("You need to fill in ACCESS_TOKEN and ACCESS_TOKEN_SECRET in secret_data.py.")
        exit()
    print(test_oauth())

    CACHE_DICT = open_cache()

    baseurl = "https://api.twitter.com/1.1/search/tweets.json"
    while(True):
        hashtag = input("What hashtag you want to search? ")
        if hashtag == 'exit':
            break
        else:
            hashtag = '#' + hashtag
            count = 100

            tweet_data = make_request_with_cache(baseurl, hashtag, count)
            top_three_cooccurring_hashtag = find_most_common_cooccurring_hashtag(tweet_data, hashtag)
            if top_three_cooccurring_hashtag == []:
                print("There are no coocurring hashtags")
            else:
                print("The top three cooccurring hashtag with {} is {}.".format(hashtag, top_three_cooccurring_hashtag))

            top_ten_occuring_words = find_most_common_occurring_words(tweet_data)
            if top_ten_occuring_words == {}:
                print("There are no occuring words")
            else:
                print("The top ten occurring words with {} is shown below along with the frequency.".format(hashtag))
                i = 1
                for key, val in top_ten_occuring_words.items():
                    print(f'{i}: {key} occurs {val} times')
                    i += 1