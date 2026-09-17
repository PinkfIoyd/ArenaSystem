import { expect, test } from '@playwright/test';

test('login and recovery entry points are responsive', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('button', { name: 'Entrar' })).toBeVisible();
  await page.getByRole('link', { name: 'Esqueci minha senha' }).click();
  await expect(page.getByRole('heading', { name: 'Recuperar senha' })).toBeVisible();
});

test('public pricing handles unpublished catalog', async ({ page }) => {
  await page.route('**/api/saas/plans/', async (route) => route.fulfill({ json: [] }));
  await page.goto('/precos');
  await expect(page.getByRole('heading', { name: 'Planos para operar sua arena' })).toBeVisible();
  await expect(page.getByText('Catalogo em preparacao')).toBeVisible();
});

