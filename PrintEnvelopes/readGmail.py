import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import PrintEnvelopes
import config

def nth_repl_all(s, sub, repl, nth):
    find = s.find(sub)
    # loop util we find no match
    i = 1
    while find != -1:
        # if i  is equal to nth we found nth matches so replace
        if i == nth:
            s = s[:find]+repl+s[find + len(sub):]
            i = 0
        # find + len(sub) + 1 means we start after the last match
        find = s.find(sub, find + len(sub) + 1)
        i += 1
    return s

def EmailToCSV():
    
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify']
        # 'https://www.googleapis.com/auth/gmail.labels']
    
    # DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'
    PRINT_ENVELOPES_PATH = config.PROJECT_DIRECTORY + "\\TCGPlayer\\PrintEnvelopes\\"
    # DIR_PATH = PrintEnvelopes.config.path
    CREDENTIAL_FILEPATH = PRINT_ENVELOPES_PATH + 'credentials.json'
    TOKEN_FILEPATH = PRINT_ENVELOPES_PATH + 'token.json'
    GETFROMTHISEMAIL = 'Eddie Fernandez <fernandezeddie54@gmail.com>'
    emailCSVFilePath = config.DOWNLOADS_DIRECTORY + '\\new_cards.csv'

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILEPATH):
        creds = Credentials.from_authorized_user_file(TOKEN_FILEPATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(               
                # your creds file here. Please create json file as here https://cloud.google.com/docs/authentication/getting-started
                CREDENTIAL_FILEPATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILEPATH, 'w') as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        # results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages',[])
        if not messages:
            print('No new messages.')
        else:
            message_count = 0
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                email_data = msg['payload']['headers']
                for values in email_data:
                    name = values['name']
                    if name == 'From':
                        from_name= values['value']
                        if from_name == GETFROMTHISEMAIL:
                            try:
                                data = msg['payload']['parts'][0]['body']['data']
                                data = msg['payload']['parts'][1]['body']['data']
                                byte_code = base64.urlsafe_b64decode(data)
                                text = byte_code.decode("utf-8")
                                # text = nth_repl_all(text, "\r\n", "", 2)
                                text = text.replace('<div>','')
                                text = text.replace('</div>','')
                                text = text.replace('&quot;','"')
                                text = text.replace('&#39;','\'')
                                text = text.replace('<br>','\n')
                                print (text)
                                with open(emailCSVFilePath, "w") as text_file:
                                    text_file.write(text)
                            except BaseException as error:
                                pass
                        # for part in msg['payload']['parts']:
                        #     try:
                        #         data = part['body']["data"]
                        #         byte_code = base64.urlsafe_b64decode(data)

                        #         text = byte_code.decode("utf-8")
                                # print ("This is the message: "+ str(text))
                                # print('text', text)

                                # mark the message as read (optional)
                                # msg  = service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()                                                       
                            # except BaseException as error:
                            #     pass                            
    except Exception as error:
        print(f'An error occurred: {error}')
    
    return emailCSVFilePath

# EmailToCSV()