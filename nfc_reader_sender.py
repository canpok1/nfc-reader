import glob
import os
import pickle
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

WATCH_TARGET = '/tmp/nfc-reader/*'
SAMPLE_SPREADSHEET_ID = '1m9qYN7rzIrnciJHBXfxrqJgdDSTeVSeWHroAH5JQ6Rs'
SAMPLE_RANGE_NAME = 'NFCタグ!A:B'

class SheetClient(object):
    def __init__(self):
        print('SheetClient.__init__() start')

        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds_file = 'credentials.json'
        self.creds_token = 'token.pickle'
        self.creds = self.__load_creds()
        self.service = self.__build_service()

        print('SheetClient.__init__() end')

    def __load_creds(self):
        print('SheetClient.__load_creds() start')
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
        print('SheetClient.__load_creds() end')
        return creds

    def __build_service(self):
        print('SheetClient.__build_service() start')
        service = build('sheets', 'v4', credentials=self.creds)
        print('SheetClient.__build_service() end')
        return service

    def get_values(self, sheet_id, range_name):
        print('SheetClient.get_values() start')
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=range_name).execute()
        values = result.get('values', [])
        print('SheetClient.get_values() end')
        return values

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

        print(str(body))

        result = sheet.values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        print('update result : ')
        print(result)

class Row():
    def __init__(self, index, idm, yyyymmdd, hhmmss):
        self.index = index
        self.idm = idm
        self.yyyymmdd = yyyymmdd
        self.hhmmss = hhmmss
        self.datetime = datetime.datetime.strptime(yyyymmdd+hhmmss, '%Y%m%d%H%M%S')

    def get_range(self):
        return 'NFCタグ!A' + str(self.index+1) + ':B'

    def get_row(self):
        # return [[self.idm, self.yyyymmdd + self.hhmmss]]
        return [[self.idm, self.datetime.strftime('%Y/%m/%d %H:%M:%S')]]

def main():
    files = sorted(glob.glob(WATCH_TARGET), reverse=True)
    if len(files) == 0:
        return

    client = SheetClient()
    values = client.get_values(SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
    idms = {}
    for index, value in enumerate(values):
        idm = value[0]
        idms[idm] = index
    maxIndex = len(values)-1

    print('---------- file check ----------')
    send_targets = {}
    remove_file_paths = []
    for file_path in files:
        file_name = os.path.basename(file_path)
        splited = file_name.split('_')

        if len(splited) != 3:
            print('skip : ' + file_name + ' => file name invalid')
            continue

        remove_file_paths.append(file_path)

        idm = splited[0]
        yyyymmdd = splited[1]
        hhmmss = splited[2]

        if send_targets.get(idm) != None:
            print('skip : ' + file_name + ' => old info')
            continue

        index = idms.get(idm)
        if index == None:
            maxIndex = maxIndex + 1
            print('send : ' + file_name + ' => insert:' + str(maxIndex))
            send_targets[idm] = Row(maxIndex, idm, yyyymmdd, hhmmss)
        else:
            print('send : ' + file_name + ' => update:' + str(index))
            send_targets[idm] = Row(index, idm, yyyymmdd, hhmmss)

    print('---------- send ----------')
    client.update(SAMPLE_SPREADSHEET_ID, send_targets.values())

    print('---------- remove ----------')
    for path in remove_file_paths:
        os.remove(path)
        print('removed: ' + path)
 
if __name__ == '__main__':
    main()
