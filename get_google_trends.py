import ssl
import json
import time
import random
import logging
from _datetime import datetime, timedelta
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

module_logger = logging.getLogger('get_google_trends')

def get_dates():
    """
    Returns a list of dates from today to 3 days ago in year, month, day format
    :return: list of string of dates in year, month, day format
    """
    dates = []
    for i in range(0, 2):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime('%Y%m%d'))
    return dates

def get_search_terms():
    dates = get_dates()

    search_list = []
    for date in dates:
        try:
            url = f'https://trends.google.com/trends/api/dailytrends?hl=en-US&ed={date}&geo=US&ns=15'

            response = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
            response = json.loads(response.read()[5:])  # skips the byte junk and formatting at the beginning

            for topic in response['default']['trendingSearchesDays'][0]['trendingSearches']:
                search_list.append(topic['title']['query'].lower())
                for related_topic in topic['relatedQueries']:
                    search_list.append(related_topic['query'].lower())
            time.sleep(random.randint(3,10))
        except (URLError, HTTPError):
            module_logger.info('Error retrieving google trends json.')
    module_logger.info(msg=f'# of search items: {len(search_list)}\n')
    return list(enumerate(set(search_list)))






