#  SCRAPE USING URLS INPUT FROM CSV WITH SEASON-1 ONLY
#  REMOVE CONDITION AT LINE 75 FOR ALL SEASONS TO BE SCRAPED IN FUNCTION "parse_movie_page"

import csv
from urllib.parse import urlencode
import scrapy
from scrapy import Request

from multiple_movies.items import MultipleMoviesItem
from creds import API_KEY, origin, referer, authority, allowed_domains, base_url
import re

def get_scrapeops_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'keep_headers': True}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

class ScrapeJustwatchSpider(scrapy.Spider):

    name = 'scrape_from_urls_only_season_1_and_movies'

    custom_settings = {
        'FEEDS':{
            'output/multiple_data.csv': {
                'format':'csv',
            }
        }
    }
    
    allowed_domains = [allowed_domains]

    headers = {
        'authority': authority,
        'method': 'GET',
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': origin,
        'referer': referer,
    }

    urls_done = []
    def start_requests(self):
        with open('input_files/justwatch_data_urls.csv','r') as file:
            reader = csv.reader(file)
            for idx, row in enumerate(reader):
                print(f'movie number : {idx}')
                url = row[0]
                popularity = idx+1
                self.urls_done.append(url)
                yield Request(get_scrapeops_url(url), method='GET', headers=self.headers, meta = {'movie_url' : url , 'popularity' : popularity}, callback=self.parse_movie_page)
        
        self.done_urls_data()


    def done_urls_data(self):
        with open("done_urls.csv", "a") as file:
            writer =csv.writer(file)
            for url in self.urls_done:
                writer.writerow([url])
            

    def parse_movie_page(self, response):
        popularity = response.meta.get('popularity')
        movie_url = response.meta.get('movie_url')
        synopsis = response.xpath('//p[@class="text-wrap-pre-line mt-0"]/span/text()').get()
        year = response.xpath('//div[@class="title-block"]//span[@class="text-muted"]/text()').get()
        year = year.replace('(','').replace(')','')
        if "tv-series" in movie_url or "tv-show" in movie_url:
            h2_headings = response.css('h2[class="detail-infos__subheading--label"]')
            for heading in h2_headings:
                heading_text = heading.css('*::text').get()
                if 'Season' in heading_text:
                    number_of_seasons = ''.join(filter(str.isdigit, heading_text))
                    print(number_of_seasons)
                    seasons_list = response.css(f'div[itemamount="{number_of_seasons}"] div[class="horizontal-title-list__item"]')
                    for season in seasons_list:
                        url = season.css('a::attr("href")').get()
                        season_url = f"{base_url}{url}"
                        if re.search(r'\bseason-1\b', url): 
                            yield Request(
                                get_scrapeops_url(season_url),
                                method='GET',
                                headers=self.headers,
                                meta = {
                                        'year' : year,
                                        'popularity' : popularity, 
                                        'movie_url': season_url,
                                        'synopsis' : synopsis
                                        }, 
                                callback=self.parse_seasons,
                                dont_filter=True
                            )
        elif "movie" in movie_url:
            yield Request(get_scrapeops_url(movie_url), method='GET', headers=self.headers, meta = {'popularity' : popularity, 'movie_url': movie_url}, callback=self.parse_movie, dont_filter=True)
        

    def parse_movie(self, response):
        pg_rating = str()
        director = str()
        casts = []
        streaming_sources = []
        genres = str()
        length = str()
        title = str()
        imdb_id = ''
        poster_url = ''
        back_drop_url = ''
        popularity = response.meta.get('popularity')
        web_deep_link = response.meta.get('movie_url')
        movie_name = web_deep_link.split('/')[-1]
        movie_id = f"movie/{movie_name}"
        title = response.xpath('//div[@class="title-block"]//h1/text()').get()
        year = response.xpath('//div[@class="title-block"]//span[@class="text-muted"]/text()').get()
        year = year.replace('(','').replace(')','')
        posters_tag = response.css('aside div[class="hidden-sm visible-md visible-lg title-sidebar__desktop"] picture[class="picture-comp title-poster__image"] ')
        poster_url_list = posters_tag.xpath('(//source[@media="(max-width: 479px)"])[1]/@srcset').get()
        if poster_url_list:
            poster_url = poster_url_list.split(',')[0]
        back_drop = response.css('picture[class="picture-comp"] ')
        back_drop_urls_list = back_drop.css('source[media="(min-width: 992px)"]::attr("srcset")').get()
        if back_drop_urls_list:
            back_drop_url = back_drop_urls_list.split(',')[1].replace('2x','')
        synopsis = response.xpath('//p[@class="text-wrap-pre-line mt-0"]/span/text()').get()
        if synopsis:
            synopsis = re.sub('\s+',' ', synopsis)
            synopsis = synopsis.strip()
        if synopsis == None:
            synopsis = response.meta.get('synopsis')
            if synopsis:
                synopsis = re.sub('\s+',' ', synopsis)
                synopsis = synopsis.strip()
        imdb_rating = response.css('div[v-uib-tooltip="IMDB"] a::text').get()
        if imdb_rating:
            imdb_rating = imdb_rating.split('(')[0]
        imdb_url = response.css('div[v-uib-tooltip="IMDB"] a::attr("href")').get()
        if imdb_url:
            imdb_id = imdb_url.split('/')[-2]
        streaming_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--stream price-comparison__grid__row--block"] a ')
        for streaming in streaming_source_tag:
            streaming_source = streaming.css('img::attr("title")').get()
            if streaming_source not in streaming_sources:
                streaming_sources.append(streaming_source)
        rent_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--rent price-comparison__grid__row--block"] a ')
        for renting in rent_source_tag:
            renting_source = renting.css('img::attr("title")').get()
            if renting_source not in streaming_sources:
                streaming_sources.append(renting_source)
        buy_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--buy price-comparison__grid__row--block"] a ')
        for buying in buy_source_tag:
            buying_source = buying.css('img::attr("title")').get()
            if buying_source not in streaming_sources:
                streaming_sources.append(buying_source)
        detail_info_tags = response.xpath('//div[@class="detail-infos"]')
        for tag in detail_info_tags:
            h3_tag = tag.css('[class="detail-infos__subheading--label"]::text').get()
            if 'Genres' in h3_tag:
                genres = tag.css('[class="detail-infos__subheading"]+div::text').get()
            if 'Runtime' in  h3_tag:
                runtime = tag.css('[class="detail-infos__subheading"]+div::text').get()
                if 'h' in runtime:
                    hours = runtime.split('h')[0]
                    if hours:
                        mins = runtime.split('h')[1].replace(" ",'')
                        numeric_filter = filter(str.isdigit, mins)
                        min_string = "".join(numeric_filter)
                        hours_to_mins = int(hours) * 60
                        if min_string != '':
                            total_minutes = hours_to_mins + int(min_string)
                        else:
                            total_minutes = hours_to_mins
                        length = f"{total_minutes} Min"
                else:
                    length = runtime
            if 'Age rating' in h3_tag:
                pg_rating = tag.css('[class="detail-infos__subheading"]+div::text').get()
            if 'Director' in h3_tag:
                director = tag.css('[class="detail-infos__subheading"]+div span a::text').get()
            casts_tags = response.css('[class="title-credits__actor"] a')
            for cast in casts_tags:
                actor = cast.css('*::text').get()
                casts.append(actor)

        details = MultipleMoviesItem(
            name = title,
            id = movie_id,
            streaming_source = streaming_sources,
            imdb_id = imdb_id,
            imdb_rating = imdb_rating,
            popularity = popularity,
            pg_rating = pg_rating,
            web_link = web_deep_link,
            year = year,
            length = length,
            genres = genres,
            backdrop_url = back_drop_url,
            poster_url = poster_url,
            summary = synopsis,
            directors = director,
            actors = casts
        )
        return details


    def parse_seasons(self, response):
        pg_rating = str()
        director = str()
        casts = []
        streaming_sources = []
        genres = str()
        length = str()
        back_drop_url = ''
        imdb_id = ''
        poster_url = ''
        web_deep_link = response.meta.get('movie_url')
        movie_name = web_deep_link.split('/')[-2]
        season_name = web_deep_link.split('/')[-1]
        if "tv-series" in web_deep_link:
            movie_id = f"tv-series/{movie_name}-{season_name}"
        elif "tv-show" in web_deep_link:
            movie_id = f"tv-show/{movie_name}-{season_name}"
        popularity = response.meta.get('popularity')
        title = response.xpath('//div[@class="title-block"]//h1/a/text()').get()
        season = season_name
        if season:
            season = season.replace('-',' ')
        year = response.xpath('//div[@class="title-block"]//span[@class="text-muted"]/text()').get()
        year = year.replace('(','').replace(')','')
        if year == '':
            year = response.meta.get('year')
        episodes = []
        episodes_list = response.css('[class="episodes-item"] span[class="episodes-item__heading--title"]')
        for episode in episodes_list:
            episode_name = episode.css('*::text').get()
            episodes.append(episode_name)
        episodes = ','.join(str(x) for x in episodes)
        posters_tag = response.css('aside div[class="hidden-sm visible-md visible-lg title-sidebar__desktop"] picture[class="picture-comp title-poster__image"] ')
        poster_url_list = posters_tag.xpath('(//source[@media="(max-width: 479px)"])[1]/@srcset').get()
        if poster_url_list:
            poster_url = poster_url_list.split(',')[0]
        back_drop = response.css('picture[class="picture-comp"] ')
        back_drop_urls_list = back_drop.css('source[media="(min-width: 992px)"]::attr("srcset")').get()
        if back_drop_urls_list:
            back_drop_url = back_drop_urls_list.split(',')[1].replace('2x','')
        synopsis = response.xpath('//p[@class="text-wrap-pre-line mt-0"]/span/text()').get()
        if synopsis:
            synopsis = re.sub('\s+',' ', synopsis)
            synopsis = synopsis.strip()
        if synopsis == None:
            synopsis = response.meta.get('synopsis')
            if synopsis:
                synopsis = re.sub('\s+',' ', synopsis)
                synopsis = synopsis.strip()
        imdb_rating = response.css('div[v-uib-tooltip="IMDB"] a::text').get()
        if imdb_rating:
            imdb_rating = imdb_rating.split('(')[0]
        imdb_url = response.css('div[v-uib-tooltip="IMDB"] a::attr("href")').get()
        if imdb_url:
            imdb_id = imdb_url.split('/')[-2]
        streaming_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--stream price-comparison__grid__row--block"] a ')
        for streaming in streaming_source_tag:
            streaming_source = streaming.css('img::attr("title")').get()
            if streaming_source not in streaming_sources:
                streaming_sources.append(streaming_source)
        rent_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--rent price-comparison__grid__row--block"] a ')
        for renting in rent_source_tag:
            renting_source = renting.css('img::attr("title")').get()
            if renting_source not in streaming_sources:
                streaming_sources.append(renting_source)
        buy_source_tag = response.css('[class="monetizations"] div[class="price-comparison__grid__row price-comparison__grid__row--buy price-comparison__grid__row--block"] a ')
        for buying in buy_source_tag:
            buying_source = buying.css('img::attr("title")').get()
            if buying_source not in streaming_sources:
                streaming_sources.append(buying_source)
        detail_info_tags = response.xpath('//div[@class="detail-infos"]')
        for tag in detail_info_tags:
            h3_tag = tag.css('[class="detail-infos__subheading--label"]::text').get()
            if 'Genres' in h3_tag:
                genres = tag.css('[class="detail-infos__subheading"]+div::text').get()
            if 'Runtime' in  h3_tag:
                runtime = tag.css('[class="detail-infos__subheading"]+div::text').get()
                if 'h' in runtime:
                    hours = runtime.split('h')[0]
                    if hours:
                        mins = runtime.split('h')[1].replace(" ",'')
                        numeric_filter = filter(str.isdigit, mins)
                        min_string = "".join(numeric_filter)
                        hours_to_mins = int(hours) * 60
                        if min_string != '':
                            total_minutes = hours_to_mins + int(min_string)
                        else:
                            total_minutes = hours_to_mins
                        length = f"{total_minutes} Min"
                else:
                    length = runtime
            if 'Age rating' in h3_tag:
                pg_rating = tag.css('[class="detail-infos__subheading"]+div::text').get()
            if 'Director' in h3_tag:
                director = tag.css('[class="detail-infos__subheading"]+div span a::text').get()
            casts_tags = response.css('[class="title-credits__actor"] a')
            for cast in casts_tags:
                actor = cast.css('*::text').get()
                casts.append(actor)

        details = MultipleMoviesItem(
            name = title,
            id = movie_id,
            streaming_source = streaming_sources,
            imdb_id = imdb_id,
            imdb_rating = imdb_rating,
            web_link = web_deep_link,
            popularity = popularity,
            pg_rating = pg_rating,
            year = year,
            length = length,
            genres = genres,
            backdrop_url = back_drop_url,
            poster_url = poster_url,
            summary = synopsis,
            seasons = season,
            episodes = episodes,
            directors = director,
            actors = casts
        )
        return details