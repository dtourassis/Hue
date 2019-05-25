import requests
import json
import logging
from time import sleep


class HueBridge:
    logger = logging.getLogger()

    def __init__(self):
        self.id_ = None
        self.internal_ip = None
        self.username = None
        self.start_logging(5)

    def info(self):
        return "ID: {} || Internal IP address: {} || Username: {}".format(self.id_, self.internal_ip, self.username)

    def authenticate(self):
        r = requests.get('http://{}/api/newdeveloper'.format(self.internal_ip))
        data = r.json()
        error = data[0]["error"]["type"]
        print(error)

    def create_user(self):
        self.logger.info('Press the link button on your Hue bridge!')
        url = 'http://{}/api'.format(self.internal_ip)
        params = {'devicetype': 'AutoHue#mydevice'}
        tries = 30
        while tries > 0 and self.username is None:
            r = requests.post(url, json=params)
            if r.status_code == 200:
                data = r.json()
                self.logger.debug(data)
                if data[0].get('success'):
                    self.username = data[0]['success']['username']
                    self.logger.debug('Successfully created new user! Username:{}'.format(self.username))
                    return True
            sleep(1)
            tries -= 1
        return False

    def setup(self):
        # load settings from configuration file
        load_config = self.load_config()
        if load_config:
            # verify the connection to the bridge
            if not self.test_connection() or not self.test_authentication():
                self.logger.info('Configuration file error. Starting discovery!')
                load_config = False
                self.id_ = None
                self.internal_ip = None
                self.username = None
            else:
                self.logger.info('Bridge setup successful!')
                return True
        if not load_config:
            # no or corrupt config -> start bridge discovery
            if self.discover():
                if self.create_user():
                    self.logger.info('Connected successfully to your Hue bridge!')
                    self.save_config()
                    return True
            else:
                self.logger.info('Could not discover any Hue bridges on your network!')

    def discover(self):
        self.logger.info("Searching for Hue bridges in your network!")
        # api-endpoint
        api = 'https://discovery.meethue.com/'
        # sending get request and saving the response in json format
        r = requests.get(api).json()
        # for debug purposes
        # r = [{"id":"001788fffe498011","internalipaddress":"192.168.11.111"},{"id":"001788fffe498022","internalipaddress":"192.168.22.222"},{"id":"001788fffe498033","internalipaddress":"192.168.33.333"}]
        # found multiple bridges in the network
        if len(r) > 1:
            self.logger.debug("Found multiple Hue bridges in your network!")
            for i in range(len(r)):
                print("No.{} => ID: {} || Internal IP address: {}".format(i, r[i]['id'], r[i]['internalipaddress']))
            sel = input("Type the No. of the bridge you want to connect and press enter:")
            self.id_ = r[int(sel)]['id']
            self.internal_ip = r[int(sel)]['internalipaddress']
            return True
        # found one bridge
        elif len(r) == 1:
            self.logger.debug('Found your Hue bridge!')
            self.id_ = r[0]['id']
            self.internal_ip = r[0]['internalipaddress']
            self.logger.debug(self.info())
            return True
        # found no bridges, user has to enter IP of the bridge manually
        else:
            self.logger.info("Couldn't find any Hue bridges in your network!")
            self.internal_ip = input("Please enter the IP of your Hue bridge:")
            if self.test_connection():
                return True
            else:
                return False

    def load_config(self):
        try:
            f = open('config.json')
            config = json.load(f)
            f.close()
        except:
            self.logger.debug('Could not find configuration file!')
            return False
        self.id_ = config['bridge']['id']
        self.internal_ip = config['bridge']['internal_ip']
        self.username = config['bridge']['username']
        return True

    def save_config(self):
        if self.internal_ip and self.username:
            try:
                f = open('config.json', 'w')
                data = {"bridge": {"id": self.id_, "internal_ip": self.internal_ip, "username": self.username}}
                json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)
                f.close()
                return True
            except IOError:
                self.logger.debug('Could not create configuration file!')
                return False

    def test_connection(self):
        # api-endpoint
        api = 'http://{}/api/config'.format(self.internal_ip)
        # sending get request
        try:
            r = requests.get(api).json()
            if self.id_ is None:
                self.id_ = r['bridgeid']
            self.logger.debug('Established connection with the bridge!')
            return True
        except:
            self.logger.info('Νο Hue bridge found with IP: {}'.format(self.internal_ip))
            return False

    def test_authentication(self):
        # api-endpoint
        api = 'http://{}/api/{}/lights'.format(self.internal_ip, self.username)
        # sending get request
        r = requests.get(api).json()
        self.logger.debug(r)
        try:
            if r[0]['error']['description'] == 'unauthorized user':
                self.logger.debug('Unauthorized user')
                return False
        except:
            self.logger.debug('Authentication successful!')
            return True

    def start_logging(self, level):
        fh = logging.FileHandler('log.txt')
        ch = logging.StreamHandler()
        if level == 5:
            self.logger.setLevel(logging.DEBUG)
            ch.setLevel(logging.INFO)
            fh.setLevel(logging.DEBUG)
        elif level == 4:
            self.logger.setLevel(logging.INFO)
            ch.setLevel(logging.INFO)
            fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        self.logger.debug('--------------------LOG STARTS HERE--------------------')

    def set_light(self, light_id, **args):
        # api-endpoint
        api = 'http://{}/api/{}/lights/{}/state'.format(self.internal_ip, self.username, light_id)
        # sending get request
        data = json.dumps(args)
        r = requests.put(api, data)
        print(r.json())
