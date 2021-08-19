import re
import sys
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

MAX_SECONDS_TO_WAIT_FOR_ELEMENT = 5

from datetime import datetime


def main(args):
    start_time = datetime.now()
    project_name = args[1]
    output_path = args[2]
    url = get_url(project_name)
    process(url, output_path)
    print(f'Done.')
    end_time = datetime.now()
    print('Duration: {}'.format(end_time - start_time))


def get_url(project_name):
    return f'https://crowdin.com/project/{project_name}/activity_stream'


def process(url, output_path=None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)
    df = None
    if click_show_more_while_available(driver):
        if expand_all_details_available(driver):
            df = get_activities_df(driver)
            if output_path is not None:
                df.to_csv(output_path, quoting=1, index=False)

    driver.quit()
    return df


def finished_loading_or_loaded_more_items(css):
    def _predicate(driver):
        next_item = driver.find_elements(by=By.CSS_SELECTOR, value=css)
        return next_item or driver.find_elements(by=By.CSS_SELECTOR,
                                                 value='li.create_project')
    return _predicate


def click_show_more_while_available(driver):
    items_css = '#activity-stream > div > ul > li'

    while True:
        try:
            loaded_items = driver.find_elements(by=By.CSS_SELECTOR,
                                                value=items_css)

            print('Loading more activities...')
            WebDriverWait(driver, MAX_SECONDS_TO_WAIT_FOR_ELEMENT).until(
                EC.element_to_be_clickable((By.ID, 'more_activity_btn'))
            ).click()

            next_item_css = items_css + f':nth-child({len(loaded_items) + 1})'
            WebDriverWait(driver, MAX_SECONDS_TO_WAIT_FOR_ELEMENT).until(
                finished_loading_or_loaded_more_items(next_item_css))

            print('Done.')
            if driver.find_elements_by_css_selector('li.create_project'):
                print('Loaded all items since the project was created.')
                return True

        except Exception as e:
            print(type(e))
            print(e)
            return False


def expand_all_details_available(driver):
    actions = ActionChains(driver)
    try:
        buttons = driver.find_elements_by_class_name('details_btn')
        print(f'Obtaining details of {len(buttons)} items...')
        for i, button in enumerate(buttons):
            # print(f'Loading details for item {i + 1}.')
            driver.execute_script('arguments[0].click();', button)
            time.sleep(0.2)
            # print('Done.')

        print('Loaded details for all items.')
        return True
    except Exception as e:
        print(type(e))
        print(e)
        return False


def get_activities_df(driver):
    print('Get activity details from loaded items...')
    list = driver.find_element_by_class_name('user-activities')
    activities = []
    for item in list.find_elements_by_tag_name('li'):
        is_activity_item = item.get_attribute('id')
        if not is_activity_item:
            continue

        activity_data = extract_activity_data(item)
        activities.append(activity_data)

    df = pd.DataFrame(activities)
    # TODO: Update the time with the hour and minute from <td> cells
    #       with class="sub-list-acitity-time"
    df['date'] = pd.to_datetime(1000 * df['date'], unit='ms')
    df = df.explode('articles')
    df = df.reset_index(drop=True)
    return df


def extract_activity_data(item):
    id = item.get_attribute('id')
    result = parse_id(id)

    user = item.find_element_by_css_selector('a.user-link').text
    result['user'] = user

    trs = item.find_elements_by_xpath('.//div/table/tbody/tr')
    articles = [get_article_from_tr(tr) for tr in trs]
    if not articles:
        spans = item.find_elements_by_css_selector('span.filename')
        articles = [span.text for span in spans]
    articles = [clean_article_name(article) for article in articles]
    result['articles'] = articles
    return result


def get_article_from_tr(tr):
    return tr.find_element_by_class_name('sub-list-acitity-file').text


def clean_article_name(article):
    result = re.sub(r'^/traducoes.+/([^/]+)/\1(?:\.md)?$', r'\1', article)
    result = re.sub(r'^/traducoes.+/([^/]+)/([^/]+?)(?:\.md)?$', r'\1/\2', result)
    result = re.sub(r'\.md$', '', result)
    result = re.sub(r'_', ' ', result)
    return result


def parse_id(id_text):
    id_regex = re.compile(r'^(.+?)-(\d+)-(\d+)$')
    match = re.match(id_regex, id_text)
    activity_type = match.group(1)
    user_id = int(match.group(2))
    date = int(match.group(3))
    return {
        'activity_type': activity_type,
        'user_id': user_id,
        'date': date
    }


if __name__ == "__main__":
    main(sys.argv)
