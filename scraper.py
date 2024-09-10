import json
from playwright.sync_api import sync_playwright

def scrape_profile_for_latest_tweet(profile_url: str) -> str:
    """
    Scrape the latest tweet URL from a profile page.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()

        # Go to the Twitter profile page
        page.goto(profile_url)

        # Wait for tweets to load
        page.wait_for_selector("article")

        # Get the first tweet article element and extract the href of the tweet link
        latest_tweet = page.query_selector('article a[href*="/status/"]')
        latest_tweet_url = latest_tweet.get_attribute('href')

        # Complete the URL by adding the base Twitter domain
        full_tweet_url = f"https://x.com{latest_tweet_url}"
        browser.close()

        return full_tweet_url


def scrape_tweet(tweet_url: str) -> dict:
    """
    Scrape the contents of a tweet using its URL.
    """
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Enable background request intercepting
        page.on("response", intercept_response)

        # Go to the tweet URL and wait for the page to load
        page.goto(tweet_url)
        page.wait_for_selector("[data-testid='tweet']")

        # Find all tweet background requests
        tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
        for xhr in tweet_calls:
            data = xhr.json()
            return data['data']['tweetResult']['result']


def save_to_json(data: dict, filename: str = "results.json"):
    """
    Save the scraped data to a JSON file, overwriting any previous content.
    """
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    # Step 1: Scrape the profile page for the latest tweet URL
    profile_url = "https://x.com/facil_pay"
    latest_tweet_url = scrape_profile_for_latest_tweet(profile_url)
    print(f"Latest Tweet URL: {latest_tweet_url}")

    # Step 2: Scrape the latest tweet content
    tweet_data = scrape_tweet(latest_tweet_url)
    
    # Step 3: Save the results to results.json
    save_to_json(tweet_data, "results/results.json")
