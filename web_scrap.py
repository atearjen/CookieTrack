from itertools import cycle
from bs4 import BeautifulSoup
import requests
import grequests
import logging
import random
import sys
from fake_useragent import UserAgent, FakeUserAgentError

# Narrowing down the space to the article in the page
#(since there are many other irrelevant elements in the page)
#article = soup.find(class_="article-wrapper grid row")

# Getting the keywords section
#keyword_section = soup.find(class_="keywords-section")
# Same as: soup.select("div.article-wrapper grid row div.keywords-section")

# Getting a list of all keywords which are inserted into a keywords list in line 7.
#keywords_raw = keyword_section.find_all(class_="keyword")
#keyword_list = [word.get_text() for word in keywords_raw]
def main():
    urls = ["www.aaronistheman.github.io/#/home"] # all links to scrape

# Create pools of proxies and headers and get the first ones
    proxy_pool, headers_pool = create_pools()
    current_proxy = next(proxy_pool)
    current_headers = next(headers_pool)

# Create a generator of all links that are used in grequests.map() function. This way, 4 requests are sent concurrently
# Note that the current proxy and headers are the same for all the requests below. It is up to you to specify the urls for it.
    rs = (grequests.get(u) for u in urls)
    pages = grequests.map(rs, size=4, proxies={"http": current_proxy, "https": current_proxy}, headers=current_headers, exception_handler=exception_handler)

# get all Beautifulsoup objects of all retrieved pages
    soups = [BeautifulSoup(pages[ind].content, 'html.parser') if
         pages[ind].status_code == 200 else "problem" for ind in range(len(pages))]


def proxies_pool():
    url = 'https://www.sslproxies.org/'

    # Retrieve the site's page. The 'with'(Python closure) is used here in order to automatically close the session when done
    with requests.Session() as res:
        proxies_page = res.get(url)

    # Create a BeutifulSoup object and find the table element which consists of all proxies
    soup = BeautifulSoup(proxies_page.content, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Go through all rows in the proxies table and store them in the right format (IP:port) in our proxies list
    proxies = []
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append('{}:{}'.format(row.find_all('td')[0].string, row.find_all('td')[1].string))
    return proxies

# Generate the pools
def create_pools():
    proxies = proxies_pool()
    logger = Logger().logger
    headers = [random_header(logger) for ind in range(len(proxies))] # list of headers, same length as the proxies list

    # This transforms the list into itertools.cycle object (an iterator) that we can run
    # through using the next() function in lines 16-17.
    proxy_pool = cycle(proxies)
    headers_pool = cycle(headers)
    return proxy_pool, headers_pool

def random_header(logger):
    # Create a dict of accept headers for each user-agent.
    accepts = {"Firefox": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Safari, Chrome": "application/xml,application/xhtml+xml,text/html;q=0.9, text/plain;q=0.8,image/png,*/*;q=0.5"}

    # Get a random user-agent. We used Chrome and Firefox user agents.
    # Take a look at fake-useragent project's page to see all other options - https://pypi.org/project/fake-useragent/
    try:
        # Getting a user agent using the fake_useragent package
        ua = UserAgent()
        if random.random() > 0.5:
            random_user_agent = ua.chrome
        else:
            random_user_agent = ua.firefox

    # In case there's a problem with fake-useragent package, we still want the scraper to function
    # so there's a list of user-agents that we created and swap to another user agent.
    # Be aware of the fact that this list should be updated from time to time.
    # List of user agents can be found here - https://developers.whatismybrowser.com/.
    except FakeUserAgentError  as error:
        # Save a message into a logs file. See more details below in the post.
        logger.error("FakeUserAgent didn't work. Generating headers from the pre-defined set of headers. error: {}".format(error))
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1"]  # Just for case user agents are not extracted from fake-useragent package
        random_user_agent = random.choice(user_agents)

    # Create the headers dict. It's important to match between the user-agent and the accept headers as seen in line 35
    finally:
        valid_accept = accepts['Firefox'] if random_user_agent.find('Firefox') > 0 else accepts['Safari, Chrome']
        headers = {"User-Agent": random_user_agent,
                  "Accept": valid_accept}
    return headers

class Logger:
    def __init__(self):
        # Initiating the logger object
        self.logger = logging.getLogger(__name__)

        # Set the level of the logger. This is SUPER USEFUL since it enables you to decide what to save in the logs file.
        # Explanation regarding the logger levels can be found here - https://docs.python.org/3/howto/logging.html
        self.logger.setLevel(logging.DEBUG)

        # Create the logs.log file
        handler = logging.FileHandler('logs.log')

        # Format the logs structure so that every line would include the time, name, level name and log message
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Adding the format handler
        self.logger.addHandler(handler)

        # And printing the logs to the console as well
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

if __name__ == '__main__':
    main()
