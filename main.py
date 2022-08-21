# -*- coding: utf-8 -*-

import datetime
import random
import string
import time
import os
import urllib.request

from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By


class Check:

    def __init__(self, proxy, url, min_likes, min_days, min_written):
        self.url = url
        self.domain_url = 'https://www.vinted.de'
        self.proxy = proxy
        self.min_likes = min_likes
        self.min_days = min_days
        self.min_written = min_written
        self.driver = self.get_driver()
        self.page = 1
        self.ads_to_check = []

    def get_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--proxy-server=%s' % self.proxy)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(40)
        return driver

    def open_url(self, url):
        tries = 0
        while tries < 4:
            try:
                self.driver.get(url)
                time.sleep(4)
                if '403 Forbidden' in self.driver.page_source or 'Не удается' in self.driver.page_source:
                    break
                return
            except:
                tries += 1
        raise Exception('too long wait page load')

    def wait_element(self, elem):
        tried = 0
        while True:
            try:
                self.driver.find_element(By.XPATH, elem)
                break
            except:
                tried += 1
            if tried >= 4:
                raise Exception('too long wait element load')
            time.sleep(2)

    def random_str(self, N=35):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))

    def check(self):
        while True:
            try:
                self.ads_to_check.clear()
                self.open_url(self.url[:-1] + str(self.page))
                logger.info(f'Паршу {self.page} страницу')
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('div', {'class': 'feed-grid__item'})
                if len(items) == 0:
                    raise Exception('no more items')
                # parse good items
                for item in items:
                    like_tags = item.find_all('h4')
                    for like_tag in like_tags:
                        if like_tag.text.isdigit():
                            likes = int(like_tag.text)
                            if likes >= self.min_likes:
                                item_link = item.find_all(href=True)[-1]['href']
                                if 'members' not in item_link:
                                    self.ads_to_check.append((item_link, likes))
                # check good items
                for good_item_data in self.ads_to_check:
                    date = None
                    days = 0
                    written = 0
                    good = True
                    item_link, item_likes = good_item_data
                    self.open_url(item_link)
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    item_details = soup.find_all('div', {'class': 'details-list__item-value'})
                    for detail in item_details:
                        if 'mitgli' in detail.text.lower():
                            written_list = [int(s) for s in detail.text.split() if s.isdigit()]
                            written = written_list[0]
                            if len(written_list) > 1:
                                print('aboba_written')
                            if written < self.min_written:
                                good = False
                                break
                        try:
                            date = detail.contents[1]['title'].split(' ')[0]
                            dtime = datetime.datetime.strptime(date, '%d.%m.%Y')
                            days = (datetime.datetime.today() - dtime).days
                            if days < self.min_days:
                                good = False
                                break
                        except:
                            pass
                    if good and days >= self.min_days and written >= self.min_written:
                        desc_tag = soup.find('div', {'class': 'details-list details-list--info'})
                        item_title = desc_tag.find('div', itemprop='name').text.replace('\n', ' ').strip()
                        try:
                            os.mkdir(item_title)
                        except:
                            continue
                        item_description = desc_tag.find('div', itemprop='description').text.replace('\n', ' ')
                        photos_tag = soup.find_all('div', {'class': 'item-photos'})
                        for photo_tag in photos_tag:
                            for photo_info in photo_tag.find_all(href=True):
                                photo_link = photo_info['href']
                                urllib.request.urlretrieve(photo_link, f'{item_title}/{self.random_str()}.jpg')
                        with open(f'{item_title}/result.txt', 'w', encoding='utf-8') as file:
                            file.write(f'Title: {item_title}\n'
                                       f'Link: {item_link}\n'
                                       f'Date: {date}\n'
                                       f'Anfragen: {written}\n\n'
                                       f'Description: {item_description}')
                        logger.success(item_title)
                self.page += 1
            except Exception as e:
                logger.error(f'check: {e}')
                try:
                    self.driver.quit()
                except:
                    pass


def read_input(text, integer=True):
    while True:
        try:
            data = input(text + ':\n')
            if integer:
                data = int(data)
            return data
        except:
            print('Похоже вы ввели не число, попробуйте еще раз.')


if __name__ == '__main__':
    link_parse = read_input('Введите ссылку на категорию с указателем страницы\n'
                            '(пример: https://www.vinted.de/vetements?catalog[]=2313&time=1661092977&page=1)\n'
                            '(плохой: пример https://www.vinted.de/unterhaltung/videospiele-and-konsolen)',
                            integer=False)
    min_likes = read_input('От скольки лайков парсить?')
    min_days = read_input('От скольки дней парсить?')
    min_written = read_input('От скольки написавших парсить?')
    check = Check('', link_parse, min_likes, min_days, min_written)
    check.check()
