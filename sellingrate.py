import os
import sys
import json
import time
import collections
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options 
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#建立货币中文名称与货币标准符号的映射列表
def currency_table(driver:webdriver) -> dict:
    try:
        currency_Xpath = WebDriverWait(driver,10).until(
            EC.presence_of_all_elements_located((By.XPATH,'//*[@id="desc"]/table/tbody/tr[position() >= 3]'))
        )
    except TimeoutException:
        print('捕获货币元素失败，请检查该页面是否有可获取信息')
    #定位所有货币的中文名称以及标准符号
    currency_notation = []
    currency_chinese = []

    for tr_element in currency_Xpath:
        #中文名称
        try:
            chinese_elements = tr_element.find_elements(By.XPATH,'./td[2]')
            #货币标准符号
            notation_elements = tr_element.find_elements(By.XPATH,'./td[5]')
        except NoSuchElementException:
            print('获取货币中文名称或货币标准符号失败，请检查该页面是否存在该元素')
        for i in chinese_elements:
            currency_chinese.append(i.text)
        for i in notation_elements:
            currency_notation.append(i.text)
    #将中文名称以及标准符号映射成字典
    return dict(zip(currency_notation,currency_chinese))


def get_price(driver:webdriver,date,currency):
    date = str(date)

    # 选择开始时间的日期
    try:
        start_date_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="historysearchform"]/div/table/tbody/tr/td[2]/div/input'))
        )
        start_date_input.click()
    except TimeoutException:
        print('捕获开始日期元素失败，请检查该页面是否有可获取信息')

    # 输入开始时间的日期
    start_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    start_date_input.clear()
    start_date_input.send_keys(start_date)

    # 选择结束时间的日期
    try:
        end_date_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="historysearchform"]/div/table/tbody/tr/td[4]/div/input'))
        )
        end_date_input.click()
    except TimeoutException:
        print('捕获结束日期元素失败，请检查该页面是否有可获取信息')

    # 输入结束时间的日期
    end_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    end_date_input.clear()
    end_date_input.send_keys(end_date)

    #关闭日期选择框
    try:
        close_date = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="calendarClose"]'))
        )
        close_date.click()
    except TimeoutException:
        print('捕获日期选择框元素失败，请检查该页面是否有可获取信息')

    #货币选择
    try:
        currency_select = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="pjname"]'))
        )
    except TimeoutException:
        print('捕获货币选择菜单元素失败，请检查该页面是否有可获取信息')
    select = Select(currency_select)
    try:
        select.select_by_value(currency)
    except NoSuchElementException:
        print('选择货币种类时失败，请检查字典中该货币符号对应的中文名称是否与检索框一致')
    time.sleep(3)

    #搜索按钮
    try:
        search_button = WebDriverWait(driver,10).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="historysearchform"]/div/table/tbody/tr/td[7]/input'))
        )
        search_button.click()
    except TimeoutException:
        print('捕获搜索按钮元素失败，请检查该页面是否有可获取信息')

    #获取对应货币的现汇卖出价
    try:
        selling_rates = WebDriverWait(driver,10).until(
            EC.presence_of_all_elements_located((By.XPATH,'/html/body/div/div[4]/table/tbody/tr[position() >= 2]/td[4]'))
        )
    except TimeoutException:
        print('捕获现汇卖出价元素失败，请检查该页面是否有可获取信息')
    for selling_rate in selling_rates:
        rate = selling_rate.text
        if rate:
            return rate
    return None


if __name__=='__main__':
    # 获取命令行参数
    if len(sys.argv) != 3:
        print("Usage: python3 yourcode.py <date> <currency_code>")
        sys.exit(1)
    date = sys.argv[1]
    currency_code = sys.argv[2]

    #配置webdriver
    options = Options()
    driver = webdriver.Chrome(options=options)
    
    #获取字典对照表
    driver.get('https://www.11meigui.com/tools/currency')
    time.sleep(3)
    cur_notation_table = currency_table(driver)

    #货币对照表中文名称与中国银行外汇网牌价选择栏中的不一致、手动修改其中几则
    cur_notation_table['HKD'] = '港币'
    cur_notation_table['FRF'] = '法国法郎'
    cur_notation_table['DEM'] = '德国马克'
    cur_notation_table['CAD'] = '加拿大元'
    #检索货币现汇卖出价
    currency_code = cur_notation_table[f'{currency_code.upper()}']

    driver.get('https://srh.bankofchina.com/search/whpj/search_cn.jsp')
    time.sleep(3)
    selling_rate = get_price(driver,date=date,currency=currency_code)
    if selling_rate:
        print("现汇卖出价:", selling_rate)
        with open('result.txt','a',encoding = 'utf-8') as file:
            file.write(f'{date}时间下，{currency_code}的现汇卖出价为：{selling_rate}\n')
    else:
        print("现汇卖出价为空")
