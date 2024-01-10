import os
import requests
from bs4 import BeautifulSoup
import boto3
import json

def lambda_handler(event, context):
    try:
        # Read the IP address from Lambda environment variables
        ip_address = os.environ.get("AUTOAM_IP_ADDRESS")
        sqs_queue_url = os.environ.get("SQS_QUEUE_URL")

        if not ip_address:
            raise Exception("AUTOAM_IP_ADDRESS environment variable is not set.")
        
        if not sqs_queue_url:
            raise Exception("SQS_QUEUE_URL environment variable is not set.")

        # Initialize SQS client
        sqs = boto3.client('sqs')

        for record in event['Records']:
            listing_url = json.loads(record['body'])
            get_data_from_listing(listing_url, ip_address)

            # If processing is successful, delete the message from the queue
            sqs.delete_message(
                QueueUrl=sqs_queue_url,
                ReceiptHandle=record['receiptHandle']
            )

        # Return the result
        return {"statusCode": 200, "body": json.dumps({"page_urls": page_urls})}
    except Exception as e:
        # Handle exceptions and return an error response
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_data_from_listing(listing_url, ip_address):
    # Step 1: Send an HTTP GET request to obtain cookies and CSRF token
    base_url = f"https://{ip_address}/lang/en"
    response = requests.get(base_url, verify=False)

    # Check if the initial request was successful (status code 200)
    if response.status_code == 200:
        # Extract cookies and CSRF token from the response
        autoam_session_cookie = response.cookies.get("autoam_session")
        xsrf_token_cookie = response.cookies.get("XSRF-TOKEN")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

        # Step 2: Make a GET request to the listing endpoint using CSRF token and cookies
        listing_page_url = f"https://{ip_address}{listing_url}"
        listing_headers = {
            'Host': 'auto.am',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-CSRF-Token': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://auto.am',
            'Connection': 'keep-alive',
            'Referer': base_url,
            'Cookie': f'XSRF-TOKEN={xsrf_token_cookie}; autoam_session={autoam_session_cookie}'
        }

        # Step 3: Send an HTTP GET request to the listing endpoint with CSRF token, cookies, and headers
        listing_response = requests.get(listing_page_url, headers=listing_headers, verify=False)

        # Check if the second request was successful (status code 200)
        if listing_response.status_code == 200:
            # Extract relevant information from the listing page
            soup = BeautifulSoup(listing_response.text, 'html.parser')
            car_year = soup.select('h1 a')[-3].text
            car_make = soup.select('h1 a')[-2].text
            car_model = soup.select('h1 a')[-1].text
            car_insert_date = soup.select('.attrs span')[0].text
            car_location = soup.select('.attrs span')[1].text
            car_price = soup.select('.offer-top-price .price span, .offer-top-price .price small')[0].text.replace(" ", "").lower()
            car_seller_id = soup.select('.ad-seller-details a.call-seller')[0].get('data-sellerid')
            car_pricing_attributes = soup.select('.offer-top-price .price-attrs')[0].text.lower()
            car_vin = soup.select('.pad-left-6')[0].text.strip() if len(soup.select('.pad-left-6')) > 0 else None
            car_is_exchangable = False
            car_pay_with_installments = False
            car_is_urgent = False
            car_options = soup.select('.ad-options')[0].text.strip() if len(soup.select('.ad-options')) > 0 else None

            if "exchange" in car_pricing_attributes:
                car_is_exchangable = True
            if "installments" in car_pricing_attributes:
                car_pay_with_installments = True
            if len(soup.select('.urgent-stiker')) > 0:
                car_is_urgent = True

            # Extract additional details from the listing page
            car_details = {}
            car_details_table = soup.select('.ad-det tr')
            for detail in car_details_table:
                key = detail.select('td')[0].text.lower().replace(" ", "_")
                value = detail.select('td')[1].span.text.strip().lower().strip('"') if detail.select('td')[1].span else detail.select('td')[1].text.strip().lower()
                car_details[key] = value

            if car_details["mileage"]:
                # Define a regex pattern to capture the mileage number and measurement type
                milage_list = car_details["mileage"].split()
                car_details["mileage"] = milage_list[0]
                car_details["milage_measurement"] = milage_list[1]

            # Print or return the extracted data as needed
            print(car_year, car_make, car_model, car_vin, car_is_urgent)
            print(car_is_exchangable, car_pay_with_installments)
            print(car_insert_date, car_location, car_price, car_seller_id)
            print(car_details)
            print(car_options)
        else:
            raise Exception(f"Failed to make the GET request to the listing endpoint. Status code: {listing_response.status_code}")
    else:
        raise Exception(f"Failed to retrieve cookies. Status code: {response.status_code}")
