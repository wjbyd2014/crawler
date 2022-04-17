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
    ret = []
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
            ref = 'http://quote.eastmoney.com/center/boardlist.html#boards2-90.%s' %  strs[1].split('/')[-1]
            ret.append((type_, ref, strs[2][1:-4].replace('/', '')))
    return ret

def download(sub_url, path):
    print("downloading " + sub_url[0] + ' ' + sub_url[1] + ' ' + sub_url[2])
    f = open(path + "\\result.txt", "w+")
    f.write(sub_url[1] + '\n')

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(DEFAULT_EXECUTABLE_PATH, DEFAULT_PORT, options)
    browser.get(sub_url[1])

    total = 0
    index = 1
    page_count = None
    last_result = read_page(browser.page_source)

    if not last_result:
        print('got an empty page, index = %d' % index)
        return False

    for r in last_result:
        total += 1
        f.write(r)

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
            sleep(0.5)

        result = read_page(browser.page_source)

        if not result:
            print('got an empty page, index = %d' % index)
            return False
        else:
            index += 1

        if result != last_result:
            last_result = result
            for r in last_result:
                total += 1
                f.write(r)
        else:
            print('got an same page, index = %d' % index)
            return False

        if len(last_result) % 20 != 0 or page_count == index:
            break

    f.close()
    print("total = %d" % total)
    return total > 0

def read_page(page):
    ret = []
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
                        number = page[i1+1:i2]
                    else:
                        ret.append(page[i1 + 1:i2] + ':' + number + '\n')
                    write_num += 1
                start = i2 + 1
            else:
                print("parse html error")
                break
    return ret

if __name__ == '__main__':
    if os.path.exists("crawler"):
        shutil.rmtree("crawler")
    os.mkdir("crawler")

    sub_urls = read_sub_urls('https://data.eastmoney.com/bkzj/gn.html')
    for sub_url in sub_urls:
        if not os.path.exists('crawler\\' + sub_url[0]):
            os.mkdir('crawler\\' + sub_url[0])

        path = 'crawler\\' + sub_url[0] + '\\' + sub_url[2]
        if not os.path.exists(path):
            os.mkdir(path)

        retry = 0
        while not download(sub_url, path):
            retry += 1
            print("download " + sub_url[0] + ' ' + sub_url[1] + ' ' + sub_url[2] + ' failed, retry = %d' % retry)
