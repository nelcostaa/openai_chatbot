import { test, expect } from '@playwright/test';

/**
 * E2E Authentication Flow Tests
 * 
 * Tests user registration, login, logout, and token persistence
 */

test.describe('Authentication Flow', () => {
    // Unique email for each test run to avoid conflicts
    const timestamp = Date.now();
    const testEmail = `test${timestamp}@example.com`;
    const testPassword = 'TestPassword123!';
    const testFullName = 'Test User';

    test.beforeEach(async ({ page }) => {
        // Start from the home page
        await page.goto('/');
    });

    test('should register a new user successfully', async ({ page }) => {
        // Navigate to auth page
        await page.click('text=Login');

        // Wait for auth page to load
        await expect(page).toHaveURL('/auth');

        // Switch to register tab if not already there
        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        // Fill registration form
        await page.fill('input[name="email"], input[type="email"]', testEmail);
        await page.fill('input[name="fullName"], input[placeholder*="name"]', testFullName);
        await page.fill('input[name="password"], input[type="password"]', testPassword);

        // Submit registration
        await page.click('button[type="submit"]');

        // Should redirect to home page after successful registration
        await expect(page).toHaveURL('/', { timeout: 10000 });

        // User should be logged in - check for user menu or logout button
        await expect(page.getByText(testFullName).or(page.getByText('My Stories'))).toBeVisible();
    });

    test('should login with correct credentials', async ({ page }) => {
        // First register the user
        await page.goto('/auth');

        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');
        await page.waitForURL('/', { timeout: 10000 });

        // Logout
        await page.click('text=Logout, text=Sign out');

        // Now login again
        await page.goto('/auth');

        const loginButton = page.getByRole('button', { name: /login|sign in/i });
        if (await loginButton.isVisible()) {
            await loginButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');

        // Should redirect to home page
        await expect(page).toHaveURL('/', { timeout: 10000 });
        await expect(page.getByText(testFullName).or(page.getByText('My Stories'))).toBeVisible();
    });

    test('should reject login with incorrect password', async ({ page }) => {
        // First register the user
        await page.goto('/auth');

        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');
        await page.waitForURL('/', { timeout: 10000 });

        // Logout
        await page.click('text=Logout, text=Sign out');

        // Try to login with wrong password
        await page.goto('/auth');

        const loginButton = page.getByRole('button', { name: /login|sign in/i });
        if (await loginButton.isVisible()) {
            await loginButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[type="password"]', 'WrongPassword123!');
        await page.click('button[type="submit"]');

        // Should show error message
        await expect(page.getByText(/incorrect|invalid|wrong/i)).toBeVisible({ timeout: 5000 });

        // Should stay on auth page
        await expect(page).toHaveURL('/auth');
    });

    test('should persist authentication after page reload', async ({ page }) => {
        // Register and login
        await page.goto('/auth');

        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');
        await page.waitForURL('/', { timeout: 10000 });

        // Reload the page
        await page.reload();

        // Should still be logged in
        await expect(page.getByText(testFullName).or(page.getByText('My Stories'))).toBeVisible();
    });

    test('should logout successfully', async ({ page }) => {
        // Register and login
        await page.goto('/auth');

        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');
        await page.waitForURL('/', { timeout: 10000 });

        // Click logout
        await page.click('text=Logout, text=Sign out');

        // Should redirect to home and show login button
        await expect(page.getByRole('button', { name: /login/i })).toBeVisible();

        // Should not be able to access protected routes
        await page.goto('/my-stories');

        // Should redirect to auth or home
        await expect(page).toHaveURL(/\/auth|\/$/);
    });

    test('should protect routes that require authentication', async ({ page }) => {
        // Try to access protected route without auth
        await page.goto('/my-stories');

        // Should redirect to auth page
        await expect(page).toHaveURL(/\/auth|\/$/);
    });
});
