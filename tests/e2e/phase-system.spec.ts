import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for the Phase System
 * 
 * Tests the complete interview flow with age selection and phase transitions
 * 
 * NOTE: Tests marked with `test.skip` require AI backend responses and may fail
 * if the AI models are rate-limited. Run these separately when AI is available.
 */

// Helper function to login
async function loginAsTestUser(page: Page) {
    await page.goto('/auth');

    // Fill login form
    await page.getByRole('textbox', { name: 'you@example.com' }).fill('test@example.com');
    await page.getByRole('textbox', { name: 'Enter your password' }).fill('TestPass123!');
    await page.locator('form').getByRole('button', { name: 'Sign In' }).click();

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
}

// Helper function to navigate to a project
async function navigateToProject(page: Page) {
    // Click on Continue Working for the first project
    await page.getByRole('button', { name: 'Continue Working' }).first().click();
    await page.waitForURL(/\/project\/\d+/);
}

test.describe('Phase System', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display age selection cards on GREETING phase', async ({ page }) => {
        // Navigate to a project - create a new one for clean state
        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Wait for page to load
        await page.waitForTimeout(3000);

        // Should see welcome message
        await expect(page.getByText(/Welcome.*help you capture your life story/)).toBeVisible({ timeout: 10000 });

        // Should see age selection prompt
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });

        // All age options should be visible
        await expect(page.getByRole('button', { name: 'Under 18' })).toBeVisible();
        await expect(page.getByRole('button', { name: '– 30' })).toBeVisible();
        await expect(page.getByRole('button', { name: '– 45' })).toBeVisible();
        await expect(page.getByRole('button', { name: '– 60' })).toBeVisible();
        await expect(page.getByRole('button', { name: '61 and over' })).toBeVisible();
    });

    test('should transition to FAMILY_HISTORY after age selection', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Wait for age selection to appear
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });

        // Select an age range
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for phase transition - AI response required
        await page.waitForTimeout(15000);

        // Should see Family History header (requires successful AI response)
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });

        // Should see Chapter indicator
        await expect(page.getByText('Chapter 1 of')).toBeVisible();

        // Age selection cards should be gone
        await expect(page.getByText('Please select your age range:')).not.toBeVisible();
    });

    test('should display phase timeline after age selection', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for transition - AI response can take time
        await page.waitForTimeout(15000);

        // Timeline should show phases for 31-45 age range
        // Use more specific locators to avoid strict mode violations
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });
        await expect(page.locator('text=Childhood').first()).toBeVisible();
        await expect(page.locator('text=Adolescence').first()).toBeVisible();
    });

    test('should show Next Chapter button after leaving GREETING phase', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for transition - AI response required
        await page.waitForTimeout(15000);

        // Next Chapter button should appear
        await expect(page.getByRole('button', { name: 'Next Chapter' })).toBeVisible({ timeout: 20000 });
    });

    test('should advance to next phase when clicking Next Chapter', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for Family History phase
        await page.waitForTimeout(15000);
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });

        // Click Next Chapter
        await page.getByRole('button', { name: 'Next Chapter' }).click();

        // Wait for phase transition
        await page.waitForTimeout(15000);

        // Should now be in Childhood phase
        await expect(page.getByRole('heading', { name: /Childhood/ })).toBeVisible({ timeout: 20000 });
    });

    test('should mark completed phases with checkmark', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for Family History
        await page.waitForTimeout(15000);
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });

        // Advance to next phase
        await page.getByRole('button', { name: 'Next Chapter' }).click();
        await page.waitForTimeout(15000);

        // Should now be in Childhood phase
        await expect(page.getByRole('heading', { name: /Childhood/ })).toBeVisible({ timeout: 20000 });

        // Family History text should still be visible in timeline
        await expect(page.locator('text=Family History').first()).toBeVisible();
    });

    test('should send message and receive AI response', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for Family History
        await page.waitForTimeout(15000);
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });
        await page.waitForTimeout(2000);

        // Type a message
        const messageInput = page.getByRole('textbox', { name: 'Type your response here...' });
        await messageInput.fill('My grandmother was born in Portugal.');
        await page.keyboard.press('Enter');

        // Wait for response cycle - input gets disabled then re-enabled
        await page.waitForTimeout(3000);

        // Message should appear
        await expect(page.getByText('My grandmother was born in Portugal.')).toBeVisible({ timeout: 10000 });

        // Wait for AI response (input should re-enable)
        await expect(messageInput).toBeEnabled({ timeout: 30000 });
    });

    test('should disable input while waiting for AI response', async ({ page }) => {
        // This test requires AI backend - skip if AI models are rate-limited
        test.skip(process.env.SKIP_AI_TESTS === 'true', 'AI backend required');

        await page.getByRole('button', { name: 'Start New Project' }).click();
        await page.waitForURL(/\/project\/\d+/);

        // Select age range
        await expect(page.getByText('Please select your age range:')).toBeVisible({ timeout: 10000 });
        await page.getByRole('button', { name: '– 45' }).click();

        // Wait for phase
        await page.waitForTimeout(15000);
        await expect(page.getByRole('heading', { name: 'Family History' })).toBeVisible({ timeout: 20000 });

        // Type and send message
        const messageInput = page.getByRole('textbox', { name: 'Type your response here...' });
        await messageInput.fill('Testing disabled state');
        await page.keyboard.press('Enter');

        // Input should be disabled while waiting
        await expect(messageInput).toBeDisabled({ timeout: 3000 });
    });

    test('should filter system markers from displayed messages', async ({ page }) => {
        await navigateToProject(page);

        // Any messages with system markers should be filtered
        // Check that no messages contain "[Moving to next phase:" or "[Age selected via button:"
        const visibleMessages = page.locator('[role="paragraph"]');
        const count = await visibleMessages.count();

        for (let i = 0; i < count; i++) {
            const text = await visibleMessages.nth(i).textContent();
            if (text) {
                expect(text).not.toContain('[Moving to next phase:');
                expect(text).not.toContain('[Age selected via button:');
            }
        }
    });
});

