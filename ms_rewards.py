#! /usr/lib/python3.6
# ms_rewards.py - Searches for results via pc bing browser and mobile, completes quizzes on pc bing browser
# Version 2018.03

# TODO replace sleeps with minimum sleeps for explicit waits to work, especially after a page redirect

# FIXME mobile version does not require re-sign in, but pc version does, why?
# FIXME Known Cosmetic Issue - logged point total caps out at the point cost of the item on wishlist

"""
- Fixed login, now waits until page is fully loaded
- Replaced urllib api call with requests
- Updated get points with chrome extension source, less prone to error (credit to Shoginn for the url!)
- Updated quizzes to log open quiz offers, completed quiz offers, all points
- Modified error catching for alerts, combined with timeoutexception
"""

import os
import argparse
import json
import time
import random
import logging
from _datetime import datetime, timedelta

import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, \
    ElementClickInterceptedException, ElementNotVisibleException, \
    ElementNotInteractableException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains


# URLs
BING_SEARCH_URL = 'https://www.bing.com'
DASHBOARD_URL = 'https://account.microsoft.com/rewards/dashboard'
POINT_TOTAL_URL = 'http://www.bing.com/rewardsapp/bepflyoutpage?style=chromeextension'

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
    for i in range(0, 2):
        # get dates
        date = datetime.now() - timedelta(days=i)
        # append in year month date format
        dates.append(date.strftime('%Y%m%d'))
    return dates


def get_search_terms():
    dates = get_dates()

    search_terms = []
    for date in dates:
        try:
            # get URL, get api response and parse with json
            url = f'https://trends.google.com/trends/api/dailytrends?hl=en-US&ed={date}&geo=US&ns=15'
            request = requests.get(url)
            response = json.loads(request.text[5:])
            # get all trending searches with their related queries
            for topic in response['default']['trendingSearchesDays'][0]['trendingSearches']:
                search_terms.append(topic['title']['query'].lower())
                for related_topic in topic['relatedQueries']:
                    search_terms.append(related_topic['query'].lower())
            time.sleep(random.randint(3, 5))
        except RequestException:
            logging.error('Error retrieving google trends json.')
        except KeyError:
            logging.error('Cannot parse, JSON keys are modified.')
    # get unique terms, return an enumerated list
    search_terms = set(search_terms)
    logging.info(msg=f'# of search items: {len(search_terms)}\n')
    return list(enumerate(search_terms, start=0))


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
    # experimental disable notifications
    profile.set_preference('dom.webnotifications.serviceworker.enabled', False)
    profile.set_preference('dom.webnotifications.enabled', False)
    profile.set_preference('geo.enabled', False)
    firefox_browser_obj = webdriver.Firefox(options=options, firefox_profile=profile)
    return firefox_browser_obj


def log_in(email_address, pass_word):
    logging.info(msg=f'Logging in {email_address}...')
    browser.get('https://login.live.com/')
    time.sleep(0.5)
    # wait for login form and enter email
    wait_until_clickable(By.NAME, 'loginfmt', 10)
    send_key_by_name('loginfmt', email_address)
    time.sleep(0.5)
    send_key_by_name('loginfmt', Keys.RETURN)
    logging.debug(msg='Sent Email Address.')
    # wait for password form and enter password
    time.sleep(0.5)
    wait_until_clickable(By.NAME, 'passwd', 10)
    send_key_by_name('passwd', pass_word)
    logging.debug(msg='Sent Password.')
    # wait for 'sign in' button to be clickable and sign in
    time.sleep(0.1)
    send_key_by_name('passwd', Keys.RETURN)
    time.sleep(1)
    wait_until_visible(By.ID, 'uhfLogo', 10)
    time.sleep(2)


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
    except (TimeoutException, UnexpectedAlertPresentException):
        logging.exception(msg=f'{selector} element Not Visible - Timeout Exception', exc_info=False)
        screenshot(selector)
        browser.refresh()
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for {selector} object')
        screenshot(selector)
        browser.refresh()


def wait_until_clickable(by_, selector, time_to_wait=10):
    """
    Waits 5 seconds for element to be clickable
    :param by_:  BY module args to pick a selector
    :param selector: string of xpath, css_selector or other
    :param time_to_wait: Int time to wait
    :return: None
    """
    try:
        WebDriverWait(browser, time_to_wait).until(ec.element_to_be_clickable((by_, selector)))
    except (TimeoutException, UnexpectedAlertPresentException):
        logging.exception(msg=f'{selector} element Not clickable - Timeout Exception', exc_info=False)
        screenshot(selector)
        browser.refresh()
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for {selector} object')
        screenshot(selector)
        browser.refresh()


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
        logging.exception(msg=f'Send key by name to {name} element not visible or clickable.')
    except NoSuchElementException:
        logging.exception(msg=f'Send key to {name} element, no such element.')
        screenshot(name)
        browser.refresh()
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for send key to {name} object')


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
        logging.exception(msg=f'Send key by ID to {obj_id} element not visible or clickable.')
    except NoSuchElementException:
        logging.exception(msg=f'Send key by ID to {obj_id} element, no such element')
        screenshot(obj_id)
        browser.refresh()
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for send key by ID to {obj_id} object')


