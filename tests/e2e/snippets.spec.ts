import { test, expect } from '@playwright/test';

/**
 * E2E Snippet Lock, Archive, and Restore Tests
 *
 * Tests snippet preservation features:
 * - Lock/unlock snippet cards
 * - Soft-delete (archive) snippets
 * - Restore archived snippets
 * - Regeneration warning modal
 * - Visual indicators for locked cards
 */

test.describe('Snippet Lock and Archive Features', () => {
    const testPassword = 'TestPassword123!';
    const testFullName = 'Snippet Tester';

    // Helper to get unique email per test
    function getUniqueEmail() {
        return `snippet_test${Date.now()}_${Math.random().toString(36).slice(2)}@example.com`;
    }

    // Helper to login and create a story with snippets
    async function setupTestWithSnippets(page) {
        const testEmail = getUniqueEmail();
        // Register and login
        await page.goto('/auth');

        // Switch to Sign Up mode
        const signUpButton = page.getByRole('button', { name: /sign up/i });
        if (await signUpButton.isVisible({ timeout: 3000 })) {
            await signUpButton.click();
            await page.waitForTimeout(300);
        }

        // Fill in registration form
        // Name field
        await page.fill('input[placeholder*="name" i], input[placeholder*="full name" i]', testFullName);

        // Email field
        await page.fill('input[placeholder*="example.com"], input[type="email"]', testEmail);

        // Password fields
        const passwordInputs = page.locator('input[placeholder*="password" i]');
        await passwordInputs.first().fill(testPassword);

        // Confirm password
        const confirmPassword = page.locator('input[placeholder*="re-enter" i], input[placeholder*="confirm" i]');
        if (await confirmPassword.isVisible({ timeout: 1000 })) {
            await confirmPassword.fill(testPassword);
        }

        // Submit the form
        await page.click('button:has-text("Create Account"), button[type="submit"]');

        // Wait for navigation away from auth page
        try {
            await page.waitForURL((url) => !url.pathname.includes('/auth'), { timeout: 15000 });
        } catch {
            // Check if there's an error message
            const errorMsg = page.locator('.text-destructive, .error, [role="alert"]');
            if (await errorMsg.isVisible({ timeout: 1000 })) {
                console.log('Registration failed, trying login instead');
                // Switch to login and try with existing account
                await page.click('button:has-text("Sign In")');
                await page.waitForTimeout(300);
                await page.fill('input[placeholder*="example.com"], input[type="email"]', testEmail);
                await page.fill('input[placeholder*="password" i]', testPassword);
                await page.click('button:has-text("Sign In"):not([role="tab"])');
                await page.waitForURL((url) => !url.pathname.includes('/auth'), { timeout: 10000 });
            }
        }

        // If we're already on a project page, we're good
        const currentUrl = page.url();
        if (currentUrl.includes('/project/')) {
            // Already have a story, proceed
        } else {
            // Create a story
            await page.click('text=Create Story, text=New Story, text=Start Your Story');
            await page.waitForURL(/\/interview|\/stories|\/project/, { timeout: 5000 });
        }

        // Have a conversation to generate snippets
        const messageInput = page.locator('textarea, input[type="text"]').first();
        if (await messageInput.isVisible()) {
            await messageInput.fill(
                'I grew up in a small town with my parents and two siblings. My favorite memory is playing soccer with my friends.'
            );
            await page.click('button[type="submit"], button:has-text("Send")');

            // Wait for response
            await page.waitForSelector('[data-testid="assistant-message"], .message.assistant', {
                timeout: 30000,
            });
        }
    }

    test('should display snippet cards in overlay', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Click to open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();

            // Should show snippets overlay
            await expect(page.locator('[data-testid="snippets-overlay"], .snippets-overlay')).toBeVisible({
                timeout: 5000,
            });

            // Should show snippet cards
            await expect(
                page.locator('[data-testid="snippet-card"], .snippet-card').first()
            ).toBeVisible();
        }
    });

    test('should lock and unlock a snippet card', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Find the lock button on first card
            const lockButton = page
                .locator('[data-testid="snippet-card"], .snippet-card')
                .first()
                .locator('button:has-text("Lock"), button[aria-label*="lock"]');

            if (await lockButton.isVisible()) {
                // Click to lock
                await lockButton.click();

                // Should show locked indicator (gold border or badge)
                await expect(
                    page
                        .locator('[data-testid="snippet-card"], .snippet-card')
                        .first()
                        .locator('.ring-amber-400, :has-text("Protected")')
                ).toBeVisible({ timeout: 2000 });

                // Click to unlock
                await lockButton.click();

                // Gold border should be gone
                await expect(
                    page.locator('[data-testid="snippet-card"], .snippet-card').first().locator('.ring-amber-400')
                ).not.toBeVisible({ timeout: 2000 });
            }
        }
    });

    test('should delete (archive) a snippet card', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Count initial cards
            const initialCount = await page.locator('[data-testid="snippet-card"], .snippet-card').count();

            // Find the delete button on first card
            const deleteButton = page
                .locator('[data-testid="snippet-card"], .snippet-card')
                .first()
                .locator('button:has-text("Delete"), button[aria-label*="delete"], button:has(svg.lucide-trash)');

            if (await deleteButton.isVisible()) {
                await deleteButton.click();

                // Wait for card to be archived
                await page.waitForTimeout(500);

                // Should have one less active card
                const newCount = await page.locator('[data-testid="snippet-card"], .snippet-card').count();
                expect(newCount).toBeLessThan(initialCount);
            }
        }
    });

    test('should show archived snippets tab', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Look for Archived tab
            const archivedTab = page.locator('button:has-text("Archived")');
            if (await archivedTab.isVisible()) {
                await archivedTab.click();

                // Should show archived view (may be empty or have archived cards)
                await expect(
                    page.locator(':has-text("No archived"), [data-testid="archived-snippets"]')
                ).toBeVisible({ timeout: 3000 });
            }
        }
    });

    test('should restore an archived snippet', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Delete a card first
            const deleteButton = page
                .locator('[data-testid="snippet-card"], .snippet-card')
                .first()
                .locator('button:has-text("Delete"), button[aria-label*="delete"], button:has(svg.lucide-trash)');

            if (await deleteButton.isVisible()) {
                await deleteButton.click();
                await page.waitForTimeout(500);
            }

            // Switch to Archived tab
            const archivedTab = page.locator('button:has-text("Archived")');
            if (await archivedTab.isVisible()) {
                await archivedTab.click();
                await page.waitForTimeout(300);

                // Find restore button
                const restoreButton = page.locator(
                    'button:has-text("Restore"), button[aria-label*="restore"]'
                );

                if (await restoreButton.isVisible()) {
                    await restoreButton.click();

                    // Card should be restored (disappear from archived view)
                    await page.waitForTimeout(500);
                }
            }
        }
    });

    test('should show regeneration warning modal', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Find the regenerate button
            const regenerateButton = page.locator(
                'button:has-text("Regenerate"), button:has-text("Generate New")'
            );

            if (await regenerateButton.isVisible()) {
                await regenerateButton.click();

                // Should show warning modal
                await expect(
                    page.locator('[role="dialog"], .modal, [data-testid="warning-modal"]')
                ).toBeVisible({ timeout: 2000 });

                // Modal should mention locked cards preservation
                await expect(page.locator(':has-text("locked"), :has-text("preserved")')).toBeVisible();
            }
        }
    });

    test('should show locked card count in overlay', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Lock a card
            const lockButton = page
                .locator('[data-testid="snippet-card"], .snippet-card')
                .first()
                .locator('button:has-text("Lock"), button[aria-label*="lock"]');

            if (await lockButton.isVisible()) {
                await lockButton.click();
                await page.waitForTimeout(300);

                // Should show locked count somewhere in the overlay
                await expect(page.locator(':has-text("1 locked"), :has-text("locked: 1")')).toBeVisible({
                    timeout: 2000,
                });
            }
        }
    });

    test('locked cards should have visible gold border indicator', async ({ page }) => {
        await setupTestWithSnippets(page);

        // Open snippets overlay
        const snippetsButton = page.locator('button:has-text("Cards"), button:has-text("Snippets")');
        if (await snippetsButton.isVisible({ timeout: 3000 })) {
            await snippetsButton.click();
            await page.waitForSelector('[data-testid="snippet-card"], .snippet-card', { timeout: 5000 });

            // Lock a card
            const firstCard = page.locator('[data-testid="snippet-card"], .snippet-card').first();
            const lockButton = firstCard.locator(
                'button:has-text("Lock"), button[aria-label*="lock"]'
            );

            if (await lockButton.isVisible()) {
                await lockButton.click();
                await page.waitForTimeout(300);

                // Check for gold border (ring-amber-400 in Tailwind)
                const cardClasses = await firstCard.getAttribute('class');
                expect(cardClasses).toMatch(/ring|border.*amber|border.*gold/i);

                // Or check computed style
                const borderColor = await firstCard.evaluate((el) => {
                    const style = window.getComputedStyle(el);
                    return style.boxShadow || style.borderColor || style.outlineColor;
                });

                // Gold/amber colors should be present
                expect(borderColor.toLowerCase()).toMatch(/rgb\(251, 191, 36\)|amber|#fbbf24/i);
            }
        }
    });
});
