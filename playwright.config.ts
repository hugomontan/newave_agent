import { defineConfig, devices } from '@playwright/test';

/**
 * Configuração do Playwright para testes E2E
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  /* Executar testes em arquivos com extensão .spec.ts ou .e2e.ts */
  testMatch: /.*\.(spec|e2e)\.(ts|tsx)$/,
  
  /* Timeout para cada teste */
  timeout: 30 * 1000,
  
  /* Expect timeout */
  expect: {
    timeout: 5000
  },
  
  /* Executar testes em paralelo */
  fullyParallel: true,
  
  /* Falhar o build se houver testes com falha */
  forbidOnly: !!process.env.CI,
  
  /* Retry em CI */
  retries: process.env.CI ? 2 : 0,
  
  /* Workers em CI */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter */
  reporter: 'html',
  
  /* Compartilhar configuração entre projetos */
  use: {
    /* Base URL para usar em navegação como `await page.goto('/')` */
    baseURL: 'http://localhost:3001',
    
    /* Coletar trace quando retentar o teste falho */
    trace: 'on-first-retry',
    
    /* Screenshot apenas quando falhar */
    screenshot: 'only-on-failure',
  },

  /* Configurar projetos para diferentes browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  /* Executar servidor de desenvolvimento antes dos testes */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