def click_by_class(selector):
    """
    Clicks on node object selected by class name
    :param selector: class attribute
    :return: None
    """
    try:
        browser.find_element_by_class_name(selector).click()
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg=f'Send key by class to {selector} element not visible or clickable.')
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for send key by class to {selector} object')


def click_by_id(obj_id):
    """
    Clicks on object located by ID
    :param obj_id: id tag of html object
    :return: None
    """
    try:
        browser.find_element_by_id(obj_id).click()
    except (ElementNotVisibleException, ElementClickInterceptedException, ElementNotInteractableException):
        logging.exception(msg=f'Click by ID to {obj_id} element not visible or clickable.')
    except WebDriverException:
        logging.exception(msg=f'Webdriver Error for click by ID to {obj_id} object')


def clear_by_id(obj_id):
    """
    Clear object found by id
    :param obj_id: ID attribute of html object
    :return: None
    """
    try:
        browser.find_element_by_id(obj_id).clear()
    except (ElementNotVisibleException, ElementNotInteractableException):
        logging.exception(msg=f'Clear by ID to {obj_id} element not visible or clickable.')
    except NoSuchElementException:
        logging.exception(msg=f'Send key by ID to {obj_id} element, no such element')
        screenshot(obj_id)
        browser.refresh()
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


def screenshot(selector):
    """
    Snaps screenshot of webpage when error occurs
    :param selector: The name, ID, class, or other attribute of missing node object
    :return: None
    """
    logging.exception(msg=f'{selector} cannot be located.')
    screenshot_file_name = f'{datetime.now().strftime("%Y%m%d%%H%M%S")}_{selector}.png'
    screenshot_file_path = os.path.join('logs', screenshot_file_name)
    browser.save_screenshot(screenshot_file_path)


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
    :return: None
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
        # ensure signed in not in mobile mode (pc mode doesn't register when searching)
        if not mobile_search:
            ensure_pc_mode_logged_in()

        for num, item in search_terms:
            try:
                # clears search bar and enters in next search term
                time.sleep(1)
                wait_until_visible(By.ID, 'sb_form_q', 30)
                clear_by_id('sb_form_q')
                send_key_by_id('sb_form_q', item)
                time.sleep(0.1)
                send_key_by_id('sb_form_q', Keys.RETURN)
                # prints search term and item, limited to 80 chars
                logging.debug(msg=f'Search #{num}: {item[:80]}')
                time.sleep(random.randint(3, 4))  # random sleep for more human-like, and let ms reward website keep up.

                # check to see if search is complete, if yes, break out of loop
                if num % search_limit == 0:
                    if mobile_search:
                        # in mobile mode, get point total does not work if no search is done, URL = 404
                        if get_point_total(mobile=True):
                            logging.info(msg=f'Stopped at search number {num}')
                            return
                        # if point total not met, return to search page
                        browser.get(BING_SEARCH_URL)
                    else:
                        if get_point_total(pc=True):
                            logging.info(msg=f'Stopped at search number {num}')
                            return
                        browser.get(BING_SEARCH_URL)
            except UnexpectedAlertPresentException:
                # this captures alerts such as bing asking for location information for certain search terms
                logging.info(msg='Unexpected alert during search, returning to search URL')
                browser.get(BING_SEARCH_URL)


def iter_dailies():
    """
    Iterates through all outstanding dailies
    :return: None
    """
    browser.get(DASHBOARD_URL)
    time.sleep(4)
    # TODO there is an error here where the object cannot be converted to data, only happens on digital ocean
    #   may be related to a wait after a sleep.
    #   stack overflow states that it is likely related to ram, need 2gb over 1gb.
    open_offers = browser.find_elements_by_xpath('//span[contains(@class, "mee-icon-AddMedium")]')
    if open_offers:
        logging.info(msg=f'Number of incomplete offers: {len(open_offers)}')
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
            time.sleep(5)
            # check for sign-in prompt
            sign_in_prompt()
            # check for poll by ID

            if find_by_id('btoption0'):
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
        # check at the end of the loop to log if any offers are remaining
        browser.get(DASHBOARD_URL)
        time.sleep(0.1)
        wait_until_visible(By.TAG_NAME, 'body', 10)
        open_offers = browser.find_elements_by_xpath('//span[contains(@class, "mee-icon-AddMedium")]')
        logging.info(msg=f'Number of incomplete offers remaining: {len(open_offers)}')
    else:
        logging.info(msg='No dailies found.')


