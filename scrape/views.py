from uuid import uuid4
from urllib.parse import urlparse
from django.shortcuts import render
from .models import ScrapyModel
from .forms import NameForm
from django.http import JsonResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods
from scrapyd_api import ScrapydAPI
from .BERT_NER import Bert_NER
from .Review_Sentiment import Review_Sentiment
import os
import pandas as pd
import numpy as np


scrapyd = ScrapydAPI('http://scrapyd:6800')
ner = Bert_NER('model/NER3/') 
sen = Review_Sentiment('model/sentiment/')

def is_valid_url(url):
    validate = URLValidator()
    try:
        validate(url) # check if url format is valid
    except ValidationError:
        return False

    return True


# Create your views here.
@require_http_methods(['POST', 'GET'])
def home(request):
    if request.method == 'POST':
        
        hotel_name = request.POST.get('hotel_name', None)
        if not hotel_name:
            return JsonResponse({'error': 'Missing  args'})

        unique_id = str(uuid4()) # create a unique ID. 
        
        # This is the custom settings for scrapy spider. 
        # We can send anything we want to use it inside spiders and pipelines. 
        # I mean, anything
        settings = {
            'unique_id': unique_id, # unique ID for each record for DB
            'FEED_FORMAT' : 'csv',
            'FEED_URI' : "cache/{}.csv".format(unique_id)
            #'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }

        # Here we schedule a new crawling task from scrapyd. 
        # Notice that settings is a special argument name. 
        # But we can pass other arguments, though.
        # This returns a ID which belongs and will be belong to this task
        # We are goint to use that to check task's status.
        task = scrapyd.schedule('default', 'trip_advisor', 
            settings=settings, hotel_name=hotel_name, unique_id=unique_id)

        return JsonResponse({'task_id': task, 'unique_id': unique_id, 'status': 'started' })

    # Get requests are for getting result of a specific crawling task
    elif request.method == 'GET':
        # We were passed these from past request above. Remember ?
        # They were trying to survive in client side.
        # Now they are here again, thankfully. <3
        # We passed them back to here to check the status of crawling
        # And if crawling is completed, we respond back with a crawled data.
        task_id = request.GET.get('task_id', None)
        unique_id = request.GET.get('unique_id', None)

        if not task_id or not unique_id:
            return JsonResponse({'error': 'Missing args'})

        # Here we check status of crawling that just started a few seconds ago.
        # If it is finished, we can query from database and get results
        # If it is not finished we can return active status
        # Possible results are -> pending, running, finished
        status = scrapyd.job_status('default', task_id)
        if status=='finished' or os.path.isfile('bots/cache/'+unique_id+'.csv'):
            context = Ner(unique_id)
            return JsonResponse({'status':status, 'context':context})
        else:
            return JsonResponse({'status': status})

def Ner(unique_id):
    data =0
    if not os.path.isfile('bots/cache/'+unique_id+'_to_CoNLL.csv'):
        print("Does not exist *_to_CoNLL.csv file, creating one")
        review = pd.read_csv('bots/cache/'+unique_id+'.csv', dtype={'comm': str})
        pred = sen.prediction(review)
        df = sen.to_csv(pred,unique_id)
        ner.data = pd.read_csv('bots/cache/'+unique_id+'_label.csv')
        pred = ner.prediction(unique_id)
        ner.to_CoNLL(pred,unique_id)
        print('complete')
        
  
    data = pd.read_csv('bots/cache/'+unique_id+'_to_CoNLL.csv')
    #hotel_name = data['hotel_name'].to_list()[0]
    #print("processing hotel name {}".format(hotel_name))
    data['adj'] = data['adj'].map(lambda x: eval(x))
    data['sentence'] = data['sentence'].map(lambda x: eval(x))
    all_sentence = data
    Filter = ~all_sentence['sentence'].duplicated() ##UID
    data = list(zip(all_sentence[Filter]['ground_truth'].to_list(),all_sentence[Filter]['sentiment'].tolist(),all_sentence[Filter]['sentence'].tolist()))
    
    good_keyword_top5 = list(np.load('bots/cache/'+unique_id+"_good_keyword_top5.npy"))
    bad_keyword_top5 = list(np.load('bots/cache/'+unique_id+"_bad_keyword_top5.npy"))
    context = {
        'good_keyword_top5': good_keyword_top5,
        'bad_keyword_top5': bad_keyword_top5,
        #'hotel_name':hotel_name,
        # 'adj_top5':ner.adj_top5,
        'data':data,
    }
    return context
