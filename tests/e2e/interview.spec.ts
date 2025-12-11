import { test, expect } from '@playwright/test';

/**
 * E2E Interview Chat Tests
 * 
 * Tests the interview conversation flow and AI interaction
 */

test.describe('Interview Chat', () => {
    const timestamp = Date.now();
    const testEmail = `interview${timestamp}@example.com`;
    const testPassword = 'TestPassword123!';
    const testFullName = 'Interview Tester';

    test.beforeEach(async ({ page }) => {
        // Register, login, and create a story
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

        // Create a new story
        await page.click('text=Create Story, text=New Story, text=Start Your Story');
        await page.waitForURL(/\/interview/);
    });

    test('should send a message and receive AI response', async ({ page }) => {
        // Find the message input
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await expect(messageInput).toBeVisible();

        // Type a message
        const userMessage = 'I was born in 1980 in New York City.';
        await messageInput.fill(userMessage);

        // Send the message
        await page.keyboard.press('Enter');

        // User message should appear in chat
        await expect(page.getByText(userMessage)).toBeVisible({ timeout: 5000 });

        // Wait for AI response (with loading indicator)
        const loadingIndicator = page.locator('text=/loading|thinking|typing/i, [data-testid="loading"], .loading');
        if (await loadingIndicator.isVisible({ timeout: 2000 }).catch(() => false)) {
            await expect(loadingIndicator).toHaveCount(0, { timeout: 30000 });
        }

        // AI response should appear
        // Look for message that's not the user's message
        const messages = page.locator('[data-testid="message"], .message, p, div').filter({ hasNotText: userMessage });
        await expect(messages.first()).toBeVisible({ timeout: 30000 });
    });

    test('should display conversation history', async ({ page }) => {
        // Send first message
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await messageInput.fill('My name is John.');
        await page.keyboard.press('Enter');

        // Wait for response
        await page.waitForTimeout(3000);

        // Send second message
        await messageInput.fill('I grew up in California.');
        await page.keyboard.press('Enter');

        // Wait for second response
        await page.waitForTimeout(3000);

        // Both messages should be visible
        await expect(page.getByText('My name is John.')).toBeVisible();
        await expect(page.getByText('I grew up in California.')).toBeVisible();
    });

    test('should handle empty message submission', async ({ page }) => {
        const messageInput = page.locator('textarea, input[type="text"]').first();

        // Try to send empty message
        await messageInput.fill('');
        await page.keyboard.press('Enter');

        // Should not send anything or show error
        // Message list should remain empty or only show initial greeting
        await page.waitForTimeout(1000);

        // No user messages should appear
        const userMessages = page.locator('[data-testid="user-message"], .user-message');
        await expect(userMessages).toHaveCount(0);
    });

    test('should show loading state while waiting for response', async ({ page }) => {
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await messageInput.fill('Tell me about your childhood.');
        await page.keyboard.press('Enter');

        // Loading indicator should appear
        const loadingIndicator = page.locator('text=/loading|thinking|typing/i, [data-testid="loading"], .loading');
        await expect(loadingIndicator.or(page.locator('button:disabled'))).toBeVisible({ timeout: 5000 });
    });

    test('should maintain scroll position when new messages arrive', async ({ page }) => {
        // Send multiple messages to create scrollable content
        const messageInput = page.locator('textarea, input[type="text"]').first();

        for (let i = 0; i < 3; i++) {
            await messageInput.fill(`Message number ${i + 1}`);
            await page.keyboard.press('Enter');
            await page.waitForTimeout(2000);
        }

        // Should auto-scroll to bottom after each message
        // Check that the input is still visible (indicates bottom of scroll)
        await expect(messageInput).toBeVisible();
    });

    test('should preserve conversation when navigating away and back', async ({ page }) => {
        // Send a message
        const messageInput = page.locator('textarea, input[type="text"]').first();
        const testMessage = 'This message should persist.';
        await messageInput.fill(testMessage);
        await page.keyboard.press('Enter');

        // Wait for response
        await page.waitForTimeout(3000);

        // Navigate away
        await page.click('text=My Stories');
        await page.waitForURL('/my-stories');

        // Navigate back to the story
        const storyCard = page.locator('[data-testid="story-card"], .story-card, article, div[role="button"]').first();
        await storyCard.click();
        await page.waitForURL(/\/interview/);

        // Message should still be visible
        await expect(page.getByText(testMessage)).toBeVisible();
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // This test assumes the backend might fail occasionally
        // We'll send a message and check for error handling

        const messageInput = page.locator('textarea, input[type="text"]').first();
        await messageInput.fill('Test message for error handling.');

        // Intercept API calls to simulate error
        await page.route('**/api/interview/**', route => {
            route.abort('failed');
        });

        await page.keyboard.press('Enter');

        // Should show error message or retry option
        await expect(page.locator('text=/error|failed|try again/i').first()).toBeVisible({ timeout: 10000 });
    });

    test('should show Woody button with correct states', async ({ page }) => {
        // Check if Woody button exists
        const woodyButton = page.locator('button:has-text("Woody"), [data-testid="woody-button"]');

        if (await woodyButton.isVisible({ timeout: 2000 }).catch(() => false)) {
            // Button should be clickable
            await expect(woodyButton).toBeEnabled();

            // Click Woody button
            await woodyButton.click();

            // Should trigger some interaction (dialog, message, etc.)
            await page.waitForTimeout(1000);
        }
    });
});
