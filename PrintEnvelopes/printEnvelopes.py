from __future__ import print_function
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from win32com import client
from PrintEnvelopes.getFilePath import getFilePath
import time
import os
import io
import PrintEnvelopes.config

# pyinstaller --onefile print_envelopes.py

DIR_PATH = PrintEnvelopes.config.path
# DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'

def getCreds():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',]
    creds = None
    TOKEN_FILE_PATH = DIR_PATH + 'token.json'
    CREDENTIALS_FILE_PATH = DIR_PATH + 'credentials.json'

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def csvToGoogleSheet(CSV_PATH):
    SPREADSHEET_ID = '145tGd66L_iCf1cDkNvRDNy2K5JkzaYEoOI3sRBYcfKk'
    creds = getCreds()
    service = build('sheets', 'v4', credentials=creds)
    with open(CSV_PATH, 'r') as csv_file:
        csvContents = csv_file.read()

    batch_update_spreadsheet_request_body = {
        # A list of updates to apply to the spreadsheet.
        # Requests will be applied in the order they are specified.
        # If any request is not valid, no requests will be applied.
        'requests': [
            {
                'deleteRange': {
                    'range': {
                        'sheetId': 1161022821,
                        "startRowIndex": 0,
                        "endRowIndex": 1000,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1000,
                    },
                    "shiftDimension": 1,
                },
            },
            {
                'pasteData': {
                    "coordinate": {
                        "sheetId": 1161022821,
                        "rowIndex": "0",  # adapt this if you need different positioning
                        "columnIndex": "0", # adapt this if you need different positioning
                    },
                    "data": csvContents,
                    "type": 'PASTE_NORMAL',
                    "delimiter": ',',
                }
            }
        ]
    }
    request = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=batch_update_spreadsheet_request_body)
    response = request.execute()

def printWordDocument(filename):
    word = client.Dispatch("Word.Application")
    word.Documents.Open(filename)
    word.ActiveDocument.PrintOut()
    time.sleep(2)
    word.ActiveDocument.Close()
    word.Quit()

# creates an envelope in google docs and google drive then returns its document id
def createEnvelopeDoc():
    template_document_id = '1oGpzkpwi9GKWGZvz2qM0pEPblE2wEBUWR54YAU31vH0'
    google_sheets_id = '145tGd66L_iCf1cDkNvRDNy2K5JkzaYEoOI3sRBYcfKk'
    folder_id = '1uf7tP99QxoHhaXJOppqIEU1C9qdwzAFM' # None --> save in the parent folder
    worksheet_name = 'Sheet1'
    document_title = 'Shipping Envelopes'

    creds = getCreds()

    DRIVE = build('drive', 'v3', credentials=creds)
    DOCS = build('docs', 'v1', credentials=creds)
    SHEETS = build('sheets', 'v4', credentials=creds)

    responses = {}
    responses['sheets'] = SHEETS.spreadsheets().values().get(
        spreadsheetId=google_sheets_id,
        range=worksheet_name,
        majorDimension='ROWS',
    ).execute()

    records = responses['sheets']['values'][1:]

    responses['docs'] = DRIVE.files().copy(
        fileId=template_document_id,
        body={
            'parents': [folder_id],
            'name': document_title
        }
    ).execute()

    document_id = responses['docs']['id']

    REQUESTS = {
        'requests': []
    }

    for record in records:
        SHIPPING_ADDRESS = {
            'firstName': record[1],
            'lastName': record[2],
            'address1': record[3],
            'address2': record[4],
            'city': record[5],
            'state': record[6],
            'postalCode': record[7],
            'country': record[8],
        }
        REQUESTS['requests'].append({
            'insertText': {
                'text': "Eddie Fernandez\n19803 15th Ave E\nSpanaway, WA 98387\n\n\n\n			{} {}\n			{} {}\n			{}, {} {}".format(
                    SHIPPING_ADDRESS['firstName'],
                    SHIPPING_ADDRESS['lastName'],
                    SHIPPING_ADDRESS['address1'],
                    SHIPPING_ADDRESS['address2'],
                    SHIPPING_ADDRESS['city'],
                    SHIPPING_ADDRESS['state'],
                    SHIPPING_ADDRESS['postalCode'],
                ),
                'endOfSegmentLocation': {
                    'segmentId': '',
                }
            }
        })
        if record != records[-1]:
            REQUESTS['requests'].append({
                'insertPageBreak': {
                    'endOfSegmentLocation': {
                        "segmentId": '',
                    }
                }   
            })

    DOCUMENT = DOCS.documents().batchUpdate(
        documentId=document_id,
        body=REQUESTS
    ).execute()
    return DOCUMENT['documentId']

# takes a google document id and returns the raw file data of the document
# The google document id can be found in the url of a google doc or
# you can get them using the google api. DRIVE is the drive service 
# that you can get using this:  DRIVE = build('drive', 'v3', credentials=creds)
def googleDocIdToRawFileData(googleDocFileId):
    creds = getCreds()
    DRIVE = build('drive', 'v3', credentials=creds)
    WORD_DOC = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    PDF = 'application/pdf'
    TEXT = 'text/plain'
    request = DRIVE.files().export_media(fileId=googleDocFileId, mimeType=WORD_DOC)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')
    rawFileData = file.getvalue()
    resp = DRIVE.files().delete(fileId=googleDocFileId).execute()
    return rawFileData

# Takes in raw file data and creates a file named 'Shipping_Envelopes.doc'
# in the same directory as the file script.
# return fileName
def rawFileDataToFile(rawFileData):
    filePath =  DIR_PATH + 'Shipping_Envelopes.doc'
    print(filePath)
    with open(filePath, "wb") as binary_file:
        # Write bytes to file
        binary_file.write(rawFileData)
    return filePath

# Select a tcgplayer ready to ship export shipping csv file and prints shipping envelopes 
# addressed to all recipients
def printFromCsv(filePath):
    # filePath = getFilePath()
    csvToGoogleSheet(filePath)
    documentID = createEnvelopeDoc()
    rawFileData = googleDocIdToRawFileData(documentID)
    wordDocFilePath = rawFileDataToFile(rawFileData)
    printWordDocument(wordDocFilePath)
    os.remove(wordDocFilePath)

# printFromCsv()