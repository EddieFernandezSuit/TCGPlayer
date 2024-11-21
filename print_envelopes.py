from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from win32com import client
import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import config
import time
import os
import io

def get_service(service_name):
    SERVICE_VERSIONS = {
        'sheets': 'v4',
        'drive': 'v3',
        'docs': 'v1',
        'gmail': 'v1'
    }
    version = SERVICE_VERSIONS[service_name]

    creds = authenticate()
    service = build(service_name, version, credentials=creds)
    return service

def csv_to_google_sheet(csv_file_path):
    """
    Upload a CSV file to a Google Sheet.
    Args:
        csv_file_path (str): Path to the CSV file.
    """
    SPREADSHEET_ID = '145tGd66L_iCf1cDkNvRDNy2K5JkzaYEoOI3sRBYcfKk'
    
    with open(csv_file_path, 'r') as csv_file:
        csv_contents = csv_file.read()

    batch_update_spreadsheet_request_body = {
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
                    "data": csv_contents,
                    "type": 'PASTE_NORMAL',
                    "delimiter": ',',
                }
            }
        ]
    }
    request = SHEETS.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=batch_update_spreadsheet_request_body)
    request.execute()

def printWordDocument(filename):
    word = client.Dispatch("Word.Application")
    word.Documents.Open(filename)
    word.ActiveDocument.PrintOut()
    time.sleep(2)
    word.ActiveDocument.Close()
    word.Quit()

# creates an envelope in google docs and google drive then returns its document id
def create_envelope_doc():
    template_document_id = '1oGpzkpwi9GKWGZvz2qM0pEPblE2wEBUWR54YAU31vH0'
    google_sheets_id = '145tGd66L_iCf1cDkNvRDNy2K5JkzaYEoOI3sRBYcfKk'
    folder_id = '1uf7tP99QxoHhaXJOppqIEU1C9qdwzAFM'
    worksheet_name = 'Sheet1'
    document_title = 'Shipping Envelopes'

    records = SHEETS.spreadsheets().values().get(
        spreadsheetId=google_sheets_id,
        range=worksheet_name,
        majorDimension='ROWS',
    ).execute()['values'][1:]

    document_id = DRIVE.files().copy(
        fileId=template_document_id,
        body={
            'parents': [folder_id],
            'name': document_title
        }
    ).execute()['id']

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
def googleDocIdToRawFileData(googleDocFileId):
    WORD_DOC = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    request = DRIVE.files().export_media(fileId=googleDocFileId, mimeType=WORD_DOC)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')
    rawFileData = file.getvalue()
    DRIVE.files().delete(fileId=googleDocFileId).execute()
    return rawFileData

def rawFileDataToFile(rawFileData):
    filePath =  config.PRINT_ENVELOPES_DIRECTORY + 'Shipping_Envelopes.doc'
    print(filePath)
    with open(filePath, "wb") as binary_file:
        binary_file.write(rawFileData)
    return filePath

def downloadGoogleDocAsWordFile(googleDocFileId):

    WORD_DOC = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    request = DRIVE.files().export_media(fileId=googleDocFileId, mimeType=WORD_DOC)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')
    rawFileData = file.getvalue()
    DRIVE.files().delete(fileId=googleDocFileId).execute()
    
    filePath =  config.DOWNLOADS_DIRECTORY + 'Shipping_Envelopes.doc'
    print(filePath)
    with open(filePath, "wb") as binary_file:
        binary_file.write(rawFileData)
    return filePath

def print_from_csv(filePath):
    csv_to_google_sheet(filePath)
    documentID = create_envelope_doc()
    rawFileData = googleDocIdToRawFileData(documentID)
    wordDocFilePath = rawFileDataToFile(rawFileData)
    # wordDocFilePath = rawFileDataToFile(documentID)
    printWordDocument(wordDocFilePath)
    os.remove(wordDocFilePath)

    
def authenticate():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify']
    
    TOKEN_FILEPATH = config.PRINT_ENVELOPES_DIRECTORY + 'token.json'
    CREDENTIAL_FILEPATH = config.PRINT_ENVELOPES_DIRECTORY + 'credentials.json'

    creds = None
    if os.path.exists(TOKEN_FILEPATH):
        creds = Credentials.from_authorized_user_file(TOKEN_FILEPATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(               
                CREDENTIAL_FILEPATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILEPATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def email_to_csv():
    GETFROMTHISEMAIL = 'Eddie Fernandez <fernandezeddie54@gmail.com>'
    EMAILCSVFILEPATH = config.PROJECT_DIRECTORY + 'data\\email_cards.csv'

    results = GMAIL.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages',[])
    for message in messages:
        msg = GMAIL.users().messages().get(userId='me', id=message['id']).execute()
        email_data = msg['payload']['headers']
        from_name = next((value['value'] for value in email_data if value['name'] == 'From'), None)
        if from_name == GETFROMTHISEMAIL:
            data = msg['payload']['parts'][1]['body']['data']
            byte_code = base64.urlsafe_b64decode(data)
            text = byte_code.decode("utf-8")
            text = text.replace('<div>','').replace('</div>','').replace('&quot;','"').replace('&#39;','\'').replace('<br>','\n').replace('<div dir="ltr">','')
            with open(EMAILCSVFILEPATH, "w") as text_file:
                text_file.write(text)
            GMAIL.users().messages().trash(userId='me', id=message['id']).execute()
    
    return EMAILCSVFILEPATH


SHEETS = get_service('sheets')
DRIVE = get_service('drive')
DOCS = get_service('docs')
GMAIL = get_service('gmail')
