# /usr/lib/python3.6
# bing_rewards.py - Searches for results via pc bing browser and mobile, completes quizzes on pc bing browser
# Attribution: https://newsapi.org - for free open source use of news api

import json
import time
import random
import logging
import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, \
    ElementClickInterceptedException, ElementNotVisibleException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# headless? True for headless mode, false for gui mode
headless_setting = True

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


def get_login_dict():
    """
    Gets login usernames and passwords from json file
    :return: Dictionary with usernames and passwords
    """
    with open('ms_rewards_login_dict.json', 'r') as f:
        return json.load(f)


def get_news_api_key():
    """
    Gets news api key from json file
    :return: String api key
    """
    with open('news_api_key.json', 'r') as f:
        return json.load(f)


def init_logging():
    logging.basicConfig(filename='ms_rewards.log', level=logging.INFO,
                        format='%(asctime)s :: %(levelname)s :: %(message)s')


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
        logging.exception(msg='Timeout Exception', exc_info=False)
    except WebDriverException:
        logging.exception(msg='Error.')


def wait_until_clickable(by_, selector, time_to_wait=10, custom_log='TimeouException'):
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
        logging.exception(msg='Error.')


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


def log_in(email_address, pass_word):
    logging.info(msg=f'Logging in {email_address}...')
    browser.get('https://login.live.com/')
    # wait for login form and enter email
    wait_until_clickable(By.NAME, 'loginfmt', 30)
    send_key_by_name('loginfmt', email_address)
    send_key_by_name('loginfmt', Keys.RETURN)
    logging.debug(msg='Sent Email Address.')
    # wait for password form and enter password
    wait_until_clickable(By.NAME, 'passwd')
    send_key_by_name('passwd', pass_word)
    logging.debug(msg='Sent Password.')
    # wait for 'sign in' button to be clickable and sign in
    wait_until_clickable(By.ID, 'idSIButton9')
    click_by_id('idSIButton9')
    logging.debug(msg='Clicked sign-in')


def get_news_api_search_terms(api_key):
    news_api_url = ('https://newsapi.org/v2/everything?'
                    'q=Cryptocurrency&'
                    'sortBy=popularity&'
                    'pageSize=50&'
                    f'apiKey={api_key}')
    try:
        request = requests.get(news_api_url)
        request.raise_for_status()
        results = request.json()['articles']
        search_terms = [results[i]['title'] for i in range(len(results))]
        if search_terms:
            search_terms = list(enumerate(set(search_terms), start=1))
            # logging.info(msg=f'# of search items: {len(search_terms)}\n')
        else:
            # logging.info(msg='No search values found!')
            pass
        return search_terms
    except RequestException:
        pass
        # logging.exception(msg='Search API failed.')


def search(search_terms):
    """
    Searches using an enumerated list of search terms, prints search item and number
    :param search_terms: enumerated list of tuples with search terms
    :return: None
    """
    logging.info(msg="Search Start")
    if search_terms == [] or search_terms is None:
        logging.info(msg="Search Aborted. No Search Terms.")
    else:
        browser.get(BING_SEARCH_URL)
        for num, item in search_terms:
            # clears search bar and enters in next search term
            wait_until_clickable(By.ID, 'sb_form_q')
            clear_by_id('sb_form_q')
            send_key_by_id('sb_form_q', item)
            send_key_by_id('sb_form_q', Keys.RETURN)
            # prints search term and item, limited to 80 chars
            logging.debug(msg=f'Search #{num}: {item[:80]}')
            time.sleep(random.randint(1, 3))


def iter_dailies():
    """
    Iterates through all outstanding dailies
    :return: None
    """
    browser.get(DASHBOARD_URL)
    wait_until_clickable(By.ID, 'signinhero', 30, 'Sign in splash not detected.')
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
        logging.exception(msg='TimeoutException.')
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
            # find any answers marked correct with green color
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
    firefox_browser_obj = webdriver.Firefox(firefox_options=options, firefox_profile=profile)
    return firefox_browser_obj


if __name__ == '__main__':
    try:
        # start logging
        init_logging()
        logging.info(msg='---------------------------------')
        logging.info(msg='---------------------------------')

        # get api key and get search terms
        news_api_key = get_news_api_key()
        search_list = get_news_api_search_terms(news_api_key)
        login_dict = get_login_dict()

        # iter through accounts, search, and complete quizzes
        for email, password in login_dict.items():
            # MOBILE MODE
            logging.info(msg='************MOBILE***************')
            # set up headless browser and mobile user agent
            browser = browser_setup(headless_setting, MOBILE_USER_AGENT)
            log_in(email, password)
            # mobile search
            search(search_list)
            browser.quit()

            # PC MODE
            logging.info(msg='************PC***************')
            # set up edge headless browser and edge pc user agent
            browser = browser_setup(headless_setting, PC_USER_AGENT)
            log_in(email, password)
            # pc edge search
            search(search_list)
            # complete quizzes
            iter_dailies()
            # get point totals
            get_point_total()
            browser.quit()

            logging.info(msg='\n\n')
    except WebDriverException:
        logging.exception(msg='Process error')
