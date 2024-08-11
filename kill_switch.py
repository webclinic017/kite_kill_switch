from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import mintotp
import traceback
import os
import time


current_file_path = os.path.dirname(os.path.realpath(__file__))


def get_client_doc_from_json(client_id):
   try:
       json_file = os.path.join(current_file_path,'credentials.json')
       with open(json_file) as f:
           data = json.load(f)
           return data[client_id]
   except Exception as e:
       traceback.print_exc()

def get_totp(userid):
    totp_key = get_client_doc_from_json(userid)['totp_key']
    totp = mintotp.totp(totp_key)
    return totp

def disable_segment(client_id):
    try:
        password = get_client_doc_from_json(client_id)['password']
        driver.get("https://console.zerodha.com/account/segment-activation")
        time.sleep(2)
        driver.find_element(by=By.ID,value="userid").send_keys(client_id)
        time.sleep(1)
        driver.find_element(by=By.ID,value="password").send_keys(password)
        time.sleep(1)
        driver.find_element(by = By.XPATH, value = "/html/body/div[1]/div/div/div[1]/div/div/div/form/div[4]/button").click()
        time.sleep(1)
        driver.find_element(by = By.XPATH, value = "/html/body/div[1]/div/div/div[1]/div[2]/div/div/form/div[1]/input").send_keys(get_totp(client_id))
        time.sleep(5)
        driver.find_element(by = By.XPATH, value = "/html/body/div[2]/div[2]/div/div/div/div[2]/div[1]/div[2]/div[4]/div[1]/div/div/div[2]/div[3]/div/div/div/label").click()
        time.sleep(1)
        driver.find_element(by = By.XPATH, value = "/html/body/div[2]/div[2]/div/div/div/div[2]/div[1]/div[2]/div[4]/div[1]/button").click()
        time.sleep(5)
        driver.find_element(by = By.XPATH, value = "/html/body/div[2]/div[2]/div/div/div[2]/div/div/div/div/form/div[2]/button[2]").click()
        time.sleep(10)
        driver.quit()
        # driver.implicitly_wait(10)
        # /html/body/div[2]/div[2]/div/div/div/div[2]/div[1]/div[2]/div[4]/div[1]/div/div/div[2]/div[3]/div/div/div/label
    except:
        traceback.print_exc()


def main(client_id):
    global driver
    options = webdriver.ChromeOptions()
    options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    # options.add_argument("--headless")
    disable_segment(client_id)


if __name__ == '__main__':
    global driver
    options = webdriver.ChromeOptions()
    options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    # options.add_argument("--headless")
    disable_segment("XQQ563")
    # driver.quit()