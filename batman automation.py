import asyncio
import os
import random
import string
from playwright.async_api import async_playwright

BATMAN_URL = os.environ.get("BATMAN_URL", "https://bt6688.net")
BATMAN_USER = os.environ.get("BATMAN_USER", "")
BATMAN_PASS = os.environ.get("BATMAN_PASS", "")

# Global browser session
_browser = None
_context = None
_page = None

def generate_password():
    """Auto generate password like Asdf1234"""
    upper = random.choice(string.ascii_uppercase)
    lower = ''.join(random.choices(string.ascii_lowercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return upper + lower + digits

async def get_page():
    global _browser, _context, _page
    if _page is None or _page.is_closed():
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        _context = await _browser.new_context()
        _page = await _context.new_page()
        await login(_page)
    return _page

async def login(page):
    """Login to Batman Agent Portal"""
    try:
        await page.goto(f"{BATMAN_URL}/login", wait_until="networkidle")
        await page.wait_for_selector('input[type="text"]', timeout=10000)
        
        # Fill username
        await page.fill('input[type="text"]', BATMAN_USER)
        
        # Fill password
        await page.fill('input[type="password"]', BATMAN_PASS)
        
        # Get captcha text
        captcha_text = await page.locator('.captcha, img + input, [class*="captcha"]').first.text_content()
        
        # Fill captcha
        captcha_inputs = await page.locator('input').all()
        for inp in captcha_inputs:
            placeholder = await inp.get_attribute('placeholder') or ''
            if 'captcha' in placeholder.lower() or 'code' in placeholder.lower():
                await inp.fill(captcha_text or '')
                break
        
        # Click login
        await page.click('button:has-text("Login"), input[type="submit"]')
        await page.wait_for_load_state("networkidle")
        
        print("✅ Batman Login Success")
        return True
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return False

async def add_player(customer_name, score):
    """Add new player and return credentials"""
    try:
        page = await get_page()
        
        # Go to account page
        await page.goto(f"{BATMAN_URL}/account", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Click ADD PLAYER
        await page.click('button:has-text("ADD PLAYER"), a:has-text("ADD PLAYER")')
        await page.wait_for_timeout(1500)
        
        # Get auto-generated username
        username_input = page.locator('input#username, input[name="username"]').first
        await username_input.wait_for(timeout=5000)
        username = await username_input.input_value()
        
        # If empty, get from placeholder or value
        if not username:
            username = await username_input.get_attribute('value') or ''
        
        # Generate password
        password = generate_password()
        
        # Fill password
        await page.fill('input[name="password"], input#password', password)
        
        # Fill name
        await page.fill('input[name="name"], input#name', customer_name)
        
        # Fill score
        await page.fill('input[name="score"], input#score', str(score))
        
        # Click Submit
        await page.click('button:has-text("Submit"), input[value="Submit"]')
        await page.wait_for_timeout(1000)
        
        # Click Confirm on dialog
        await page.click('button:has-text("Confirm")')
        await page.wait_for_timeout(2000)
        
        # Get success data from dialog
        success_text = await page.locator('.modal, .dialog, [class*="success"]').text_content()
        
        # Extract URL from success dialog
        game_url = "http://m.batman688.com"
        try:
            url_element = await page.locator('a:has-text("batman"), td:has-text("batman")').first.text_content()
            if url_element:
                game_url = url_element.strip()
        except:
            pass
        
        # Click OK
        try:
            await page.click('button:has-text("OK")')
        except:
            pass
        
        return {
            "success": True,
            "username": username,
            "password": password,
            "score": score,
            "url": game_url
        }
        
    except Exception as e:
        print(f"❌ Add Player Error: {e}")
        # Try re-login and retry once
        try:
            page = await get_page()
            await login(page)
        except:
            pass
        return {"success": False, "error": str(e)}

async def deposit(player_id, amount):
    """Deposit score to existing player"""
    try:
        page = await get_page()
        
        # Go to account page
        await page.goto(f"{BATMAN_URL}/account", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Search for player
        await page.fill('input[type="search"], input#search', player_id)
        await page.wait_for_timeout(1500)
        
        # Click DEP button for that player
        dep_buttons = await page.locator('button:has-text("DEP"), .dep-btn').all()
        
        if not dep_buttons:
            return {"success": False, "error": "Player not found"}
        
        await dep_buttons[0].click()
        await page.wait_for_timeout(1000)
        
        # Fill amount
        await page.fill('input[name="amount"], input#amount', str(amount))
        
        # Click Confirm
        await page.click('button:has-text("Confirm")')
        await page.wait_for_timeout(2000)
        
        # Confirm dialog
        try:
            await page.click('button:has-text("Confirm")')
            await page.wait_for_timeout(1500)
        except:
            pass
        
        return {
            "success": True,
            "player_id": player_id,
            "amount": amount
        }
        
    except Exception as e:
        print(f"❌ Deposit Error: {e}")
        return {"success": False, "error": str(e)}

async def withdraw(player_id, amount):
    """Withdraw score from player"""
    try:
        page = await get_page()
        
        await page.goto(f"{BATMAN_URL}/account", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Search for player
        await page.fill('input[type="search"], input#search', player_id)
        await page.wait_for_timeout(1500)
        
        # Click WDL button
        wdl_buttons = await page.locator('button:has-text("WDL"), .wdl-btn').all()
        
        if not wdl_buttons:
            return {"success": False, "error": "Player not found"}
        
        await wdl_buttons[0].click()
        await page.wait_for_timeout(1000)
        
        # Fill amount
        await page.fill('input[name="amount"], input#amount', str(amount))
        
        # Click Confirm
        await page.click('button:has-text("Confirm")')
        await page.wait_for_timeout(2000)
        
        try:
            await page.click('button:has-text("Confirm")')
            await page.wait_for_timeout(1500)
        except:
            pass
        
        return {
            "success": True,
            "player_id": player_id,
            "amount": amount
        }
        
    except Exception as e:
        print(f"❌ Withdraw Error: {e}")
        return {"success": False, "error": str(e)}
