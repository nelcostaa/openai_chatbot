import { test, expect } from '@playwright/test';

/**
 * E2E Story Management Tests
 * 
 * Tests creating, viewing, updating stories
 */

test.describe('Story Management', () => {
    const timestamp = Date.now();
    const testEmail = `storyt test${timestamp}@example.com`;
    const testPassword = 'TestPassword123!';
    const testFullName = 'Story Tester';

    const storyTitle = `My Test Story ${timestamp}`;

    test.beforeEach(async ({ page }) => {
        // Register and login before each test
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
    });

    test('should create a new story', async ({ page }) => {
        // Click create story button
        await page.click('text=Create Story, text=New Story, text=Start Your Story');

        // Should navigate to interview page or show story creation form
        await expect(page).toHaveURL(/\/interview|\/stories\/new/);

        // If there's a title input, fill it
        const titleInput = page.locator('input[name="title"], input[placeholder*="title"]');
        if (await titleInput.isVisible({ timeout: 2000 }).catch(() => false)) {
            await titleInput.fill(storyTitle);
            await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Start")');
        }

        // Should be on interview page with chat interface
        await expect(page.locator('textarea, input[type="text"]').first()).toBeVisible({ timeout: 5000 });
    });

    test('should view stories list', async ({ page }) => {
        // Create a story first
        await page.click('text=Create Story, text=New Story, text=Start Your Story');
        await page.waitForURL(/\/interview|\/stories/);

        // Navigate to My Stories
        await page.click('text=My Stories');
        await expect(page).toHaveURL('/my-stories');

        // Should show stories list
        await expect(page.getByText(/story|title|created/i).first()).toBeVisible();
    });

    test('should open existing story for interview', async ({ page }) => {
        // Create a story
        await page.click('text=Create Story, text=New Story, text=Start Your Story');
        await page.waitForURL(/\/interview|\/stories/);

        // Go to My Stories
        await page.click('text=My Stories');
        await page.waitForURL('/my-stories');

        // Click on a story to open it
        const storyCard = page.locator('[data-testid="story-card"], .story-card, article, div[role="button"]').first();
        await storyCard.click();

        // Should navigate to interview page
        await expect(page).toHaveURL(/\/interview\/\d+/);

        // Should show chat interface
        await expect(page.locator('textarea, input[type="text"]').first()).toBeVisible();
    });

    test('should show empty state when no stories exist', async ({ page }) => {
        // Navigate to My Stories immediately (no stories created)
        await page.click('text=My Stories');
        await expect(page).toHaveURL('/my-stories');

        // Should show empty state message
        await expect(page.getByText(/no stories|start your first|create a story/i)).toBeVisible();
    });

    test('should display story metadata', async ({ page }) => {
        // Create a story with chat
        await page.click('text=Create Story, text=New Story, text=Start Your Story');
        await page.waitForURL(/\/interview|\/stories/);

        // Send a message to create conversation history
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await messageInput.fill('Hello, I want to share my story');
        await page.keyboard.press('Enter');

        // Wait for response
        await page.waitForTimeout(2000);

        // Go to My Stories
        await page.click('text=My Stories');
        await page.waitForURL('/my-stories');

        // Should show story with metadata (title, date, status)
        await expect(page.locator('text=/created|draft|active|progress/i').first()).toBeVisible();
    });
});
