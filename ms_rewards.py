#! /usr/lib/python3.6
# ms_rewards.py - Searches for results via pc bing browser and mobile, completes quizzes on pc bing browser
# Version 2018.02

import os
import argparse
import json
import time
import random
import logging
import ssl
from _datetime import datetime, timedelta
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, \
    ElementClickInterceptedException, ElementNotVisibleException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains


# URLs
BING_SEARCH_URL = 'https://www.bing.com'
DASHBOARD_URL = 'https://account.microsoft.com/rewards/dashboard'

# user agents for edge/pc and mobile
PC_USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134')

MOBILE_USER_AGENT = ('Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; WebView/3.0) '
                     'AppleWebKit/537.36 (KHTML, like Gecko) coc_coc_browser/64.118.222 '
                     'Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.15063')


def init_logging():
    # gets dir path of python script, not cwd, for execution on cron
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.makedirs('logs', exist_ok=True)
    log_path = os.path.join('logs', 'ms_rewards.log')
    logging.basicConfig(filename=log_path, level=logging.INFO,
                        format='%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s')


def parse_args():
    """
    Parses command line arguments for headless mode, mobile search, pc search, quiz completion
    :return: argparse object
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--headless', action='store_true', dest='headless_setting', default=False,
                            help='Activates headless mode, default is off.')
    arg_parser.add_argument('--mobile', action='store_true', dest='mobile_mode', default=False,
                            help='Activates mobile search, default is off.')
    arg_parser.add_argument('--pc', action='store_true', dest='pc_mode', default=False,
                            help='Activates pc search, default is off.')
    arg_parser.add_argument('--quiz', action='store_true', dest='quiz_mode', default=False,
                            help='Activates pc quiz search, default is off.')
    arg_parser.add_argument('--email', action='store_true', dest='email_mode', default=False,
                            help='Activates quiz mode, default is off.')
    return arg_parser.parse_args()


def get_dates():
    """
    Returns a list of dates from today to 3 days ago in year, month, day format
    :return: list of string of dates in year, month, day format
    """
    dates = []
    for i in range(0, 3):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime('%Y%m%d'))
    return dates


def get_search_terms():
    dates = get_dates()

    search_terms = []
    for date in dates:
        try:
            url = f'https://trends.google.com/trends/api/dailytrends?hl=en-US&ed={date}&geo=US&ns=15'

            response = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
            response = json.loads(response.read()[5:])  # skips the byte junk and formatting at the beginning

            for topic in response['default']['trendingSearchesDays'][0]['trendingSearches']:
                search_terms.append(topic['title']['query'].lower())
                for related_topic in topic['relatedQueries']:
                    search_terms.append(related_topic['query'].lower())
            time.sleep(random.randint(3, 10))
        except (URLError, HTTPError):
            logging.info('Error retrieving google trends json.')
    logging.info(msg=f'# of search items: {len(search_terms)}\n')
    return list(enumerate(set(search_terms)))


def get_login_info():
    """
    Gets login usernames and passwords from json
    :return: login dict
    """
    with open('ms_rewards_login_dict.json', 'r') as f:
        return json.load(f)


def browser_setup(headless_mode, user_agent):
    """
    Inits the firefox browser with headless setting and user agent
    :param headless_mode: Boolean
    :param user_agent: String
    :return: webdriver obj
    """
    options = Options()
    options.headless = headless_mode
    profile = webdriver.FirefoxProfile()
    profile.set_preference('general.useragent.override', user_agent)
    firefox_browser_obj = webdriver.Firefox(options=options, firefox_profile=profile)
    return firefox_browser_obj


def log_in(email_address, pass_word):
    logging.info(msg=f'Logging in {email_address}...')
    browser.get('https://login.live.com/')
    time.sleep(1)
    # wait for login form and enter email
    wait_until_clickable(By.NAME, 'loginfmt', 30)
    send_key_by_name('loginfmt', email_address)
    send_key_by_name('loginfmt', Keys.RETURN)
    logging.debug(msg='Sent Email Address.')
    # wait for password form and enter password
    time.sleep(1)
    wait_until_clickable(By.NAME, 'passwd', 30)
    send_key_by_name('passwd', pass_word)
    logging.debug(msg='Sent Password.')
    # wait for 'sign in' button to be clickable and sign in
    time.sleep(1)
    send_key_by_name('passwd', Keys.RETURN)
    # Wait until logged in
    wait_until_visible(By.CLASS_NAME, 'personal-info', 30)


def find_by_id(obj_id):
    """
    Searches for elements matching ID
    :param obj_id:
    :return: List of all nodes matching provided ID
    """
    return browser.find_elements_by_id(obj_id)


def find_by_xpath(selector):
    """
    Finds elements by xpath
    :param selector: xpath string
    :return: returns a list of all matching selenium objects
    """
    return browser.find_elements_by_xpath(selector)


def find_by_class(selector):
    """
    Finds elements by class name
    :param selector: Class selector of html obj
    :return: returns a list of all matching selenium objects
    """
    return browser.find_elements_by_class_name(selector)


def find_by_css(selector):
    """
    Finds nodes by css selector
    :param selector: CSS selector of html node obj
    :return: returns a list of all matching selenium objects
    """
    return browser.find_elements_by_css_selector(selector)


def wait_until_visible(by_, selector, time_to_wait=10):
    """
    Wait until all objects matching selector are visible
    :param by_: Select by ID, XPATH, CSS Selector, other, from By module
    :param selector: string of selector
    :param time_to_wait: Int time to wait
    :return: None
    """
    try:
        WebDriverWait(browser, time_to_wait).until(ec.visibility_of_element_located((by_, selector)))
    except TimeoutException:
        logging.exception(msg=f'{selector} element Not Visible - Timeout Exception', exc_info=False)
    except WebDriverException:
        logging.exception(msg=f'Webdriver error for {selector} object')


def wait_until_clickable(by_, selector, time_to_wait=10, custom_log='TimeoutException'):
    """
    Waits 5 seconds for element to be clickable
    :param by_:  BY module args to pick a selector
    :param selector: string of xpath, css_selector or other
    :param time_to_wait: Int time to wait
    :param custom_log: String custom msg to log
    :return: None
    """
    try:
        WebDriverWait(browser, time_to_wait).until(ec.element_to_be_clickable((by_, selector)))
    except TimeoutException:
        logging.exception(msg=custom_log)
    except WebDriverException:
        logging.exception(msg=f'Error., selector: {selector}')


def send_key_by_name(name, key):
    """
    Sends key to target found by name
    :param name: Name attribute of html object
    :param key: Key to be sent to that object
    :return: None
    """
    try:
        browser.find_element_by_name(name).send_keys(key)
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def send_key_by_id(obj_id, key):
    """
    Sends key to target found by id
    :param obj_id: ID attribute of the html object
    :param key: Key to be sent to that object
    :return: None
    """
    try:
        browser.find_element_by_id(obj_id).send_keys(key)
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def click_by_class(selector):
    """
    Clicks on node object selected by class name
    :param selector: class attribute
    :return: None
    """
    try:
        browser.find_element_by_class_name(selector).click()
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def click_by_id(obj_id):
    """
    Clicks on object located by ID
    :param obj_id: id tag of html object
    :return: None
    """
    try:
        browser.find_element_by_id(obj_id).click()
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def clear_by_id(obj_id):
    """
    Clear object found by id
    :param obj_id: ID attribute of html object
    :return: None
    """
    try:
        browser.find_element_by_id(obj_id).clear()
    except (ElementNotVisibleException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def main_window():
    """
    Closes current window and switches focus back to main window
    :return: None
    """
    try:
        for i in range(1, len(browser.window_handles)):
            browser.switch_to.window(browser.window_handles[i])
            browser.close()
    except WebDriverException:
        logging.error('Error when switching to main_window')
    finally:
        browser.switch_to.window(browser.window_handles[0])


def latest_window():
    """
    Switches to newest open window
    :return:
    """
    browser.switch_to.window(browser.window_handles[-1])


def search(search_terms, mobile_search=False):
    """
    Searches using an enumerated list of search terms, prints search item and number
    :param search_terms: enumerated list of tuples with search terms
    :param mobile_search: Boolean, True for mobile search limits, default false for pc search limits
    :return:
    """
    if mobile_search:
        search_limit = 20
    else:
        search_limit = 30

    logging.info(msg="Search Start")
    if search_terms == [] or search_terms is None:
        logging.info(msg="Search Aborted. No Search Terms.")
    else:
        browser.get(BING_SEARCH_URL)
        for num, item in search_terms[:search_limit]:
            # clears search bar and enters in next search term
            wait_until_visible(By.ID, 'sb_form_q', 10)
            clear_by_id('sb_form_q')
            send_key_by_id('sb_form_q', item)
            send_key_by_id('sb_form_q', Keys.RETURN)
            # prints search term and item, limited to 80 chars
            logging.debug(msg=f'Search #{num}: {item[:80]}')
            time.sleep(random.randint(3, 5))  # random sleep for more human-like, and let ms reward website keep up.


def iter_dailies():
    """
    Iterates through all outstanding dailies
    :return: None
    """
    browser.get(DASHBOARD_URL)
    sign_in_splash = find_by_id('signinhero')
    if sign_in_splash:
        sign_in_splash[0].click()
    # on dashboard, get list of dailies by yellow plus icon signifying open offer
    # need this sleep otherwise MS thinks I am not logged in. In future change to wait until fully loaded.
    time.sleep(10)
    wait_until_visible(By.XPATH, '//span[contains(@class, "mee-icon-AddMedium")]', 30)
    open_offers = browser.find_elements_by_xpath('//span[contains(@class, "mee-icon-AddMedium")]')
    if not open_offers:
        logging.info(msg='No dailies found.')
    # get common parent element of open_offers
    parent_elements = [open_offer.find_element_by_xpath('..//..//..//..') for open_offer in open_offers]
    # get points links from parent, # finds ng-transclude descendant of selected node
    offer_links = [parent.find_element_by_xpath('descendant::ng-transclude') for parent in parent_elements]
    # iterate through the dailies
    for offer in offer_links:
        time.sleep(3)
        logging.debug(msg='Detected offer.')
        # click and switch focus to latest window
        offer.click()
        latest_window()
        time.sleep(10)
        # check for poll by ID
        if find_by_id('Radio00'):
            logging.debug(msg='Poll identified.')
            daily_poll()
        # check for quiz by checking for ID
        elif find_by_id('rqStartQuiz'):
            click_by_id('rqStartQuiz')
            # test for drag or drop or regular quiz
            if find_by_id('rqAnswerOptionNum0'):
                logging.debug(msg='Drag and Drop Quiz identified.')
                drag_and_drop_quiz()
            # look for lightning quiz indicator
            elif find_by_id('rqAnswerOption0'):
                logging.debug(msg='Lightning Quiz identified.')
                lightning_quiz()
        elif find_by_class('wk_Circle'):
            logging.debug(msg='Click Quiz identified.')
            click_quiz()
        # else do scroll for exploring pages
        else:
            logging.debug(msg='Explore Daily identified.')
            explore_daily()


def explore_daily():
    # needs try/except bc these functions don't have exception handling built in.
    try:
        # select html to send commands to
        html = browser.find_element_by_tag_name('html')
        # scroll up and down
        for i in range(3):
            html.send_keys(Keys.END)
            html.send_keys(Keys.HOME)
        # exit to main window
        main_window()
    except TimeoutException:
        logging.exception(msg='Explore Daily Timeout Exception.')
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg='Element not clickable or visible.')
    except WebDriverException:
        logging.exception(msg='Error.')


def daily_poll():
    """
    Randomly clicks a poll answer, returns to main window
    :return: None
    """
    # click poll option
    choices = ['Radio00', 'Radio01']
    click_by_id(random.choice(choices))
    time.sleep(3)
    # close window, switch to main
    main_window()


def lightning_quiz():
    for question_round in range(10):
        logging.debug(msg=f'Round# {question_round}')
        # iterate through 4 choices
        for i in range(4):
            click_choices = find_by_class('rqOption')
            if click_choices:
                i = click_choices[i]
                # if object is stale, greyed out, or not visible, skip it
                if i.is_displayed():
                    logging.debug(msg=f'Clicked {i}')
                    i.click()
                    time.sleep(2)
        # let new page load
        time.sleep(3)
        if find_by_id('quizCompleteContainer'):
            break
    # close the quiz completion splash
    find_by_css('.cico.btCloseBack')[0].click()
    main_window()


def click_quiz():
    # start the quiz, iterates 10 times
    for i in range(10):
        if find_by_css('.cico.btCloseBack'):
            find_by_css('.cico.btCloseBack')[0].click()[0].click()
            logging.debug(msg='Quiz popped up during a click quiz...')
        choices = find_by_class('wk_Circle')
        # click answer
        if choices:
            random.choice(choices).click()
            time.sleep(3)
        # click the 'next question' button
        wait_until_clickable(By.ID, 'check', 30)
        click_by_id('check')
        # if the green check mark reward icon is visible, end loop
        if find_by_css('span[class="rw_icon"]'):
            break
    main_window()


def drag_and_drop_quiz():
    """
    Checks for drag quiz answers and exits when none are found.
    :return: None
    """
    for i in range(100):
        try:
            # find possible solution buttons
            drag_option = find_by_class('rqOption')
            # find any answers marked correct with correctAnswer tag
            right_answers = find_by_class('correctAnswer')
            # remove right answers from possible choices
            if right_answers:
                drag_option = [x for x in drag_option if x not in right_answers]
            if drag_option:
                # select first possible choice and remove from options
                choice_a = random.choice(drag_option)
                drag_option.remove(choice_a)
                # select second possible choice from remaining options
                choice_b = random.choice(drag_option)
                ActionChains(browser).drag_and_drop(choice_a, choice_b).perform()
        except (WebDriverException, TypeError):
            logging.debug(msg='Unknown Error.')
            continue
        finally:
            time.sleep(3)
            if find_by_id('quizCompleteContainer'):
                break
    # close the quiz completion splash
    time.sleep(3)
    find_by_css('.cico.btCloseBack')[0].click()
    time.sleep(3)
    main_window()


def get_point_total():
    """
    Logs points for account, on both mobile and pc user agents
    :return: None
    """
    browser.get(DASHBOARD_URL)
    time.sleep(10)
    # get number of incomplete offers
    num_open_offers = len(browser.find_elements_by_xpath('//span[contains(@class, "mee-icon-AddMedium")]'))
    logging.info(msg=f'Number of incomplete offers: {num_open_offers}')
    # get number of total number of points
    points = find_by_css('mee-rewards-user-status-balance.ng-isolate-scope > '
                         'div:nth-child(1) > div:nth-child(2) > '
                         'div:nth-child(1) > div:nth-child(1) > div:nth-child(1) >'
                         ' p:nth-child(1) > mee-rewards-counter-animation:nth-child(1) > span:nth-child(1)')[0].text
    logging.info(msg=f'Total points = {points}')
    # get edge, pc, mobile point totals
    browser.find_element_by_link_text('Points breakdown').click()
    edge_points = browser.find_element_by_xpath('/html/body/div[5]/div[2]/div['
                                                '2]/mee-rewards-points-breakdown/div/div/div[2]/div[1]/div/div['
                                                '2]/mee-rewards-user-points-details/div/div/div/div/p[2]').text
    pc_points = browser.find_element_by_xpath('/html/body/div[5]/div[2]/div['
                                              '2]/mee-rewards-points-breakdown/div/div/div[2]/div[2]/div/div['
                                              '2]/mee-rewards-user-points-details/div/div/div/div/p[2]').text
    mobile_points = browser.find_element_by_xpath('/html/body/div[5]/div[2]/div['
                                                  '2]/mee-rewards-points-breakdown/div/div/div[2]/div[3]/div/div['
                                                  '2]/mee-rewards-user-points-details/div/div/div/div/p[2]').text
    logging.info(msg=f'Edge points = {edge_points}')
    logging.info(msg=f'PC points = {pc_points}')
    logging.info(msg=f'Mobile points = {mobile_points}')


def get_email_links():
    """
    Gets the email links from the text file, appends to a list
    :return: List of string URLs
    """
    with open('email_links.txt', 'r') as f:
        links = []
        for link in f.readlines():
            links.append(link)
    return links


def click_email_links(links):
    """
    Receives list of string URLs and clicks through them.
    Manual mode only, quizzes are still in flux and not standardized yet.
    :param links: List of string URLs
    :return: None
    """
    for link in links:
        browser.get(link)
        input('Press any key to continue.')


if __name__ == '__main__':
    try:
        # start logging
        init_logging()
        logging.info(msg='---------------------------------')
        logging.info(msg='---------------------------------')

        # argparse
        parser = parse_args()
        logging.info(msg='args parsed.')

        # get login dict
        login_dict = get_login_info()
        logging.info(msg='logins retrieved.')

        # get search terms
        search_list = []
        if parser.mobile_mode or parser.pc_mode:
            search_list = get_search_terms()

        # get URLs from emailed links
        email_links = []
        if parser.email_mode:
            email_links = get_email_links()

        # iter through accounts, search, and complete quizzes
        login_dict_keys = list(login_dict.keys())
        random.shuffle(login_dict_keys)
        for dict_key in login_dict_keys:
            email = dict_key
            password = login_dict[dict_key]
            # for email,password in random.sample(list(login_dict.items())):
            # for email, password in login_dict.items():

            if parser.mobile_mode:
                # MOBILE MODE
                logging.info(msg='************MOBILE***************')
                # set up headless browser and mobile user agent
                browser = browser_setup(parser.headless_setting, MOBILE_USER_AGENT)
                try:
                    log_in(email, password)
                    # mobile search
                    search(search_list, mobile_search=True)
                    browser.quit()
                except KeyboardInterrupt:
                    browser.quit()

            if parser.pc_mode or parser.quiz_mode or parser.email_mode:
                # PC MODE
                logging.info(msg='************PC***************')
                # set up edge headless browser and edge pc user agent
                browser = browser_setup(parser.headless_setting, PC_USER_AGENT)
                try:
                    log_in(email, password)
                    if parser.pc_mode:
                        # pc edge search
                        search(search_list)
                    if parser.quiz_mode:
                        # complete quizzes
                        iter_dailies()
                    if parser.email_mode:
                        click_email_links(email_links)
                    # get point totals
                    get_point_total()
                    browser.quit()
                except KeyboardInterrupt:
                    browser.quit()

            logging.info(msg='\n\n')
    except WebDriverException:
        logging.exception(msg='Webdriver failure.')
