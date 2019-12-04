import itertools
import json
import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tqdm import tqdm

SCOPES = ['https://mail.google.com/']


class Gmail:
    def __init__(self, username, senders):
        self.username = username
        self.api = self.get_api()
        self.senders = senders

    def get_api(self):
        creds = None
        token_name = f"token/{self.username}.pickle"
        if os.path.exists(token_name):
            with open(token_name, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            if not os.path.exists('token'):
                os.mkdir("token")
            with open(token_name, 'wb') as token:
                pickle.dump(creds, token)

        api = build('gmail', 'v1', credentials=creds)
        return api

    def get_mails_with_sender_address(self, sender_address):
        api = self.api.users().messages()
        filtered_messages = api.list(
            userId='me',
            labelIds=["UNREAD"],
            q=f'from:{sender_address}').execute()
        if filtered_messages["resultSizeEstimate"] == 0:
            return
        return filtered_messages["messages"]

    def read_mail(self, message):
        response = self.api.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"addLabelIds": [], "removeLabelIds": ["UNREAD"]}
        ).execute()
        return


def main(username_list, senders_list):
    for username, senders in zip(username_list, senders_list):
        client = Gmail(username, senders)
        read_mails = [
            messages for s in senders
            if (messages := client.get_mails_with_sender_address(s))]
        read_mails = list(itertools.chain.from_iterable(read_mails))
        print(f"{username}: 自動既読するメール{len(read_mails)}件")
        [client.read_mail(x) for x in tqdm(read_mails)]


if __name__ == '__main__':
    with open("data.json") as f:
        user_data = json.load(f)
    main(
        user_data.keys(),
        user_data.values()
    )
