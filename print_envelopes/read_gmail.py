import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config

def email_to_csv():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify']
        # 'https://www.googleapis.com/auth/gmail.labels']
    
    PRINT_ENVELOPES_PATH = config.PROJECT_DIRECTORY + "print_envelopes\\"
    CREDENTIAL_FILEPATH = PRINT_ENVELOPES_PATH + 'credentials.json'
    TOKEN_FILEPATH = PRINT_ENVELOPES_PATH + 'token.json'
    GETFROMTHISEMAIL = 'Eddie Fernandez <fernandezeddie54@gmail.com>'
    emailCSVFilePath = config.DOWNLOADS_DIRECTORY + '\\new_cards.csv'

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
    try:
        service = build('gmail', 'v1', credentials=creds)
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
    except Exception as error:
        print(f'An error occurred: {error}')
    
    return emailCSVFilePath
