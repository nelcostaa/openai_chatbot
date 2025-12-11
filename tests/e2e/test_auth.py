"""
E2E Authentication Flow Tests

Tests user registration, login, logout, and token persistence using Playwright.
"""

import re

import pytest
from playwright.sync_api import Page, expect


def test_registration_flow(page: Page, base_url: str):
    """Should register a new user successfully."""
    timestamp = page.evaluate("Date.now()")
    test_email = f"test{timestamp}@example.com"
    test_password = "TestPassword123!"
    test_full_name = "Test User"

    # Navigate to home page
    page.goto(base_url)

    # Click login/get started
    page.get_by_text(
        re.compile(r"Login|Get Started|Sign In", re.IGNORECASE)
    ).first.click()

    # Should be on auth page
    expect(page).to_have_url(re.compile(r"/auth"))

    # Switch to register tab
    register_button = page.get_by_role(
        "button", name=re.compile(r"Register|Sign Up", re.IGNORECASE)
    )
    if register_button.is_visible():
        register_button.click()

    # Fill registration form
    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[placeholder*="name"], input[name="fullName"]').fill(
        test_full_name
    )
    page.locator('input[type="password"]').fill(test_password)

    # Submit
    page.locator('button[type="submit"]').click()

    # Should redirect to home
    expect(page).to_have_url("/", timeout=15000)

    # User should be logged in
    expect(page.get_by_text(test_full_name)).to_be_visible()


def test_login_flow(page: Page, base_url: str):
    """Should login with correct credentials."""
    timestamp = page.evaluate("Date.now()")
    test_email = f"logintest{timestamp}@example.com"
    test_password = "TestPassword123!"
    test_full_name = "Login Tester"

    # Register first
    page.goto(f"{base_url}/auth")
    register_button = page.get_by_role(
        "button", name=re.compile(r"Register", re.IGNORECASE)
    )
    if register_button.is_visible():
        register_button.click()

    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[placeholder*="name"]').fill(test_full_name)
    page.locator('input[type="password"]').fill(test_password)
    page.locator('button[type="submit"]').click()
    expect(page).to_have_url("/", timeout=15000)

    # Logout
    page.get_by_text(re.compile(r"Logout|Sign Out", re.IGNORECASE)).first.click()

    # Login again
    page.goto(f"{base_url}/auth")
    login_button = page.get_by_role(
        "button", name=re.compile(r"Login|Sign In", re.IGNORECASE)
    ).first
    if login_button.is_visible():
        login_button.click()

    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[type="password"]').fill(test_password)
    page.locator('button[type="submit"]').click()

    # Should be logged in
    expect(page).to_have_url("/", timeout=15000)
    expect(page.get_by_text(test_full_name)).to_be_visible()


def test_incorrect_password_rejected(page: Page, base_url: str):
    """Should reject login with incorrect password."""
    timestamp = page.evaluate("Date.now()")
    test_email = f"wrongpass{timestamp}@example.com"
    test_password = "TestPassword123!"
    test_full_name = "Wrong Pass User"

    # Register
    page.goto(f"{base_url}/auth")
    register_button = page.get_by_role(
        "button", name=re.compile(r"Register", re.IGNORECASE)
    )
    if register_button.is_visible():
        register_button.click()

    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[placeholder*="name"]').fill(test_full_name)
    page.locator('input[type="password"]').fill(test_password)
    page.locator('button[type="submit"]').click()
    expect(page).to_have_url("/", timeout=15000)

    # Logout
    page.get_by_text(re.compile(r"Logout|Sign Out", re.IGNORECASE)).first.click()

    # Try wrong password
    page.goto(f"{base_url}/auth")
    login_button = page.get_by_role(
        "button", name=re.compile(r"Login", re.IGNORECASE)
    ).first
    if login_button.is_visible():
        login_button.click()

    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[type="password"]').fill("WrongPassword123!")
    page.locator('button[type="submit"]').click()

    # Should show error
    expect(
        page.get_by_text(re.compile(r"incorrect|invalid|wrong", re.IGNORECASE))
    ).to_be_visible(timeout=5000)

    # Stay on auth page
    expect(page).to_have_url("/auth")


def test_authentication_persistence(page: Page, base_url: str):
    """Should persist authentication after page reload."""
    timestamp = page.evaluate("Date.now()")
    test_email = f"persist{timestamp}@example.com"
    test_password = "TestPassword123!"
    test_full_name = "Persist User"

    # Register
    page.goto(f"{base_url}/auth")
    register_button = page.get_by_role(
        "button", name=re.compile(r"Register", re.IGNORECASE)
    )
    if register_button.is_visible():
        register_button.click()

    page.locator('input[type="email"]').fill(test_email)
    page.locator('input[placeholder*="name"]').fill(test_full_name)
    page.locator('input[type="password"]').fill(test_password)
    page.locator('button[type="submit"]').click()
    expect(page).to_have_url("/", timeout=15000)

    # Reload page
    page.reload()

    # Should still be logged in
    expect(page.get_by_text(test_full_name)).to_be_visible()


def test_protected_routes(page: Page, base_url: str):
    """Should protect routes that require authentication."""
    # Try to access protected route without login
    page.goto(f"{base_url}/my-stories")

    # Should redirect to auth or home
    expect(page).to_have_url(re.compile(r"/auth|/$"))
