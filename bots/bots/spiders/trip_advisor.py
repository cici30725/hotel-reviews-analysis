# -*- coding: utf-8 -*-
import re
import scrapy
import urllib.parse
import json
from ..items import HotelItem


class TripAdvisorSpider(scrapy.Spider):
    name = 'trip_advisor'
    start_urls = []
    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        # To make everything dynamic, we need to override them inside __init__ method
        self.hotel_name = kwargs.get('hotel_name')
        self.unique_id = kwargs.get('unique_id')
        self.log(self.hotel_name)
        trip_url = "https://www.tripadvisor.co.uk/TypeAheadJson?action=API&searchSessionId=5EA7063EF579282813E930121DC93B621583682415792ssid&source=SINGLE_SEARCH_NAV&uiOrigin=SINGLE_SEARCH_NAV&max=10&startTime=1583682610457&query={}&beforeQuery=&afterQuery={}&parentids=1&scope=1&beforeGeoId=1&afterGeoId=1&position=&isNearby=&details=true&disableMaxGroupSize=true&geoBoostFix=true&geoPages=true&injectLists=false&injectNewLocation=true&interleaved=true&link_type=geo&local=true&matchKeywords=true&matchOverview=true&matchUserProfiles=true&matchTags=true&matchGlobalTags=true&nearPages=true&nearPagesLevel=strict&neighborhood_geos=true&scoreThreshold=0.8&strictAnd=false&supportedSearchTypes=find_near_stand_alone_query&typeahead1_5=true&simple_typeahead=true&matchQuerySuggestions=true&rescue=true&scopeFilter=global&types=geo%2Chotel%2Ceat%2Cattr%2Cvr%2Cair%2Ctheme_park%2Cal%2Cact%2Cuni%2Cshop%2Cport%2Cgeneral_hospital%2Cferry%2Ccorp%2Cship%2Ccruise_line%2Ccar".format(self.hotel_name, self.hotel_name)
        agoda_url = "https://www.agoda.com/Search/Search/GetUnifiedSuggestResult/3/1/1/0/en-gb/?searchText={}&guid=23de9a43-8a3b-4119-b647-99ae38b7b051&origin=TW&cid=1844104&pageTypeId=1&logtime=Wed%20Mar%2011%202020%2009%3A22%3A14%20GMT%2B0800%20(%E5%8F%B0%E5%8C%97%E6%A8%99%E6%BA%96%E6%99%82%E9%96%93)&logTypeId=1&isHotelLandSearch=true".format(self.hotel_name)
        self.start_urls.append(trip_url)
        self.start_urls.append(agoda_url)
        super(TripAdvisorSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        target = response.url
        ## Create trip advisor requests
        if 'tripadvisor' in target:
            base_url = 'https://www.tripadvisor.co.uk'
            data = json.loads(response.body)
            #　loop though all hotels found
            for hotel in data['results']:
                try:
                    suffix = hotel['urls'][0]['url']
                    hotel_name = hotel['urls'][0]['name']
                    self.log(suffix)
                    self.log(hotel_name)
                except:
                    continue
                if 'Hotel_Review' in suffix:
                    new_url = base_url + suffix
                    yield scrapy.Request(new_url, callback=self.tripadvisor_get_max_page, 
                        meta={'hotel_name':hotel_name, 'suffix':suffix, 'base_url':base_url})
                    # Now breaking because we only want the first suggested result
                    break

        elif 'agoda' in target:
            base_url = 'https://hkg.agoda.com'
            data = json.loads(response.body)
            for hotel in data['SuggestionList']:
                hotel_name = hotel['Name']
                suffix = hotel['Url']
                hotel_id = hotel['ObjectID']

                '''
                Currently I'm getting the exact hotel_url and hotel_id from suggested results and 
                directly sending requests to the agoda comment api
                '''
                if 'search' not in suffix:
                    hotel_url = base_url + suffix
                    api_url = 'https://hkg.agoda.com/NewSite/en-gb/Review/HotelReviews'
                    my_headers = {'accept':'application/json', 'referer':hotel_url, 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
                        , 'Host':'hkg.agoda.com', 'Origin':'https://hkg.agoda.com', 'content-type':'application/json; charset=UTF-8', 'accept-encoding':'gzip, deflate, br', 'accept-language':'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7', 'X-Requested-With': 'XMLHttpRequest'}
                    for pageNumber in range(1, 100):
                        # This is a bit stupid. I'm bruteforing 100 pages becuase I don't know the max page of reviews
                        payload = {"hotelId":int(hotel_id),"demographicId":0,"pageNo":pageNumber,"pageSize":40,"sorting":1,"reviewProviderIds":[332,3038,27901,28999,27980],"isReviewPage":'false',"isCrawlablePage":'true',"paginationSize":5,"filters":{"language":[1],"room":[]}}
                        yield scrapy.Request(url=api_url, method='POST', headers=my_headers, body=json.dumps(payload), callback=self.parse_agoda_hotel_review)

                    '''
                    yield SeleniumRequest(url=new_url, 
                        callback=self.parse_agoda_search_menu,
                        wait_time=10,
                        wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, "ol.hotel-list-container")))
                    '''
                    # Now breaking means we are only scrapying for the first suggestion
                    break


    def tripadvisor_get_max_page(self, response):
        hotel_name = response.meta.get('hotel_name')
        max_page = int(response.xpath('//div[@class="pageNumbers"]/a[last()]/text()').get())
        suffix = response.meta.get('suffix')
        base_url = response.meta.get('base_url')

        suffix_list = suffix.split('Reviews', maxsplit=1)
        # loop through all comment pages
        for i in range(0, max_page):
            suffix_t = suffix_list[0] + "Reviews-or{}".format(i*5) + suffix_list[1]
            new_url = base_url + suffix_t
            self.log('now sending request to '+new_url)
            yield scrapy.Request(new_url, callback=self.parse_tripadvisor_hotel, meta={'hotel_name':hotel_name})


    # Parse tripadvisor requests and go to next page
    def parse_tripadvisor_hotel(self, response):
        #comments = response.xpath('//*[@data-reviewid]//q/span/text()').getall()
        hotels = response.xpath('//*[@data-reviewid]')
        hotel_name = response.meta.get('hotel_name')
        item = HotelItem()
        item['source'] = 'trip_advisor'
        for hotel in hotels:
            comment = ' '.join(hotel.xpath('.//q/span/text()').getall())
            # Getting the rating bubble 
            rating = int(hotel.xpath('./div/div/span/@class').get()[-2])
            #self.log(comment)
            #self.log(rating)
            item['hotel_name'] = hotel_name
            item['comm'] = comment.replace('\n', ' ') 
            item['label'] = '1' if rating>=4 else '0'
            yield(item)

    # Parse's the search menu of agoda
    def parse_agoda_search_menu(self, response):
        driver = response.request.meta['driver']
        hotel_container = driver.find_element_by_class_name('hotel-list-container')
        hotels = hotel_container.find_elements_by_xpath('.//li[@data-hotelid]/a[contains(@id, "hotel-")]')
        api_url = 'https://www.agoda.com/NewSite/en-gb/Review/HotelReviews'
        for hotel in hotels:
            hotel_url = hotel.get_attribute('href')
            hotel_url = hotel_url[:hotel_url.find('?')]
            hotel_id = re.search('[0-9]+', hotel.get_attribute('id')).group(0)
            my_headers = {'accept':'application/json', 'referer':hotel_url, 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
                , 'Host':'hkg.agoda.com', 'Origin':'https://hkg.agoda.com', 'content-type':'application/json; charset=UTF-8', 'accept-encoding':'gzip, deflate, br', 'accept-language':'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7', 'X-Requested-With': 'XMLHttpRequest'}
            self.log(hotel_url)
            self.log(hotel_id)
            for pageNumber in range(1, 100):
                # This is a bit stupid. I'm bruteforing 100 pages becuase I don't know the max page of reviews
                payload = {"hotelId":int(hotel_id),"demographicId":0,"pageNo":pageNumber,"pageSize":40,"sorting":1,"reviewProviderIds":[332,3038,27901,28999,27980],"isReviewPage":'false',"isCrawlablePage":'true',"paginationSize":5,"filters":{"language":[1],"room":[]}}
                yield scrapy.Request(url=api_url, method='POST', headers=my_headers, body=json.dumps(payload), callback=self.parse_agoda_hotel_review)
            # Now breaking means that we are only scraping the first search result
            break



    def parse_agoda_hotel_review(self, response):
        json_resp = json.loads(response.body)
        comments = json_resp['commentList']['comments']
        hotel_name = json_resp['hotelName']
        item = HotelItem()
        item['source'] = 'agoda'
        for c in comments:
            rating = int(c['rating'])
            item['comm'] = c['reviewComments'].replace('\n',' ')
            item['hotel_name'] = hotel_name
            item['label'] = '1' if rating >= 7 else '0'
            yield(item)
        


        


        
