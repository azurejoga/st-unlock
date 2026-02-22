"""
SteamUnlocked Web Interface
Complete web interface for searching, browsing, and auto-downloading games
"""
from flask import Flask, render_template, request, jsonify
import os
import asyncio
import threading
from scraper import SteamUnlockedScraper
from models import CATEGORIES
from playwright.async_api import async_playwright

app = Flask(__name__)

# Initialize scraper
scraper = SteamUnlockedScraper(request_delay=1.0)


async def auto_download_playwright_async(game_url: str, headless: bool = False):
    """
    Open the game page on SteamUnlocked and click download button using Playwright

    Args:
        game_url: URL of the game page on SteamUnlocked
        headless: Run in headless mode (default: False)
    """
    print("=" * 60)
    print("SteamUnlocked Auto Download - Playwright Version")
    print("=" * 60)
    print(f"\nGame URL: {game_url}\n")

    async with async_playwright() as p:
        # Launch browser
        print("Step 1: Launching browser...")
        browser = await p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        # Create context with realistic user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        try:
            # Step 2: Navigate to game page
            print("Step 2: Opening game page on SteamUnlocked...")
            await page.goto(game_url, wait_until='domcontentloaded', timeout=30000)
            print("✓ Game page loaded")

            # Step 3: Find download button
            print("\nStep 3: Looking for download button...")
            await page.wait_for_timeout(2000)  # Wait for dynamic content

            download_btn = None

            # Method 1: btn-download class
            try:
                download_btn = await page.query_selector("a.btn-download")
                if download_btn:
                    print("✓ Found download button (btn-download class)")
            except:
                pass

            # Method 2: Link with uploadhaven
            if not download_btn:
                try:
                    download_btn = await page.query_selector("a[href*='uploadhaven.com/download/']")
                    if download_btn:
                        print("✓ Found download button (uploadhaven link)")
                except:
                    pass

            if not download_btn:
                print("✗ Download button not found!")
                print("\nWaiting 10 seconds before closing...")
                await page.wait_for_timeout(10000)
                return False

            # Step 4: Scroll to button
            print("\nStep 4: Scrolling to download button...")
            await download_btn.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)

            # Highlight button
            await page.eval_on_selector("a.btn-download", "el => el.style.border='3px solid red'")

            # Step 5: Click download button
            print("\nStep 5: Clicking download button...")

            # Create new page for download link
            async with context.expect_page() as new_page_info:
                await download_btn.click()

            new_page = await new_page_info.value
            print("✓ Download button clicked!")

            # Step 6: Handle UploadHaven
            print("\nStep 6: Waiting for UploadHaven page...")
            await new_page.wait_for_load_state('domcontentloaded', timeout=15000)

            current_url = new_page.url
            print(f"Current URL: {current_url}")

            if "uploadhaven.com" in current_url:
                print("✓ UploadHaven page opened")

                # Look for countdown or download button
                print("\nStep 7: Looking for countdown/download button...")

                # Wait for page to fully load and countdown to complete (wait 16 seconds)
                print("⏳ Waiting 16 seconds for countdown to complete...")
                await new_page.wait_for_timeout(16000)
                print("✓ Initial wait completed")

                # Try to find countdown
                try:
                    # Look for countdown elements
                    countdown_elements = await new_page.query_selector_all("[class*='countdown'], [id*='countdown']")
                    if countdown_elements:
                        countdown_text = await new_page.evaluate("el => el.textContent", countdown_elements[0])
                        print(f"Countdown found: {countdown_text}")

                    # Look for free download button
                    free_download_btns = await new_page.query_selector_all("button:has-text('Free Download'), [class*='download']")
                    if free_download_btns:
                        print("✓ Free Download button found!")

                        # Check if enabled
                        is_enabled = await new_page.evaluate("el => !el.disabled", free_download_btns[0])

                        if is_enabled:
                            print("✓ Button is enabled, clicking...")
                            await free_download_btns[0].click()
                            print("✓ Download started!")
                        else:
                            print("⏳ Button is disabled, waiting for countdown...")

                            # Wait for button to become enabled (up to 60 seconds)
                            for i in range(60):
                                await new_page.wait_for_timeout(1000)
                                is_enabled = await new_page.evaluate("el => !el.disabled", free_download_btns[0])

                                if is_enabled:
                                    print(f"✓ Button enabled after {i+1} seconds, clicking...")
                                    await free_download_btns[0].click()
                                    print("✓ Download started!")
                                    break

                                if i % 10 == 0:
                                    print(f"  Waiting... {i}/60 seconds")
                    else:
                        print("⚠ No download button found yet")
                        print("  The countdown may still be running")

                except Exception as e:
                    print(f"Error handling UploadHaven: {e}")

                # Keep browser open for manual interaction if not headless
                if not headless:
                    print("\n" + "=" * 60)
                    print("Download initiated! Browser will stay open for 30 seconds")
                    print("You can interact with the browser if needed")
                    print("=" * 60)
                    await page.wait_for_timeout(30000)

            else:
                print(f"✗ Unexpected URL: {current_url}")
                print("Waiting 10 seconds before closing...")
                await page.wait_for_timeout(10000)

            return True

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await browser.close()
            print("\nBrowser closed")


