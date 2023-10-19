import datetime as dt
import json
import os
import time

import requests
from dateutil.relativedelta import relativedelta
from requests.auth import HTTPDigestAuth


class Hikvision():

    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f'http://{self.ip}/ISAPI/'

    def _requests(self, method, res_url, payload=None):
        response = requests.request(method,
                                    url=self.base_url + res_url,
                                    data=payload, timeout=10,
                                    verify=False,
                                    auth=HTTPDigestAuth(self.username,
                                                        self.password))
        # print(res_url, response.status_code)
        return response.json()

    @staticmethod
    def hex_to_dec(value: str):
        dec_value = int(value, 16)
        return f'{dec_value:010}'

    def search_user(self, employee_id: str = None, pos: int = 0):
        res_url = 'AccessControl/UserInfo/Search?format=json'
        data = {"UserInfoSearchCond": {
                "searchID": '0',
                "maxResults": 30,
                "searchResultPosition": pos}}
        if employee_id:
            data["UserInfoSearchCond"]["fuzzySearch"] = employee_id
        payload = json.dumps(data)
        return self._requests('POST', res_url, payload)

    def search_card(self, pos: int = 0):
        res_url = 'AccessControl/CardInfo/Search?format=json'
        data = {"CardInfoSearchCond": {
                "searchID": '0',
                "maxResults": 30,
                "searchResultPosition": pos}}
        payload = json.dumps(data)
        return self._requests('POST', res_url, payload)

    def search_incomplete_set_cards(self, employee_id: str = None,
                                    qty_mifare_ids: int = 0):
        pos = 0
        cards, found_free = [], 0
        print(f'{self.ip} - looking for unfilled users...')
        while True:
            result = self.search_user(employee_id, pos)['UserInfoSearch']
            if qty_mifare_ids and found_free >= qty_mifare_ids:
                return cards, result['totalMatches']
            match result['responseStatusStrg']:
                case 'NO MATCH' | 'OK':
                    if result.get('UserInfo'):
                        for user in result['UserInfo']:
                            if user['numOfCard'] < 5:
                                free = 5 - user['numOfCard']
                                found_free += free
                                cards.append(
                                    (user['employeeNo'],
                                     free))
                    return cards, result['totalMatches']
                case 'MORE':
                    for user in result['UserInfo']:
                        if user['numOfCard'] < 5:
                            free = 5 - user['numOfCard']
                            found_free += free
                            cards.append(
                                (user['employeeNo'], free))
                    pos += 30
                    time.sleep(0.5)

    def get_number_users(self):
        res_url = 'AccessControl/UserInfo/Count?format=json'
        return self._requests('GET', res_url)['UserInfoCount']['userNumber']

    def get_number_cards(self) -> int:
        res_url = 'AccessControl/CardInfo/Count?format=json'
        return self._requests('GET', res_url)['CardInfoCount']['cardNumber']

    def get_employee_by_card(self, mifare_id: str):
        pos = 0
        while True:
            result = self.search_card(pos)['CardInfoSearch']
            match result['responseStatusStrg']:
                case 'NO MATCH' | 'OK':
                    if result.get('CardInfo'):
                        for card in result['CardInfo']:
                            if mifare_id == card['cardNo']:
                                return card['employeeNo']
                    return False
                case 'MORE':
                    for card in result['CardInfo']:
                        if mifare_id == card['cardNo']:
                            return card['employeeNo']
                    pos += 30

    def get_cards(self, employee_id: str = None):
        '''Query all cards or cards by employee_id (user name)'''
        pos = 0
        cards = []

        def append_cards(result):
            for card in result['CardInfo']:
                if employee_id and employee_id not in card['employeeNo']:
                    pass
                else:
                    cards.append(card['cardNo'])

        while True:
            result = self.search_card(pos)['CardInfoSearch']
            match result['responseStatusStrg']:
                case 'NO MATCH' | 'OK':
                    if result.get('CardInfo'):
                        append_cards(result)
                    return cards
                case 'MORE':
                    append_cards(result)
                    pos += 30

    def add_user_info(self, employee_id: str, name: str):
        res_url = 'AccessControl/UserInfo/Record?format=json'
        start = dt.datetime.now()
        end = start + relativedelta(years=10)
        payload = json.dumps(
            {"UserInfo": {"employeeNo": employee_id,
                          "name": name,
                          "userType": "normal",
                          "localUIRight": False,
                          "maxOpenDoorTime": 0,
                          "RightPlan": [{"doorNo": 1}],
                          "Valid": {
                              "enable": True,
                              "beginTime": start.strftime('%Y-%m-%dT%H:%M:%S'),
                              "endTime": end.strftime('%Y-%m-%dT%H:%M:%S'),
                              "timeType": "local"},
                          "userVerifyMode": ""}})
        return self._requests('POST', res_url, payload)

    def add_mifare_id(self, mifare_id: str, employee_id: str):
        time.sleep(0.5)  # otherwise, when adding in bulk, error 401
        res_url = 'AccessControl/CardInfo/Record?format=json'
        payload = json.dumps(
            {"CardInfo": {
                "employeeNo": employee_id,
                "cardNo": self.hex_to_dec(mifare_id),
                "cardType": "normalCard"}}
        )
        return self._requests('POST', res_url, payload)

    def add_users_and_cards(self, mifare_ids: list, user: str, number: int):
        '''Add new user and 5 cards'''
        ids = mifare_ids
        number = number
        last_index = 0
        while True:
            number += 1
            cards_limit = 5
            username = f'{user}{number}'
            self.add_user_info(username, username)
            for index, mifare_id in enumerate(ids[last_index:],
                                              start=last_index):
                if not cards_limit:
                    last_index = index
                    break
                self.add_mifare_id(mifare_id, username)
                if index == len(ids) - 1:
                    return
                cards_limit -= 1

    def del_user(self, employee_id: str):
        res_url = 'AccessControl/UserInfo/Delete?format=json'
        payload = json.dumps(
            {"UserInfoDelCond":
                {"EmployeeNoList": [{"employeeNo": employee_id}]}}
        )
        return self._requests('PUT', res_url, payload)

    def del_mifare_id(self, mifare_id: str):
        res_url = 'AccessControl/CardInfo/Delete?format=json'
        payload = json.dumps(
            {"CardInfoDelCond":
                {"CardNoList": [{"cardNo": mifare_id}]}}
        )
        return self._requests('PUT', res_url, payload)

    def clear_users(self, employee_id: str = None):
        while True:
            result = self.search_user(employee_id)['UserInfoSearch']
            match result['responseStatusStrg']:
                case 'NO MATCH':
                    break
                case 'OK' | 'MORE':
                    for user in result['UserInfo']:
                        self.del_user(user['employeeNo'])
        print(f'{self.ip} - сleaning done!')

    def clear_cards(self, mifare_ids: list):
        for ids in mifare_ids:
            self.del_mifare_id(ids)
        print(f'{self.ip} - mifare_id deleted!')

    def create_cards(self, mifare_ids: list, employee_id: str):
        users, number = self.search_incomplete_set_cards(employee_id,
                                                         len(mifare_ids))
        # users - list of user tuples (name, number of free seats)
        # number - number of the last created user
        match users, number:
            case [], _:
                # No users have been created or all users are full
                self.add_users_and_cards(mifare_ids, employee_id, number)
            case [_, *_], _:
                # There are incomplete users
                for user in users:
                    if not mifare_ids:
                        break
                    employee, num_of_card = user
                    add_quantity = (num_of_card
                                    if len(mifare_ids) >= num_of_card
                                    else len(mifare_ids))
                    for idx_n, _ in enumerate(range(add_quantity)):
                        self.add_mifare_id(mifare_ids[idx_n], employee)
                    mifare_ids = mifare_ids[add_quantity:]
                if mifare_ids:
                    self.add_users_and_cards(mifare_ids, employee_id, number)
        print(f'{self.ip} - mifare_id added!')

    def update_cards(self, external_mifIds: list, employee_id: str = None):
        with open('dump.txt',
                  'r' if os.path.exists('dump.txt') else 'a+') as f:
            exist_mifIds = f.read().splitlines()
        if not exist_mifIds or len(exist_mifIds) != self.get_number_cards():
            print(f'{self.ip} - get existing mifare_id...')
            exist_mifIds = self.get_cards(employee_id)
        # First, delete mifare ids that are in the panel,
        # but they are not in the current list of cards
        mifIds_to_deleted = list(set(exist_mifIds) - set(external_mifIds))
        if mifIds_to_deleted:
            print(f'{self.ip} - {len(mifIds_to_deleted)} '
                  'mifare_id to remove')
            self.clear_cards(mifIds_to_deleted)
        after_deletion = set(exist_mifIds) - set(mifIds_to_deleted)
        mifIds_to_added = list(map(lambda x: hex(int(x)).split('x')[-1],
                               set(external_mifIds) - set(after_deletion)))
        if mifIds_to_added:
            print(f'{self.ip} - {len(mifIds_to_added)} '
                  'mifare_id to add')
            self.create_cards(mifIds_to_added, employee_id)
        if not mifIds_to_deleted and not mifIds_to_added:
            print(f'{self.ip} - \033[32mno mifare_id to remove or add!\033[0m')


