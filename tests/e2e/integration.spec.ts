import { test, expect } from '@playwright/test';

/**
 * E2E Integration Test - Complete User Journey
 * 
 * Tests the full flow: Register → Login → Create Story → Chat → View Stories
 */

test.describe('Complete User Journey', () => {
    const timestamp = Date.now();
    const testEmail = `journey${timestamp}@example.com`;
    const testPassword = 'SecurePass123!';
    const testFullName = 'Journey Tester';
    const storyTitle = `Complete Journey Story ${timestamp}`;

    test('should complete full user journey from registration to story creation', async ({ page }) => {
        // Step 1: Visit home page
        await page.goto('/');
        await expect(page).toHaveTitle(/Life Story/i);

        // Step 2: Navigate to registration
        await page.click('text=Login, text=Get Started, text=Sign In');
        await expect(page).toHaveURL(/\/auth/);

        // Step 3: Register new account
        const registerButton = page.getByRole('button', { name: /register|sign up/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"], input[name="fullName"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');

        // Step 4: Should redirect to home page after registration
        await expect(page).toHaveURL('/', { timeout: 15000 });

        // Step 5: Verify user is logged in
        await expect(page.getByText(testFullName).or(page.getByText('My Stories'))).toBeVisible();

        // Step 6: Create a new story
        await page.click('text=Create Story, text=New Story, text=Start Your Story');
        await expect(page).toHaveURL(/\/interview|\/stories/, { timeout: 10000 });

        // Handle story title input if present
        const titleInput = page.locator('input[name="title"], input[placeholder*="title"]');
        if (await titleInput.isVisible({ timeout: 2000 }).catch(() => false)) {
            await titleInput.fill(storyTitle);
            await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Start")');
        }

        // Step 7: Send first message in interview
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await expect(messageInput).toBeVisible({ timeout: 5000 });

        const firstMessage = 'Hello, I am excited to share my life story!';
        await messageInput.fill(firstMessage);
        await page.keyboard.press('Enter');

        // Step 8: Verify message appears in chat
        await expect(page.getByText(firstMessage)).toBeVisible({ timeout: 5000 });

        // Step 9: Wait for AI response
        await page.waitForTimeout(3000);

        // Step 10: Send another message
        const secondMessage = 'I was born in 1985 in Seattle.';
        await messageInput.fill(secondMessage);
        await page.keyboard.press('Enter');
        await expect(page.getByText(secondMessage)).toBeVisible();

        // Step 11: Wait for second AI response
        await page.waitForTimeout(3000);

        // Step 12: Navigate to My Stories
        await page.click('text=My Stories');
        await expect(page).toHaveURL('/my-stories', { timeout: 10000 });

        // Step 13: Verify story appears in list
        await expect(page.locator('[data-testid="story-card"], .story-card, article').first()).toBeVisible();

        // Step 14: Open the story again
        const storyCard = page.locator('[data-testid="story-card"], .story-card, article, div[role="button"]').first();
        await storyCard.click();
        await expect(page).toHaveURL(/\/interview\/\d+/);

        // Step 15: Verify conversation history is preserved
        await expect(page.getByText(firstMessage)).toBeVisible();
        await expect(page.getByText(secondMessage)).toBeVisible();

        // Step 16: Send one more message
        const thirdMessage = 'My parents were teachers.';
        await messageInput.fill(thirdMessage);
        await page.keyboard.press('Enter');
        await expect(page.getByText(thirdMessage)).toBeVisible();

        // Step 17: Logout
        await page.click('text=Logout, text=Sign Out');
        await expect(page.getByRole('button', { name: /login/i })).toBeVisible({ timeout: 5000 });

        // Step 18: Login again
        await page.click('text=Login');
        await expect(page).toHaveURL(/\/auth/);

        const loginButton = page.getByRole('button', { name: /login|sign in/i }).first();
        if (await loginButton.isVisible()) {
            await loginButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');

        // Step 19: Verify login successful
        await expect(page).toHaveURL('/', { timeout: 15000 });
        await expect(page.getByText(testFullName).or(page.getByText('My Stories'))).toBeVisible();

        // Step 20: Check stories still exist
        await page.click('text=My Stories');
        await expect(page).toHaveURL('/my-stories');
        await expect(page.locator('[data-testid="story-card"], .story-card, article').first()).toBeVisible();

        // Step 21: Open story and verify all messages are still there
        await storyCard.click();
        await expect(page).toHaveURL(/\/interview\/\d+/);
        await expect(page.getByText(firstMessage)).toBeVisible();
        await expect(page.getByText(secondMessage)).toBeVisible();
        await expect(page.getByText(thirdMessage)).toBeVisible();
    });

    test('should handle errors during user journey gracefully', async ({ page }) => {
        // Visit home
        await page.goto('/');

        // Try to access protected route without auth
        await page.goto('/my-stories');

        // Should redirect to auth or home
        await expect(page).toHaveURL(/\/auth|\/$/);

        // Register
        await page.goto('/auth');
        const registerButton = page.getByRole('button', { name: /register/i });
        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail);
        await page.fill('input[placeholder*="name"]', testFullName);
        await page.fill('input[type="password"]', testPassword);
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL('/', { timeout: 15000 });

        // Now try to register with same email (should fail gracefully)
        await page.click('text=Logout, text=Sign Out');
        await page.goto('/auth');

        if (await registerButton.isVisible()) {
            await registerButton.click();
        }

        await page.fill('input[type="email"]', testEmail); // Same email
        await page.fill('input[placeholder*="name"]', 'Another Name');
        await page.fill('input[type="password"]', 'AnotherPass123!');
        await page.click('button[type="submit"]');

        // Should show error about existing email
        await expect(page.locator('text=/already exists|already registered/i')).toBeVisible({ timeout: 5000 });
    });

    test('should maintain UI responsiveness during heavy interaction', async ({ page }) => {
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
        await page.waitForURL('/', { timeout: 15000 });

        // Create story
        await page.click('text=Create Story, text=New Story');
        await page.waitForURL(/\/interview/);

        // Rapidly send multiple messages
        const messageInput = page.locator('textarea, input[type="text"]').first();

        for (let i = 0; i < 5; i++) {
            await messageInput.fill(`Rapid message ${i + 1}`);
            await page.keyboard.press('Enter');
            await page.waitForTimeout(500); // Brief pause between messages
        }

        // UI should still be responsive
        await expect(messageInput).toBeEnabled({ timeout: 5000 });

        // Navigate away while responses might still be processing
        await page.click('text=My Stories');
        await expect(page).toHaveURL('/my-stories');

        // Navigate back
        const storyCard = page.locator('[data-testid="story-card"], .story-card, article').first();
        await storyCard.click();
        await expect(page).toHaveURL(/\/interview/);

        // At least some messages should be visible
        await expect(page.getByText(/Rapid message/)).toHaveCount({ min: 1 });
    });
});
