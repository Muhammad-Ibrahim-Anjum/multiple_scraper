# SCRAPE USING SEARCH QUERY USING IMDB CSV INPUT
# REMOVE CONDITION AT LINE 110 FOR ALL SEASONS TO BE SCRAPED IN FUNCTION "parse_movie_page"

import csv
import re
import scrapy
from scrapy import Request
from urllib.parse import urlencode

from multiple_movies.items import MultipleMoviesItem
from creds import API_KEY, origin, referer, authority, allowed_domains, base_url

YEAR = '2023'

def get_scrapeops_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'keep_headers': True}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

class ScrapeJustwatchSpider(scrapy.Spider):
    name = 'scrape_justwatch_with_search_query'
    custom_settings = {
        'FEEDS':{
            'output/multiple_data.csv': {
                'format':'csv',
            }
        },
        'FEED_EXPORT_FIELDS' : ['imdb_id','streaming_source','id', 'name', 'year', 'rating', 'imdb_rating', 'popularity', 'summary', 'length', 'genres', 'directors', 'actors', 'supporting_actors', 'producers', 'writers', 'studio', 'pg_rating','content_advisory', 'seasons', 'episodes', 'web_link', 'ios_deep_link', 'android_deep_link',   'trailer_url', 'poster_url', 'backdrop_url']
    }
    allowed_domains = [allowed_domains]

    headers = {
        'authority': authority,
        'method': 'POST',
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': origin,
        'referer': referer,
    }


    urls_done = []
    visited_urls = set()

    def start_requests(self):
        with open('input_files/product_testing.csv','r') as file:
            reader = csv.reader(file)
            next(reader)
            for idx, row in enumerate(reader):
                name = row[3]  ##name
                popularity = row[7]  ##popularity 
                self.urls_done.append(row[21])  ##url
                search_query = f"{base_url}/in/search?q={name}"
                yield Request(search_query, method='GET', headers=self.headers, meta = {'popularity' : popularity,"synopsis":row[8]}, callback=self.search_result_links)
        
        self.done_urls_data()


    def done_urls_data(self):
        with open("done_urls.csv", "a") as file:
            writer =csv.writer(file)
            for url in self.urls_done:
                writer.writerow([url])
    

    def search_result_links(self, response):
        urls = response.css(f'a.title-list-row__column-header span.header-year:contains("{YEAR}")')
        popularity = response.meta.get('popularity')

        for url in urls:
            link = url.xpath('ancestor::a/@href').get()
            complete_link = f"{base_url}{link}"
            if link not in self.visited_urls:
                self.visited_urls.add(link)
                yield Request(
                    get_scrapeops_url(complete_link),
                    method='GET',
                    headers=self.headers,
                    meta = {
                            'popularity' : popularity, 
                            'movie_url': complete_link,
                            'synopsis':response.meta.get('synopsis')
                            }, 
                    callback=self.parse_movie_page, 
                    dont_filter=True
                )
                

    def parse_movie_page(self, response):
        popularity = response.meta.get('popularity')
        movie_url = response.meta.get('movie_url')
        synopsis = response.meta.get('synopsis')

        imdb_id = re.findall(r'"imdbId":"(.+?)"', response.text)
        if len(imdb_id)>0:
            imdb_id = imdb_id[0]
        else:
            imdb_id = ''

        year = response.xpath('//div[@class="title-block"]//span[@class="text-muted"]/text()').get()
        year = year.replace('(','').replace(')','')

        if movie_url and "tv-series" in movie_url or "tv-show" in movie_url:
            h2_headings = response.css('h2[class="detail-infos__subheading--label"]')
            for heading in h2_headings:
                heading_text = heading.css('*::text').get()
                if heading_text:
                    heading_text = heading_text.upper()
                    if 'SEASONS' in heading_text:
                        number_of_seasons = ''.join(filter(str.isdigit, heading_text))
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
                                            'synopsis' : synopsis,
                                            "imdb_id":imdb_id
                                            }, 
                                    callback=self.parse_seasons,
                                    dont_filter=True
                                )
        elif "movie" in movie_url:
            yield Request(get_scrapeops_url(movie_url), method='GET', headers=self.headers, meta = {'popularity' : popularity, 'movie_url': movie_url,"imdb_id":imdb_id,'synopsis' : synopsis}, callback=self.parse_movie, dont_filter=True)
        
    def parse_movie(self, response):
        pg_rating = str()
        director = str()
        casts = []
        streaming_sources = []
        genres = str()
        length = str()
        poster_url = ''
        back_drop_url = ''
        imdb_rating = None
 
        imdb_id = response.meta.get('imdb_id')
        popularity = response.meta.get('popularity')
        web_deep_link = response.meta.get('movie_url')
        movie_id = web_deep_link.split('/')[-1]
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
            synopsis = re.sub(r"[\n\t]*", "", synopsis)
        if synopsis == None:
            synopsis = response.meta.get('synopsis')
            if synopsis:
                synopsis = re.sub(r"[\n\t]*", "", synopsis)

        imdb_img_tag = response.css('.detail-infos__value .jw-scoring-listing__rating span img[alt="IMDB"]')
    
        for imdb_rating in imdb_img_tag:
            parent_span = imdb_rating.xpath('./ancestor::span')
            if parent_span:
                imdb_rating = parent_span.css('::text').get().strip()

        if imdb_rating:
            imdb_rating = imdb_rating.split('(')[0]

        streaming_sources = response.css(
            'div.buybox-row.stream div.buybox-row__offers img.offer__icon::attr(alt)').getall()
        streaming_sources = list(set(streaming_sources))

        
        detail_info_tags = response.xpath('//div[@class="detail-infos"]')
        for tag in detail_info_tags:
            h3_tag = tag.css('h3.detail-infos__subheading::text').get()
            if h3_tag and 'Genres' in h3_tag:
                genres = tag.css('[class="detail-infos__subheading"]+div::text').get()
            if h3_tag and 'Runtime' in h3_tag:
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
            if h3_tag and 'Director' in h3_tag:
                director = tag.css('[class="detail-infos__subheading"]+div span::text').get()
            if h3_tag and 'Age rating' in h3_tag:
                pg_rating = tag.css('[class="detail-infos__subheading"]+div::text').get()

            casts_tags = response.css('div.title-credits__actor span.title-credit-name')
            for cast in casts_tags:
                actor = cast.css('::text').get()
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
        poster_url = ''
        imdb_id = response.meta.get('imdb_id')
        web_deep_link = response.meta.get('movie_url')

        movie_name = web_deep_link.split('/')[-2]
        season_name = web_deep_link.split('/')[-1]
        if "tv-series" in web_deep_link:
            movie_id = f"tv-series/{movie_name}-{season_name}"
        elif "tv-show" in web_deep_link:
            movie_id = f"tv-show/{movie_name}-{season_name}"
        popularity = response.meta.get('popularity')
        title = response.xpath('//div[@class="title-block"]//h1/a/text()').get()
        season = response.xpath('//div[@class="title-block"]//h1/text()').get()
        if season:
            season = season.replace('-','')
        year = response.xpath('//div[@class="title-block"]//span[@class="text-muted"]/text()').get()
        year = year.replace('(','').replace(')','')
        if year == '':
            year = response.meta.get('year')
        episodes = []
        episodes_list = response.css('[class="episodes-item"] span[class="episodes-item__heading--title"]')
        for episode in episodes_list:
            episode_name = episode.css('*::text').get()
            episodes.append(episode_name)
        print(title,season, episodes)
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
            synopsis = re.sub(r"[\n\t]*", "", synopsis)
        if synopsis == None:
            synopsis = response.meta.get('synopsis')
            if synopsis:
                synopsis = re.sub(r"[\n\t]*", "", synopsis)

        imdb_img_tag = response.css('.detail-infos__value .jw-scoring-listing__rating span img[alt="IMDB"]')
    
        for imdb_rating in imdb_img_tag:
            parent_span = imdb_rating.xpath('./ancestor::span')
            if parent_span:
                imdb_rating = parent_span.css('::text').get().strip()
        if imdb_rating:
            imdb_rating = imdb_rating.split('(')[0]

        streaming_sources = response.css(
            'div.buybox-row.stream div.buybox-row__offers img.offer__icon::attr(alt)').getall()
        streaming_sources = list(set(streaming_sources))
        detail_info_tags = response.xpath('//div[@class="detail-infos"]')
        for tag in detail_info_tags:
            h3_tag = tag.css('h3.detail-infos__subheading::text').get()
            if h3_tag:
                if 'Genres' in h3_tag:
                    genres = tag.css('div.detail-infos__value::text').get()
                if 'Runtime' in  h3_tag:
                    runtime = tag.css('div.detail-infos__value::text').get()
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
                    pg_rating = tag.css('div.detail-infos__value::text').get()
                if 'Director' in h3_tag:
                    director = tag.css('div.detail-infos__value span::text').get()
            casts_tags = response.css('div.title-credits__actor span.title-credit-name')
            for cast in casts_tags:
                actor = cast.css('::text').get()
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