import hmac
import hashlib
import base64
import requests
import datetime
import json
import os
import time
import argparse
import sys

from dotenv import load_dotenv
from typing import Optional
from utils.banner import generate_banner

# Tool to import your custom queries from BloodHound "Legacy" to BloodHound "Community".

# part of the code came from from: https://support.bloodhoundenterprise.io/hc/en-us/articles/11311053342619-Working-with-the-BloodHound-API.

# Load environment variables from .env file
load_dotenv()
BHE_DOMAIN = os.getenv("BHE_DOMAIN")
BHE_PORT = int(os.getenv("BHE_PORT"))
BHE_SCHEME = os.getenv("BHE_SCHEME")
BHE_TOKEN_ID = os.getenv("BHE_TOKEN_ID")
BHE_TOKEN_KEY = os.getenv("BHE_TOKEN_KEY")

# function to convert request to curl command. help me to understand and debug
def curlify(req):
    command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
    method = req.method
    headers = ['"{0}: {1}"'.format(k, v) for k, v in req.headers.items()]
    headers = " -H ".join(headers)
    data = req.body.decode() if req.body else ""
    uri = req.url
    return command.format(method=method, headers=headers, data=data, uri=uri)

class Credentials(object):
    def __init__(self, token_id: str, token_key: str) -> None:
        self.token_id = token_id
        self.token_key = token_key

class APIVersion(object):
    def __init__(self, api_version: str, server_version: str) -> None:
        self.api_version = api_version
        self.server_version = server_version

class Client(object):
    def __init__(self, scheme: str, host: str, port: int, credentials: Credentials) -> None:
        self._scheme = scheme
        self._host = host
        self._port = port
        self._credentials = credentials

    def _format_url(self, uri: str) -> str:
        formatted_uri = uri
        if uri.startswith("/"):
            formatted_uri = formatted_uri[1:]

        return f"{self._scheme}://{self._host}:{self._port}/{formatted_uri}"

    def _request(self, method: str, uri: str, body: Optional[bytes] = None) -> requests.Response:
        # Digester is initialized with HMAC-SHA-256 using the token key as the HMAC digest key.
        digester = hmac.new(self._credentials.token_key.encode(), None, hashlib.sha256)

        # OperationKey is the first HMAC digest link in the signature chain.
        digester.update(f"{method}{uri}".encode())

        # Update the digester for further chaining
        digester = hmac.new(digester.digest(), None, hashlib.sha256)

        # DateKey is the next HMAC digest link in the signature chain.
        datetime_formatted = datetime.datetime.now().astimezone().isoformat("T")
        digester.update(datetime_formatted[:13].encode())

        # Update the digester for further chaining
        digester = hmac.new(digester.digest(), None, hashlib.sha256)

        # Body signing is the last HMAC digest link in the signature chain.
        if body is not None:
            digester.update(body)

        # Perform the request with the signed and expected headers
        req = requests.Request(
            method=method,
            url=self._format_url(uri),
            headers={
                "User-Agent": "bhe-python-sdk 0001",
                "Authorization": f"bhesignature {self._credentials.token_id}",
                "RequestDate": datetime_formatted,
                "Signature": base64.b64encode(digester.digest()).decode(),
                "Content-Type": "application/json",
            },
            data=body,
        )
        prepped = req.prepare()
        # print(curlify(prepped))  # print curl command
        s = requests.Session()
        return s.send(prepped)

    def get_saved_queries(self):
        return self._request("GET", "/api/v2/saved-queries")

    def delete_saved_query(self, query_id):
        return self._request("DELETE", f"/api/v2/saved-queries/{query_id}")

    def get_version(self) -> APIVersion:
        response = self._request("GET", "/api/version")
        payload = response.json()
        return APIVersion(api_version=payload["data"]["API"]["current_version"], server_version=payload["data"]["server_version"])

def load_json(file_path):
    with open(file_path) as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f)

def build_json(customqueries_file, queries_to_import):
    data = load_json(customqueries_file)
    queries = [{'name': item['name'], 'query': item['queryList'][0]['query'], 'category': item['category']} for item in data['queries']]
    save_json(queries, queries_to_import)

def loop_old_queries(client, queries_to_import):
    queries = load_json(queries_to_import)
    for i, query in enumerate(queries):
        print(f"\n\n[{i}]")
        query_name = f"{query['category']} - {query['name']}"
        query_query = query['query']
        if '--------------' in query['name']:
            continue
        print(query_name)
        print(query_query)
        data = {'name': query_name, 'query': query_query}
        body = json.dumps(data).encode()
        response = client._request("POST", "/api/v2/saved-queries", body)
        print(f"\n{response.json()}")
        time.sleep(0.5)  # delay for 0.5 second
    os.remove(queries_to_import)

def loop_new_queries(client, new_customqueries_file):
    new_queries = load_json(new_customqueries_file)
    for i, new_query in enumerate(new_queries):
        print(f"\n\n[{i}]")
        new_query_name = new_query['name']
        new_query_query = new_query['query']
        print(new_query_name)
        print(new_query_query)
        data = {'name': new_query_name, 'query': new_query_query}
        body = json.dumps(data).encode()
        response = client._request("POST", "/api/v2/saved-queries", body)
        print(f"\n{response.json()}")
        time.sleep(0.5)

def print_saved_queries(client):
    response = client.get_saved_queries()
    queries = response.json()
    count = len(queries['data'])
    print(f"\nTotal saved queries: {count}")
    # print(json.dumps(queries, indent=2))

def delete_all_saved_queries(client):
    response = client.get_saved_queries()
    queries = response.json()

    for query in queries['data']:
        query_id = query['id']
        client.delete_saved_query(query_id)

def main():
    generate_banner()
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", dest="FILE", nargs='?', const='customqueries.json', help="import old customqueries.json file. (default: customqueries.json).")
    parser.add_argument("--new", dest="NEW_FILE", nargs='?', const='new_customqueries.json', help="new customqueries.json file to import from. (default: new_customqueries.json).")
    parser.add_argument("--delete", dest="TO_DELETE", action="store_true", help="delete all saved queries.")
    args = parser.parse_args()

    # If no arguments are provided, print the help message and exit
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    credentials = Credentials(token_id=BHE_TOKEN_ID, token_key=BHE_TOKEN_KEY)
    client = Client(scheme=BHE_SCHEME, host=BHE_DOMAIN, port=BHE_PORT, credentials=credentials)

    version = client.get_version()
    print(f"\nAPI version: {version.api_version} - Server version: {version.server_version}")

    if args.FILE and not args.TO_DELETE:
        build_json(args.FILE, 'queries-toimport.json')
        loop_old_queries(client, 'queries-toimport.json')

    if args.NEW_FILE and not args.TO_DELETE:
        print("\nImporting new queries...")
        loop_new_queries(client, args.NEW_FILE)

    if args.TO_DELETE:
        print("\nDeleting all saved queries...")
        delete_all_saved_queries(client)

    print_saved_queries(client)

if __name__ == "__main__":
    main()