if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser
    from configparser import ConfigParser
    from multiprocessing import Process, active_children

    config = ConfigParser()
    config.read('settings.ini')

    IP = config.get('ip_list', 'IP').split()
    LOGIN = config.get('authorization', 'LOGIN')
    PASSWD = config.get('authorization', 'PASSWD')

    def get_number_cards():
        active = True
        while active:
            active = active_children()
            if not active:
                print('\nDONE:')
                for ip in IP:
                    after_execution = Hikvision(
                        ip, LOGIN, PASSWD).get_number_cards()
                    print(f'{ip} - \033[32mquantity of mifare_id after '
                          f'execution ({after_execution})\033[0m')
            time.sleep(1)

    def Parser():
        parser = ArgumentParser(
            prog='record_mifare_id',
            description='''Bulk record mifare_id in hikvision.''',
            epilog='''\033[36m(ノ ˘_˘)ノ\033[0m
                    https://github.com/dammaer/'''
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-u', '--update_from_file',
                           help=('Set the file name and update exist '
                                 'mifare ids from file. '
                                 'Example: -u mifare_add.txt -n user'),
                           metavar='filename')
        group.add_argument('-a', '--add_mifare_id',
                           nargs='+', type=str,
                           help=('Add mifare ids as argument value (hex). '
                                 'Example: -a 85EF77B4 7290FDE1 -n user'),
                           metavar='hex value')
        group.add_argument('-c', '--clear_users',
                           help=('Complete removal of users and their '
                                 'mifare_id. Example: -c -n user. '
                                 'All users named "user" will be deleted.'),
                           action='store_true')
        parser.add_argument('-n', '--name',
                            help=('Name of employees and users in cards. '
                                  'Example: -a 85EF77B4 -n user. Cards will '
                                  'be created with usernames user1, user2, '
                                  'etc. Default name: user.'),
                            metavar='name', default='user')
        return parser

    prs = Parser().parse_args(sys.argv[1:])

    if prs.add_mifare_id:
        print(f'Mifare_ids will be added for user with name "{prs.name}"!\n')
        for ip in IP:
            process = Process(
                target=Hikvision(ip, LOGIN, PASSWD).create_cards,
                args=(prs.add_mifare_id, prs.name))
            process.start()
        get_number_cards()

    if prs.update_from_file:
        print(f'Mifare_ids will be updated for user with name "{prs.name}"!\n')
        with open(prs.update_from_file, 'r') as f:
            external_mifIds = f.read().splitlines()
        external_mifIds = list(map(Hikvision.hex_to_dec, external_mifIds))

        for ip in IP:
            process = Process(
                target=Hikvision(ip, LOGIN, PASSWD).update_cards,
                args=(external_mifIds, prs.name))
            process.start()

        result = []
        active = True
        while active:
            active = active_children()
            if not active:
                print('\nDONE:')
                for ip in IP:
                    after_update = Hikvision(
                        ip, LOGIN, PASSWD).get_number_cards()
                    quantity = len(external_mifIds) == after_update
                    result.append(quantity)
                    print(f'{ip} - \033[32mthe quantity mifare_id matches '
                          f'({len(external_mifIds)})\033[0m'
                          if quantity
                          else f'{ip} - \033[31mthe quantity mifare_id '
                          f'not matches ({after_update})!\033[0m')
            time.sleep(1)

        if all(result):
            with open('dump.txt', 'w') as f:
                f.writelines('\n'.join(external_mifIds))

    if prs.clear_users:
        print(f'Users with the name "{prs.name}" and their '
              'mifare_id will be deleted!\n')
        for ip in IP:
            process = Process(
                target=Hikvision(ip, LOGIN, PASSWD).clear_users,
                args=(prs.name,))
            process.start()
        get_number_cards()
