import os
import requests
import json
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    try:
        # Read the IP address from Lambda environment variables
        ip_address = os.environ.get("AUTOAM_IP_ADDRESS")

        if not ip_address:
            raise Exception("AUTOAM_IP_ADDRESS environment variable is not set.")

        # Hardcoded website URL (using the IP address)
        url = "https://{}/lang/en".format(ip_address)

        # Call the function to get the pages count
        pages_count = get_pages_count(url, ip_address)

        # Return the result
        return {"statusCode": 200, "body": json.dumps({"pages_count": pages_count})}
    except Exception as e:
        # Handle exceptions and return an error response
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_pages_count(url, ip_address):
    # Step 1: Send an HTTP GET request to the URL
    response = requests.get(url, verify=False)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Extract the cookies and CSRF token from the response
        autoam_session_cookie = response.cookies.get("autoam_session")
        xsrf_token_cookie = response.cookies.get("XSRF-TOKEN")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

        # Step 2: Make a POST request to the search endpoint using the obtained CSRF token and cookies
        post_url = "https://{}/search".format(ip_address)  # Update URL for the POST request
        post_headers = {
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

        post_data = {
            'search': json.dumps({
                "category": "1",
                "page": "1",
                "sort": "latest",
                "layout": "list",
                "user": {"dealer": "0", "official": "0", "id": ""},
                "year": {"gt": "1911", "lt": "2025"},
                "usdprice": {"gt": "0", "lt": "100000000"},
                "custcleared": "1",
                "mileage": {"gt": "10", "lt": "10000000"}
            })
        }

        # Step 3: Send an HTTP POST request to the search endpoint with CSRF token, cookies, and data
        post_response = requests.post(post_url, headers=post_headers, data=post_data, verify=False)

        # Check if the POST request was successful (status code 200)
        if post_response.status_code == 200:
            soup = BeautifulSoup(post_response.text, 'html.parser')
            pages_count = int(soup.select(".pagination li a")[-2].text)

            return pages_count
        else:
            raise Exception("Failed to make the POST request to the search endpoint. Status code: {}".format(post_response.status_code))
    else:
        raise Exception("Failed to retrieve cookies. Status code: {}".format(response.status_code))

