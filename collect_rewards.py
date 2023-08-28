import time
from datetime import datetime
from colorama import init, Fore

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import requests
from web3 import Web3
from threading import Thread
from eth_account.messages import encode_defunct

web3 = Web3(Web3.HTTPProvider("https://bsc.blockpi.network/v1/rpc/public"))
max_retry = 10
threads_count = 5

headers = {
    'authority': 'graphql-ea.earnalliance.com',
    'accept': '*/*',
    'content-type': 'application/json',
    'origin': 'https://www.earnalliance.com',
    'referer': 'https://www.earnalliance.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'x-ea-platform': 'web',
}
init()

metamask_crx = "metamask.crx"

colors = {
    'time': Fore.MAGENTA,
    'account_info': Fore.CYAN,
    'message': Fore.BLUE,
    'error_message': Fore.RED,
    'reset': Fore.RESET
}


def read_file(filename):
    result = []
    with open(filename, 'r') as file:
        for tmp in file.readlines():
            result.append(tmp.replace('\n', ''))

    return result


def write_to_file(filename, text):
    with open(filename, 'a') as file:
        file.write(f'{text}\n')


def sign_signature(private_key, message):
    message_hash = encode_defunct(text=message)
    signed_message = web3.eth.account.sign_message(message_hash, private_key)

    signature = signed_message.signature.hex()
    return signature


def get_login_message(address):
    json_data = {
        'operationName': 'GetSecurityChallenge',
        'variables': {
            'address': address,
        },
        'query': 'query GetSecurityChallenge($address: String!) {\n  payload: securityChallenge(address: $address) {\n    challenge\n    __typename\n  }\n}',
    }

    response = requests.post(
        'https://graphql-ea.earnalliance.com/v1/graphql',
        headers=headers,
        json=json_data,
    ).json()

    return response['data']['payload']['challenge']


def get_pre_auth_token(address, message, signature):
    json_data = {
        'operationName': 'SignInWithMetamask',
        'variables': {
            'address': address.lower(),
            'message': message,
            'signature': signature,
        },
        'query': 'mutation SignInWithMetamask($address: String!, $message: String!, $signature: String!) {\n  payload: signIn(\n    args: {address: $address, message: $message, signature: $signature}\n  ) {\n    token\n    isNewUser\n    __typename\n  }\n}',
    }

    response = requests.post(
        'https://graphql-ea.earnalliance.com/v1/graphql',
        headers=headers,
        json=json_data,
    ).json()

    return response['data']['payload']['token']


def confirm_and_get_auth_token(token):
    params = {
        'key': 'AIzaSyD79OJpKaLDpdUO2UZrGNNU_14WyZPwB8w',
    }

    json_data = {
        'token': token,
        'returnSecureToken': True,
    }

    response = requests.post(
        'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken',
        params=params,
        headers=headers,
        json=json_data,
    ).json()

    return response['idToken']


def get_reward(auth, private):
    reward_headers = headers.copy()
    reward_headers['Authorization'] = 'Bearer ' + auth

    json_data = {
        'operationName': 'OpenDailyChest',
        'variables': {},
        'query': 'mutation OpenDailyChest {\n  payload: openDailyChest {\n    rarity\n    rewards {\n      reward {\n        rewardRarity\n        rewardKey\n        rewardType\n        displayName\n        __typename\n      }\n      rewardValue\n      __typename\n    }\n    __typename\n  }\n}',
    }

    response = requests.post(
        'https://graphql-ea.earnalliance.com/v1/graphql',
        headers=reward_headers,
        json=json_data,
    ).json()

    if 'data' in response:
        info = response['data']['payload']

        print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} |"
              f" {private} | {colors['message']}Today's rewards have been found!\n\t\t"
              f"Box rarity: {info['rarity']}; Box contains:\n", end='')

        for reward in info['rewards']:
            reward_name = reward["reward"]["rewardKey"]
            reward_value = reward["rewardValue"]
            print(f'\t\tReward name: {reward_name}; Reward value: {reward_value}')
            write_to_file('collected.txt', f'{private};{reward_name};{reward_value}')
        print(colors['reset'], end='')

        return True
    else:
        print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} |"
              f" {private} | {colors['message']}Reward not found. Waiting...\n", end='')
        return False


