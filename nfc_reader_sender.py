import glob
import os
import pickle
import datetime
import logging
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

APP_NAME = 'nfc-reader-sender'
WATCH_TARGET = '/tmp/nfc-reader/*'
SPREADSHEET_ID = '1m9qYN7rzIrnciJHBXfxrqJgdDSTeVSeWHroAH5JQ6Rs'
RANGE_NAME = 'NFCタグ!A:B'

def makeLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    client = google.cloud.logging.Client()
    gcpHandler = CloudLoggingHandler(client, name=APP_NAME)
    gcpHandler.setLevel(logging.INFO)
    logger.addHandler(gcpHandler)

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    logger.addHandler(stdoutHandler)

    return logger

class SheetClient(object):
    def __init__(self):
        self.logger = makeLogger(self.__class__.__name__)
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds_file = 'credentials/credentials.json'
        self.creds_token = 'credentials/token.pickle'
        self.creds = self.__load_creds()
        self.service = self.__build_service()

    def __load_creds(self):
        creds = None
        if os.path.exists(self.creds_token):
            with open(self.creds_token, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_file, self.scopes)
                creds = flow.run_console()
            with open(self.creds_token, 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def __build_service(self):
        return build('sheets', 'v4', credentials=self.creds)

    def get_values(self, sheet_id, range_name):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=range_name).execute()
        return result.get('values', [])

    def update(self, sheet_id, rows):
        sheet = self.service.spreadsheets()

        body = {
                'valueInputOption': 'RAW',
                'data': [],
        }
        for row in rows:
            data = {
                'range': row.get_range(),
                'values': row.get_row(),
                'majorDimension': 'ROWS',
            }
            body['data'].append(data)

        result = sheet.values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        self.logger.debug('update result : ')
        self.logger.debug(result)

class SendTarget():
    def __init__(self, path):
        self.logger = makeLogger(self.__class__.__name__)
        self.__path = path
        self.__renamed_path = None

        file_name_with_ext = os.path.basename(path)
        splited_by_ext = os.path.splitext(file_name_with_ext)

        file_name = splited_by_ext[0]
        self.__splited = file_name.split('_')
        self.__is_valid = len(self.__splited) == 3 and file_name == file_name_with_ext
        self.__is_latest = True
        self.__is_registered = True

    @property
    def path(self):
        return self.__path

    @property
    def renamed_path(self):
        return self.__renamed_path

    @property
    def file_name(self):
        if self.__renamed_path == None:
            return os.path.basename(self.__path)
        return os.path.basename(self.__renamed_path)

    @property
    def is_valid(self):
        return self.__is_valid

    @property
    def status(self):
        if not self.__is_valid:
            return 'skip'
        if not self.__is_latest:
            return 'skip'
        return 'send'

    @property
    def detail(self):
        if not self.__is_valid:
            return 'file name is invalid'
        if not self.__is_latest:
            return 'datetime is not latest'
        if self.__is_registered:
            return 'insert'
        return 'update'

    @property
    def idm(self):
        if self.__is_valid:
            return self.__splited[0]
        else:
            return None

    @property
    def is_latest(self):
        pass

    @is_latest.setter
    def is_latest(self, value):
        self.__is_latest = value

    @property
    def is_registered(self, value):
        self.__is_registered = value

    @property
    def yyyymmdd(self):
        if not self.__is_valid:
            return None
        return self.__splited[1]

    @property
    def hhmmss(self):
        if not self.__is_valid:
            return None
        return self.__splited[2]

    def rename(self):
        path = self.path + '.proc'
        os.rename(self.path, path)
        self.__renamed_path = path

    def should_remove(self):
        if not self.__is_valid:
            return False
        return True

class Row():
    def __init__(self, index, idm, yyyymmdd, hhmmss):
        self.logger = makeLogger(self.__class__.__name__)
        self.index = index
        self.idm = idm
        self.yyyymmdd = yyyymmdd
        self.hhmmss = hhmmss
        self.datetime = datetime.datetime.strptime(yyyymmdd+hhmmss, '%Y%m%d%H%M%S')

    def get_range(self):
        return 'NFCタグ!A' + str(self.index+1) + ':B'

    def get_row(self):
        return [[self.idm, self.datetime.strftime('%Y/%m/%d %H:%M:%S')]]

def main():
    logger = makeLogger(__name__)
    targets = []
    should_send = False

    logger.debug('---------- load files (' + WATCH_TARGET + ')----------')
    files = sorted(glob.glob(WATCH_TARGET), reverse=True)
    skip_count = 0
    if len(files) == 0:
        logger.debug('file is empty')
        return
    for file in files:
        target = SendTarget(file)
        targets.append(target)
        if target.is_valid:
            should_send = True
        else:
            skip_count+=1

    if should_send:
        count = len(files)
        logger.info(str(count) + ' files found. ' + str(skip_count) + ' files skip. (' + WATCH_TARGET + ')')
    else:
        for target in targets:
            logger.info(target.status + ' : ' + target.file_name + ' => ' + target.detail)
        return

    logger.debug('---------- rename target files ----------')
    for target in targets:
        if not target.is_valid:
            continue
        target.rename()
        logger.info('renamed: ' + target.path + ' => ' + target.renamed_path)

    logger.debug('---------- send targets ----------')
    client = SheetClient()
    values = client.get_values(SPREADSHEET_ID, RANGE_NAME)
    registered_idms = {}
    for index, value in enumerate(values):
        idm = value[0]
        registered_idms[idm] = index
    maxIndex = len(values)-1

    send_rows = {}
    for target in targets:
        if not target.is_valid:
            continue
        if not send_rows.get(target.idm) == None:
            target.is_latest = False
            continue
        index = registered_idms.get(target.idm)
        if index == None:
            maxIndex = maxIndex + 1
            send_rows[target.idm] = Row(maxIndex, target.idm, target.yyyymmdd, target.hhmmss)
        else:
            send_rows[target.idm] = Row(index, target.idm, target.yyyymmdd, target.hhmmss)

    for target in targets:
        logger.info(target.status + ' : ' + target.file_name + ' => ' + target.detail)

    client.update(SPREADSHEET_ID, send_rows.values())

    logger.debug('---------- remove target files ----------')
    for target in targets:
        if target.should_remove():
            os.remove(target.renamed_path)
            logger.info('removed: ' + target.renamed_path)

if __name__ == '__main__':
    main()