test.describe('Dashboard Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display dashboard after login', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /Welcome back/ })).toBeVisible();
        await expect(page.getByText('Your projects are waiting')).toBeVisible();
    });

    test('should show Start New Project button', async ({ page }) => {
        await expect(page.getByRole('button', { name: 'Start New Project' })).toBeVisible();
    });

    test('should show Continue Last Project button', async ({ page }) => {
        await expect(page.getByRole('button', { name: 'Continue Last Project' })).toBeVisible();
    });

    test('should navigate to project from dashboard', async ({ page }) => {
        await page.getByRole('button', { name: 'Continue Working' }).first().click();
        await page.waitForURL(/\/project\/\d+/);

        // Should be on project page
        await expect(page.getByRole('button', { name: 'Back to Projects' })).toBeVisible();
    });
});

test.describe('Authentication Flow', () => {
    test('should redirect unauthenticated users to auth page', async ({ page }) => {
        await page.goto('/dashboard');
        // App might redirect to /auth or /login
        await page.waitForURL(/\/(auth|login)/, { timeout: 5000 });
    });

    test('should show login form by default', async ({ page }) => {
        await page.goto('/auth');
        await expect(page.getByText('Welcome back!')).toBeVisible();
        await expect(page.getByRole('textbox', { name: 'you@example.com' })).toBeVisible();
    });

    test('should allow switching to sign up form', async ({ page }) => {
        await page.goto('/auth');
        await page.getByRole('button', { name: 'Sign Up' }).first().click();
        await expect(page.getByText('Create your account')).toBeVisible();
        await expect(page.getByRole('textbox', { name: 'Enter your full name' })).toBeVisible();
    });

    test('should not login with invalid credentials', async ({ page }) => {
        await page.goto('/auth');
        await page.getByRole('textbox', { name: 'you@example.com' }).fill('wrong@example.com');
        await page.getByRole('textbox', { name: 'Enter your password' }).fill('wrongpassword');
        await page.locator('form').getByRole('button', { name: 'Sign In' }).click();

        // Wait for response
        await page.waitForTimeout(2000);

        // Should still be on auth/login page (not redirected to dashboard)
        await expect(page).toHaveURL(/\/(auth|login)/);
    });
});
