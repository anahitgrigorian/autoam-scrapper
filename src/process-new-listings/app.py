import os
import requests
from bs4 import BeautifulSoup
import boto3
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def lambda_handler(event, context):
    try:
        # Read the IP address from Lambda environment variables
        ip_address = os.environ.get("AUTOAM_IP_ADDRESS")

        if not ip_address:
            raise Exception("AUTOAM_IP_ADDRESS environment variable is not set.")
        
        return {"statusCode": 200, "body": json.dumps({"msg": "NOT_IMPLEMENTED"})}

        for record in event['Records']:
            listing_url = json.loads(record['body'])
            get_data_from_listing(listing_url, ip_address)
                
        # Return the result
        return {"statusCode": 200, "body": json.dumps({"page_urls": page_urls})}
    except Exception as e:
        # Handle exceptions and return an error response
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_data_from_listing(listing_url, ip_address):
    # Hardcoded website URL (using the IP address)
    url = "https://{}/lang/en".format(ip_address)

    # Step 1: Send an HTTP GET request to the URL
    response = requests.get(url, verify=False)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Extract the cookies and CSRF token from the response
        autoam_session_cookie = response.cookies.get("autoam_session")
        xsrf_token_cookie = response.cookies.get("XSRF-TOKEN")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

        # Step 2: Make a GET request to the listing endpoint using the obtained CSRF token and cookies
        listing_page = "https://{}{}".format(ip_address, listing_url)  # Update URL for the GET request
        listing_headers = {
            'Host': 'auto.am',  # Set the Host header
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-CSRF-Token': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://auto.am',
            'Connection': 'keep-alive',
            'Referer': url,
            'Cookie': f'XSRF-TOKEN={xsrf_token_cookie}; autoam_session={autoam_session_cookie}'
        }

        # Step 3: Send an HTTP GET request to the listing endpoint with CSRF token, cookies, and data
        listing_response = requests.get(listing_url, headers=listing_headers, verify=False)

        # Check if the POST request was successful (status code 200)
        if listing_response.status_code == 200:
            # Extract URLs from the search results
            soup = BeautifulSoup(listing_response.text, 'html.parser')
            cars = soup.find_all(class_="card")
            page_urls = [car.select(".card-image a")[0].get("href") for car in cars]

            return page_urls
        else:
            raise Exception("Failed to make the POST request to the search endpoint. Status code: {}".format(post_response.status_code))
    else:
        raise Exception("Failed to retrieve cookies. Status code: {}".format(response.status_code))
