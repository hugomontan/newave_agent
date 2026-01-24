import { test, expect } from '@playwright/test';
import {
  waitForPageLoad,
  checkPageTitle,
  navigateToRoute,
  expect404,
  clickAndNavigate,
} from './helpers/navigation';

test.describe('Navegação - Rotas Válidas', () => {
  test('Home (/) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/');
    
    // Verificar título
    await checkPageTitle(page, 'NW Multi Agent');
    
    // Verificar presença de botões principais
    await expect(page.getByRole('button', { name: /Acessar NEWAVE/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Acessar DECOMP/i })).toBeVisible();
  });

  test('Menu NEWAVE (/newave) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/newave');
    
    // Verificar título
    await checkPageTitle(page, 'NEWAVE Agent');
    
    // Verificar presença de botões
    await expect(page.getByRole('button', { name: /Acessar Análise Single Deck/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Acessar Análise Comparativa/i })).toBeVisible();
    
    // Verificar botão voltar
    await expect(page.getByRole('button', { name: /Voltar/i })).toBeVisible();
  });

  test('Análise NEWAVE (/newave/analysis) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/newave/analysis');
    
    // Verificar que a página carregou (pode ter diferentes elementos dependendo do estado)
    await waitForPageLoad(page);
    
    // Verificar que não há erro 404
    await expect(page.locator('body')).not.toContainText('404');
  });

  test('Comparação NEWAVE (/newave/comparison) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/newave/comparison');
    
    // Verificar que a página carregou
    await waitForPageLoad(page);
    
    // Verificar que não há erro 404
    await expect(page.locator('body')).not.toContainText('404');
  });

  test('Menu DECOMP (/decomp) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/decomp');
    
    // Verificar título
    await checkPageTitle(page, 'DECOMP Agent');
    
    // Verificar presença de botões
    await expect(page.getByRole('button', { name: /Acessar Análise Single Deck/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Acessar Análise Comparativa/i })).toBeVisible();
    
    // Verificar botão voltar
    await expect(page.getByRole('button', { name: /Voltar/i })).toBeVisible();
  });

  test('Análise DECOMP (/decomp/analysis) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/decomp/analysis');
    
    // Verificar que a página carregou
    await waitForPageLoad(page);
    
    // Verificar que não há erro 404
    await expect(page.locator('body')).not.toContainText('404');
  });

  test('Comparação DECOMP (/decomp/comparison) carrega corretamente', async ({ page }) => {
    await navigateToRoute(page, '/decomp/comparison');
    
    // Verificar que a página carregou
    await waitForPageLoad(page);
    
    // Verificar que não há erro 404
    await expect(page.locator('body')).not.toContainText('404');
  });
});

test.describe('Navegação - Rotas Órfãs (404)', () => {
  test('/analysis retorna 404', async ({ page }) => {
    await expect404(page, '/analysis');
  });

  test('/comparison retorna 404', async ({ page }) => {
    await expect404(page, '/comparison');
  });
});

test.describe('Navegação Interativa', () => {
  test('Home → NEWAVE → Analysis', async ({ page }) => {
    // Iniciar na home
    await navigateToRoute(page, '/');
    
    // Clicar em "Acessar NEWAVE"
    await clickAndNavigate(page, /Acessar NEWAVE/i, '/newave');
    
    // Verificar que estamos em /newave
    await expect(page).toHaveURL(/.*\/newave$/);
    
    // Clicar em "Acessar Análise Single Deck"
    await clickAndNavigate(page, /Acessar Análise Single Deck/i, '/newave/analysis');
    
    // Verificar que estamos em /newave/analysis
    await expect(page).toHaveURL(/.*\/newave\/analysis/);
  });

  test('Home → NEWAVE → Comparison', async ({ page }) => {
    // Iniciar na home
    await navigateToRoute(page, '/');
    
    // Clicar em "Acessar NEWAVE"
    await clickAndNavigate(page, /Acessar NEWAVE/i, '/newave');
    
    // Clicar em "Acessar Análise Comparativa"
    await clickAndNavigate(page, /Acessar Análise Comparativa/i, '/newave/comparison');
    
    // Verificar que estamos em /newave/comparison
    await expect(page).toHaveURL(/.*\/newave\/comparison/);
  });

  test('Home → DECOMP → Analysis', async ({ page }) => {
    // Iniciar na home
    await navigateToRoute(page, '/');
    
    // Clicar em "Acessar DECOMP"
    await clickAndNavigate(page, /Acessar DECOMP/i, '/decomp');
    
    // Verificar que estamos em /decomp
    await expect(page).toHaveURL(/.*\/decomp$/);
    
    // Clicar em "Acessar Análise Single Deck"
    await clickAndNavigate(page, /Acessar Análise Single Deck/i, '/decomp/analysis');
    
    // Verificar que estamos em /decomp/analysis
    await expect(page).toHaveURL(/.*\/decomp\/analysis/);
  });

  test('Home → DECOMP → Comparison', async ({ page }) => {
    // Iniciar na home
    await navigateToRoute(page, '/');
    
    // Clicar em "Acessar DECOMP"
    await clickAndNavigate(page, /Acessar DECOMP/i, '/decomp');
    
    // Clicar em "Acessar Análise Comparativa"
    await clickAndNavigate(page, /Acessar Análise Comparativa/i, '/decomp/comparison');
    
    // Verificar que estamos em /decomp/comparison
    await expect(page).toHaveURL(/.*\/decomp\/comparison/);
  });

  test('Botão "Voltar" em /newave navega para /', async ({ page }) => {
    await navigateToRoute(page, '/newave');
    
    // Clicar no botão voltar
    const backButton = page.getByRole('button', { name: /Voltar/i });
    await backButton.click();
    
    // Aguardar navegação
    await page.waitForURL('**/', { timeout: 5000 });
    await waitForPageLoad(page);
    
    // Verificar que estamos na home
    await expect(page).toHaveURL(/\/$/);
    await checkPageTitle(page, 'NW Multi Agent');
  });

  test('Botão "Voltar" em /decomp navega para /', async ({ page }) => {
    await navigateToRoute(page, '/decomp');
    
    // Clicar no botão voltar
    const backButton = page.getByRole('button', { name: /Voltar/i });
    await backButton.click();
    
    // Aguardar navegação
    await page.waitForURL('**/', { timeout: 5000 });
    await waitForPageLoad(page);
    
    // Verificar que estamos na home
    await expect(page).toHaveURL(/\/$/);
    await checkPageTitle(page, 'NW Multi Agent');
  });
});
