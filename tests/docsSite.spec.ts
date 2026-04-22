import { test, expect } from 'playwright/test';

test('has title', async ({ page }) => {
  await page.goto('https://mtg-app-docs.pages.dev');

  await expect(page).toHaveTitle('MTG App Dev Notes');
});