def explore_daily():
    # needs try/except bc these functions don't have exception handling built in.
    try:
        # select html to send commands to
        html = browser.find_element_by_tag_name('html')
        # scroll up and down to trigger points
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
    time.sleep(3)
    # click poll option
    choices = ['btoption0', 'btoption1']  # new poll format
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
    time.sleep(3)
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
        wait_until_clickable(By.ID, 'check', 10)
        click_by_id('check')
        # if the green check mark reward icon is visible, end loop
        time.sleep(3)
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


def sign_in_prompt():
    time.sleep(3)
    sign_in_prompt_msg = find_by_class('simpleSignIn')
    if sign_in_prompt_msg:
        logging.info(msg='Detected sign-in prompt')
        browser.find_element_by_link_text('Sign in').click()
        logging.info(msg='Clicked sign-in prompt')
        time.sleep(4)


def get_point_total(pc=False, mobile=False, log=False):
    """
    Checks for points for pc/edge and mobile, logs if flag is set
    :return: Boolean for either pc/edge or mobile points met
    """
    browser.get(POINT_TOTAL_URL)
    # get number of total number of points
    time.sleep(0.1)
    try:
        wait_until_visible(By.CLASS_NAME, 'credits2', 15)
        # get total points, capped to current item on wishlist
        current_point_total = list(map(int, browser.find_element_by_class_name('credits2').text.split(' of ')))[0]
        # get pc points
        current_pc_points, max_pc_points = map(int, browser.find_element_by_class_name('pcsearch').text.split('/'))
        # get mobile points
        current_mobile_points, max_mobile_points = \
            map(int, browser.find_element_by_class_name('mobilesearch').text.split('/'))
        # get edge points
        current_edge_points, max_edge_points = map(int,
                                                   browser.find_element_by_class_name('edgesearch').text.split('/'))
        # if log flag is provided, log the point totals
        if log:
            logging.info(msg=f'Total points = {current_point_total}')
            logging.info(msg=f'PC points = {current_pc_points}/{max_pc_points}')
            logging.info(msg=f'Edge points = {current_edge_points}/{max_edge_points}')
            logging.info(msg=f'Mobile points = {current_mobile_points}/{max_mobile_points}')

        # if pc flag, check if pc and edge points met
        if pc:
            if current_pc_points < max_pc_points or current_edge_points < max_edge_points:
                return False
            return True
        # if mobile flag, check if mobile points met
        if mobile:
            if current_mobile_points < max_mobile_points:
                return False
            return True
    except (NoSuchElementException, TimeoutException):
        return False


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


def ensure_pc_mode_logged_in():
    """
    Navigates to www.bing.com and clicks on ribbon to ensure logged in
    PC mode for some reason sometimes does not fully recognize that the user is logged in
    :return: None
    """
    browser.get(BING_SEARCH_URL)
    time.sleep(0.1)
    # click on ribbon to ensure logged in
    wait_until_clickable(By.ID, 'id_l', 15)
    click_by_id('id_l')
    time.sleep(0.1)


if __name__ == '__main__':
    try:
        # start logging
        init_logging()
        logging.info(msg='---------------------------------')
        logging.info(msg='--------------New----------------')
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

            if parser.mobile_mode:
                # MOBILE MODE
                logging.info(msg='***************MOBILE***************')
                # set up headless browser and mobile user agent
                browser = browser_setup(parser.headless_setting, MOBILE_USER_AGENT)
                try:
                    log_in(email, password)
                    browser.get(BING_SEARCH_URL)
                    # mobile search
                    search(search_list, mobile_search=True)
                    # get point totals if running just in mobile mode
                    if not parser.pc_mode or not parser.quiz_mode or not parser.email_mode:
                        get_point_total(mobile=True, log=True)
                    browser.quit()
                except KeyboardInterrupt:
                    browser.quit()
                except WebDriverException:
                    logging.info(msg=f'WebDriverException while executing mobile portion', exc_info=True)
                    browser.quit()

            if parser.pc_mode or parser.quiz_mode or parser.email_mode:
                # PC MODE
                logging.info(msg='***************PC***************')
                # set up edge headless browser and edge pc user agent
                browser = browser_setup(parser.headless_setting, PC_USER_AGENT)
                try:
                    log_in(email, password)
                    if parser.pc_mode:
                        browser.get(BING_SEARCH_URL)
                        # pc edge search
                        search(search_list)
                    if parser.quiz_mode:
                        # complete quizzes
                        iter_dailies()
                    if parser.email_mode:
                        click_email_links(email_links)
                    # ensure logged in, log points
                    ensure_pc_mode_logged_in()
                    get_point_total(log=True)
                except KeyboardInterrupt:
                    print('Stopping Script...')
                except WebDriverException:
                    logging.error(msg=f'WebDriverException while executing pc portion', exc_info=True)
                finally:
                    browser.quit()
            logging.info(msg='\n\n')
    except WebDriverException:
        logging.exception(msg='Failure at main()')
