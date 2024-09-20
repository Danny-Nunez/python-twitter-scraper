import json
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from googletrans import Translator

def scrape_profile_for_latest_tweet(profile_url: str, headless: bool = True) -> str:
    """
    Scrape the latest tweet URL from a profile page.
    """
    with sync_playwright() as pw:
        # Launch the browser with headless mode based on the input parameter
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            # Go to the Twitter profile page
            page.goto(profile_url, timeout=60000)  # Increased timeout to 60 seconds

            # Wait for tweets to load
            page.wait_for_selector("article", timeout=60000)

            # Get the first tweet article element and extract the href of the tweet link
            latest_tweet = page.query_selector('article a[href*="/status/"]')
            if latest_tweet:
                latest_tweet_url = latest_tweet.get_attribute('href')
                # Complete the URL by adding the base Twitter domain
                full_tweet_url = f"https://x.com{latest_tweet_url}"
            else:
                raise Exception("No tweet link found using the selector.")

            return full_tweet_url

        except PlaywrightTimeoutError:
            print("TimeoutError: The selector was not found within the specified time.")
            # Optionally, take a screenshot for debugging
            page.screenshot(path="debug_profile_screenshot.png")
            # Optionally, save the page's HTML
            with open("debug_profile_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise  # Re-raise the exception after logging

        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally, take a screenshot for debugging
            page.screenshot(path="debug_profile_screenshot.png")
            # Optionally, save the page's HTML
            with open("debug_profile_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise  # Re-raise the exception after logging

        finally:
            browser.close()

def scrape_tweet(tweet_url: str, headless: bool = True) -> dict:
    """
    Scrape the contents of a tweet using its URL.
    """
    _xhr_calls = []

    def intercept_response(response):
        """Capture all background requests and save them."""
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)

    with sync_playwright() as pw:
        # Launch the browser with headless mode based on the input parameter
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Enable background request intercepting
        page.on("response", intercept_response)

        try:
            # Go to the tweet URL and wait for the page to load
            page.goto(tweet_url, timeout=60000)
            page.wait_for_selector("[data-testid='tweet']", timeout=60000)

            # Find all tweet background requests
            tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
            if tweet_calls:
                data = tweet_calls[0].json()
                return data['data']['tweetResult']['result']
            else:
                raise Exception("No relevant XHR calls found containing tweet data.")

        except PlaywrightTimeoutError:
            print("TimeoutError: The tweet page did not load within the specified time.")
            # Optionally, take a screenshot for debugging
            page.screenshot(path="debug_tweet_screenshot.png")
            # Optionally, save the page's HTML
            with open("debug_tweet_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise  # Re-raise the exception after logging

        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally, take a screenshot for debugging
            page.screenshot(path="debug_tweet_screenshot.png")
            # Optionally, save the page's HTML
            with open("debug_tweet_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise  # Re-raise the exception after logging

        finally:
            browser.close()

def translate_text(text: str, dest_language: str = 'es') -> str:
    """
    Translate the given text to the specified destination language.
    Default destination language is Spanish ('es').
    """
    translator = Translator()
    try:
        translation = translator.translate(text, dest=dest_language)
        return translation.text
    except Exception as e:
        print(f"Error during translation: {e}")
        return ""


def save_to_json(data: dict, filename: str = "results.json"):
    """
    Save the scraped data to a JSON file, overwriting any previous content.
    Includes the 'spanish_full_text' field.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    # Set headless_mode to False to run the browser in a visible window locally
    headless_mode = True  # Change to False for local testing

    # Step 1: Scrape the profile page for the latest tweet URL
    profile_url = "https://x.com/facil_pay"
    try:
        latest_tweet_url = scrape_profile_for_latest_tweet(profile_url, headless=headless_mode)
        print(f"Latest Tweet URL: {latest_tweet_url}")
    except Exception as e:
        print(f"Failed to scrape latest tweet URL: {e}")
        exit(1)

    # Step 2: Scrape the latest tweet content
    try:
        tweet_data = scrape_tweet(latest_tweet_url, headless=headless_mode)
    except Exception as e:
        print(f"Failed to scrape tweet data: {e}")
        exit(1)

    # Step 3: Translate the 'full_text' to Spanish and add it to the data
    try:
        if 'legacy' in tweet_data and 'full_text' in tweet_data['legacy']:
            original_text = tweet_data['legacy']['full_text']
            spanish_translation = translate_text(original_text, dest_language='es')
            tweet_data['legacy']['spanish_full_text'] = spanish_translation
            print("Translation added to the data.")
        else:
            print("No 'full_text' field found in the scraped data.")
    except Exception as e:
        print(f"Failed to translate text: {e}")

    # Step 4: Save the results to results.json
    save_to_json(tweet_data, "results/results.json")
