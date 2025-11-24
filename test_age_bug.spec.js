// Test to reproduce age selection bug using Playwright
// This will test the actual frontend/backend interaction

const { test, expect } = require('@playwright/test');

test('Age selection bug - AI outputs AGE_SELECTION prompt after age selected', async ({ page }) => {
    // Start dev server should already be running
    await page.goto('http://localhost:5174');

    // Wait for initial greeting
    await expect(page.locator('text=Welcome! I\'m here to help you tell your life story')).toBeVisible();

    // Step 1: Click "yes" to start
    await page.locator('input[type="text"]').fill('yes');
    await page.locator('button[type="submit"]').click();

    // Step 2: Wait for age selection UI to appear
    await expect(page.locator('text=Select Your Age Range:')).toBeVisible({ timeout: 10000 });

    // Step 3: Click age button (18-30)
    await page.locator('button:has-text("18-30")').click();

    // Step 4: Wait for response (should be CHILDHOOD prompt, NOT AGE_SELECTION)
    await page.waitForTimeout(3000); // Give AI time to respond

    // Step 5: Check what AI said
    const messages = await page.locator('.bg-gray-700').allTextContents();
    console.log('=== ALL AI MESSAGES ===');
    messages.forEach((msg, idx) => console.log(`Message ${idx}:`, msg));

    // Step 6: Type first message
    await page.locator('input[type="text"]').fill('I remember playing in the backyard');
    await page.locator('button[type="submit"]').click();

    // Step 7: Wait for AI response
    await page.waitForTimeout(5000);

    // Step 8: Get all messages again
    const allMessages = await page.locator('.bg-gray-700').allTextContents();
    console.log('=== MESSAGES AFTER FIRST USER INPUT ===');
    allMessages.forEach((msg, idx) => console.log(`Message ${idx}:`, msg));

    // Check if AGE_SELECTION prompt appears
    const hasAgeSelectionPrompt = allMessages.some(msg =>
        msg.includes('To customize the interview to your life stage') ||
        msg.includes('Please select your age range by typing the number (1-5)')
    );

    if (hasAgeSelectionPrompt) {
        console.error('❌ BUG CONFIRMED: AGE_SELECTION prompt appeared after age button clicked');
    } else {
        console.log('✅ No AGE_SELECTION prompt found');
    }

    // Take screenshot for evidence
    await page.screenshot({ path: 'age_bug_evidence.png', fullPage: true });
});
