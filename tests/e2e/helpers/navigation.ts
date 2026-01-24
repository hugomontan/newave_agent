import { Page, expect } from '@playwright/test';

/**
 * Aguarda o carregamento completo da página
 * Verifica se o Next.js terminou de carregar
 */
export async function waitForPageLoad(page: Page): Promise<void> {
  // Aguardar até que o Next.js tenha terminado de carregar
  await page.waitForLoadState('networkidle');
  // Aguardar um pouco mais para garantir que animações terminaram
  await page.waitForTimeout(500);
}

/**
 * Verifica o título da página (h1 ou título no header)
 */
export async function checkPageTitle(page: Page, expectedTitle: string): Promise<void> {
  // Verificar se o título aparece no h1 ou no header
  const titleElement = page.locator('h1').or(page.locator('header')).filter({ hasText: expectedTitle });
  await expect(titleElement).toBeVisible();
}

/**
 * Navega para uma rota e verifica que a navegação foi bem-sucedida
 */
export async function navigateToRoute(page: Page, route: string): Promise<void> {
  await page.goto(route);
  await waitForPageLoad(page);
  // Verificar que não há erros 404 ou 500
  const response = await page.goto(route, { waitUntil: 'networkidle' });
  expect(response?.status()).toBeLessThan(400);
}

/**
 * Verifica que uma rota retorna 404
 */
export async function expect404(page: Page, route: string): Promise<void> {
  const response = await page.goto(route, { waitUntil: 'networkidle' });
  expect(response?.status()).toBe(404);
}

/**
 * Clica em um botão e aguarda navegação
 */
export async function clickAndNavigate(
  page: Page,
  buttonText: string | RegExp,
  expectedRoute: string
): Promise<void> {
  const button = page.getByRole('button', { name: buttonText });
  await button.click();
  await page.waitForURL(`**${expectedRoute}`, { timeout: 5000 });
  await waitForPageLoad(page);
}