def add_metamask_wallet(private, driver):
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    time.sleep(5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/ul/li[1]/div/label')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/ul/li[2]/button')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div/button[1]')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/form/div[1]/label/input')
    button.send_keys('12121212')
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/form/div[2]/label/input')
    button.send_keys('12121212')

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/form/div[3]/label/input')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/form/button')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/button[1]')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[1]/div/div/label/input')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[2]/div/button[2]')
    button.click()
    time.sleep(0.5)

    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/button')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/button')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div/div[2]/button')
    button.click()
    time.sleep(1)

    ''' Setting up new metamask wallet'''
    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[1]/div/button')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/button')
    button.click()
    time.sleep(0.5)
    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[2]/div/div[2]/div[2]')
    button.click()
    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[2]/div/div/div[1]/div/input')
    button.send_keys(private)
    button = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/section/div[2]/div/div/div[2]/button[2]')
    button.click()


def connect_wallet_to_site(driver):
    driver.switch_to.window(driver.window_handles[0])
    driver.refresh()
    time.sleep(5)
    # Connecting wallet to earn alliance
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/nav/div/div[2]/button')
    button.click()
    time.sleep(0.5)
    button = driver.find_element(By.XPATH, '/html/body/div[14]/div[3]/div/section/div/div/div/button[4]')
    button.click()
    time.sleep(0.5)
    driver.switch_to.window(driver.window_handles[1])
    driver.refresh()
    time.sleep(5)
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[3]/div[2]/footer/button[2]')
    button.click()
    time.sleep(2)
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/footer/button[2]')
    button.click()
    time.sleep(2)
    driver.refresh()
    time.sleep(5)
    button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[3]/div/div[4]/footer/button[2]')
    button.click()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(5)


def main(private, driver):
    print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} | "
          f"{private} | {colors['message']}Start wallet connection{colors['reset']}\n", end='')
    driver.get('https://www.earnalliance.com/wall')
    time.sleep(1)
    try:
        add_metamask_wallet(private, driver)
        print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} | "
              f"{private} | {colors['message']}Private key successfully added to metamask"
              f"{colors['reset']}\n", end='')
    except:
        main(private, driver)
        return

    connect_wallet_to_site(driver)
    print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} |"
          f" {private} | {colors['message']}Wallet successfully connected to earnalliance.com"
          f"{colors['reset']}\n", end='')

    address = web3.eth.account.from_key(private).address
    msg = get_login_message(address)
    signed_message = sign_signature(private, msg)
    pre_auth = get_pre_auth_token(address, msg, signed_message)
    authorization = confirm_and_get_auth_token(pre_auth)

    retry_count = 0
    while True:
        if retry_count < max_retry:
            time.sleep(30)
            retry_count += 1
            if get_reward(authorization, private):
                break
        else:
            print(f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} | {private} |"
                  f" {colors['error_message']}Can't find the reward, maybe it's already claimed{colors['reset']}\n",
                  end='')
            write_to_file('reward_not_found.txt', private)
            break


def start_thread(index_):
    options = Options()
    options.add_extension(metamask_crx)
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        main(privates[index_], driver)
    except:
        print(index_)
        print(
            f"{colors['time']}{datetime.now().strftime('%d %H:%M:%S')}{colors['account_info']} | {privates[index_]} |"
            f" {colors['error_message']}Somthing went wrong :({colors['reset']}\n", end='')
        privates.append(privates[index_])
        time.sleep(100)


if __name__ == '__main__':
    privates = read_file('privates.txt')
    private_index = 0

    while privates:
        for _ in range(threads_count):
            thread = Thread(target=start_thread, args=(private_index, ))
            thread.start()
            private_index += 1
        time.sleep(30 * (max_retry + 1))

time.sleep(100)