def run_playwright_in_thread(game_url: str, headless: bool = False):
    """Run Playwright async function in a thread"""
    def run():
        asyncio.run(auto_download_playwright_async(game_url, headless))

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread


@app.route("/")
def index():
    """Home page with search and categories"""
    return render_template("index.html")


@app.route("/test")
def test():
    """Test page for API endpoints"""
    return render_template("test.html")


@app.route("/search")
def search():
    """Search results page"""
    query = request.args.get("q", "")
    return render_template("search.html", query=query)


@app.route("/category/<category>")
def category(category):
    """Category page"""
    return render_template("category.html", category=category)


@app.route("/games/az")
def games_az():
    """A-Z games page"""
    letter = request.args.get("letter", "")
    return render_template("games_az.html", letter=letter)


@app.route("/game/<path:game_url>")
def game(game_url):
    """Game details page"""
    # Construct full URL if needed
    if not game_url.startswith("http"):
        game_url = f"https://steamunlocked.org/{game_url}"

    return render_template("game.html", game_url=game_url)


@app.route("/api/search")
def api_search():
    """API: Search for games"""
    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", "20")

    if not query:
        return jsonify({"error": "Search query required"}), 400

    try:
        limit = int(limit)
    except ValueError:
        limit = 20

    games = scraper.search_games(query, max_results=limit)

    return jsonify({
        "query": query,
        "count": len(games),
        "results": [{
            "title": g.title,
            "url": g.url,
            "thumbnail": g.thumbnail,
            "slug": g.url.split("/")[-2] if g.url else ""
        } for g in games]
    })


@app.route("/api/category/<category>")
def api_category(category):
    """API: Get games by category"""
    page = request.args.get("page", "1")

    try:
        page = int(page)
    except ValueError:
        page = 1

    games = scraper.get_games_by_category(category.lower(), page=page)

    return jsonify({
        "category": category,
        "page": page,
        "count": len(games),
        "results": [{
            "title": g.title,
            "url": g.url,
            "thumbnail": g.thumbnail,
            "slug": g.url.split("/")[-2] if g.url else ""
        } for g in games]
    })


@app.route("/api/games/az")
def api_games_az():
    """API: Get A-Z games"""
    letter = request.args.get("letter", "").strip()
    page = request.args.get("page", "1")

    try:
        page = int(page)
    except ValueError:
        page = 1

    games = scraper.get_games_a_z(letter=letter or None, page=page)

    return jsonify({
        "letter": letter or "All",
        "page": page,
        "count": len(games),
        "results": [{
            "title": g.title,
            "url": g.url,
            "thumbnail": g.thumbnail,
            "slug": g.url.split("/")[-2] if g.url else ""
        } for g in games]
    })


@app.route("/api/categories")
def api_categories():
    """API: Get all categories"""
    categories = []
    for cat in CATEGORIES:
        slug = cat.lower().replace(" ", "-")
        categories.append({
            "name": cat,
            "slug": slug
        })

    return jsonify({"categories": categories})


@app.route("/api/game-info")
def api_game_info():
    """API: Get game details by slug"""
    slug = request.args.get("slug", "").strip()

    if not slug:
        return jsonify({"error": "Slug is required"}), 400

    try:
        # Construct full URL from slug
        game_url = f"https://steamunlocked.org/{slug}"

        # Fetch game details using scraper
        game_details = scraper.get_game_details(game_url)

        if game_details:
            return jsonify({
                "title": game_details.title,
                "url": game_details.url,
                "thumbnail": game_details.thumbnail,
                "description": game_details.description[:500] + "..." if game_details.description and len(game_details.description) > 500 else game_details.description,
                "screenshots": game_details.screenshots[:5],  # Limit to 5 screenshots
                "genre": game_details.genre,
                "developer": game_details.developer,
                "publisher": game_details.publisher,
                "release_date": game_details.release_date_full
            })
        else:
            return jsonify({"error": "Game not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auto-download-playwright", methods=["POST"])
def auto_download_playwright():
    """
    Start Playwright auto-download process

    JSON Body:
        - url: Game page URL on SteamUnlocked
        - headless: (optional) Run in headless mode (default: false)

    This endpoint runs the Playwright automation directly to automatically click download buttons
    """
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    game_url = data["url"]
    headless = data.get("headless", False)

    try:
        # Run Playwright directly in a thread
        thread = run_playwright_in_thread(game_url, headless)

        return jsonify({
            "success": True,
            "message": "Playwright auto-download started",
            "game_url": game_url,
            "thread_id": thread.ident,
            "headless": headless,
            "note": "Playwright is running in the background"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print("Starting SteamUnlocked Web Interface...")
    print("Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, debug=True)
