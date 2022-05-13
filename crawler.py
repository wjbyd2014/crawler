# coding=utf-8
import shutil
from time import sleep
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import DEFAULT_EXECUTABLE_PATH
from selenium.webdriver.chrome.webdriver import DEFAULT_PORT
from selenium.webdriver.common.by import By


def read_sub_urls(url):
    ret_list = []
    str_html = requests.get(url)

    in_div = False
    index = 0
    for line in str_html.text.split('\n'):
        if line.find('<div class="pop-cont"') != -1:
            in_div = True
            index = index + 1

        if line.find('</div>') != -1 and in_div:
            in_div = False

        if in_div and index <= 2 and line.find('<a href=') != -1:
            strs = line.split('"')
            if index == 1:
                type_ = '行业资金'
            else:
                type_ = '概念资金'
            ref = 'http://quote.eastmoney.com/center/boardlist.html#boards2-90.%s' % strs[1].split('/')[-1]
            ret_list.append((type_, ref, strs[2][1:-4].replace('/', '')))
    return ret_list


def download(sub_url, num, total_num):
    print("downloading (%d / %d)" % (num, total_num) + sub_url[0] + ' ' + sub_url[1] + ' ' + sub_url[2])

    ret_list = list()
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(DEFAULT_EXECUTABLE_PATH, DEFAULT_PORT, options)
    browser.get(sub_url[1])

    page_count = None
    last_result = read_page(browser.page_source)
    index = 1
    if not last_result:
        print('got an empty page, index = %d' % index)
        return None

    for res in last_result:
        ret_list.append(res)

    while True:
        element = browser.find_element(By.CLASS_NAME, "page-wrapper")
        try:
            button = element.find_element(By.CLASS_NAME, "next.paginate_button")
            if not page_count:
                page_count = 0
                buttons = element.find_elements(By.CLASS_NAME, "paginate_button")
                for button in buttons:
                    data_index = button.get_attribute("data-index")
                    if data_index:
                        page_count = max(page_count, int(data_index))
        except:
            break
        else:
            browser.execute_script("$(arguments[0]).click()", button)
            sleep(0.3)

        result = read_page(browser.page_source)
        index += 1
        if not result:
            print('got an empty page, index = %d' % index)
            return None

        if result != last_result:
            last_result = result
            for res in last_result:
                ret_list.append(res)
        else:
            print('got a same page, index = %d' % index)
            return None

        if len(last_result) % 20 != 0 or page_count == index:
            break

    return ret_list


def read_page(page):
    ret_list = []
    start = None
    write_num = 1
    while True:
        index = page.find("unify", start)
        if index == -1:
            break
        else:
            i = index
            i1 = i2 = -1

            while True:
                if i == len(page):
                    break
                elif page[i] == '>':
                    i1 = i
                elif page[i] == '<':
                    i2 = i
                    break
                i += 1

            if i1 > 0 and i2 > 0:
                if i2 - i1 > 1:
                    if (write_num % 2) == 1:
                        number = page[i1 + 1:i2]
                    else:
                        ret_list.append(page[i1 + 1:i2] + ':' + number + ';')
                    write_num += 1
                start = i2 + 1
            else:
                print("parse html error")
                break
    return ret_list


def store(path, bkType, bkName, stockList):
    print(len(stockList))
    f = open(path + bkType + '.' + bkName + '.stock', "w+")
    for stock in stockList:
        f.write(stock)
    f.close()


if __name__ == '__main__':
    if os.path.exists("crawler"):
        shutil.rmtree("crawler")
    os.mkdir("crawler")

    sub_urls = read_sub_urls('https://data.eastmoney.com/bkzj/gn.html')

    total_num = len(sub_urls)
    num = 0
    for sub_url in sub_urls:
        if sub_url[2].find('ST') != -1 or sub_url[2].find('昨日') != -1:
            continue

        num += 1
        retry = 0
        while retry < 16:
            ret = download(sub_url, num, total_num)
            if not ret:
                retry += 1
                print("download " + sub_url[0] + ' ' + sub_url[1] + ' ' + sub_url[2] + ' failed, retry = %d' % retry)
            else:
                store('crawler\\', sub_url[0], sub_url[2], ret)
                break
