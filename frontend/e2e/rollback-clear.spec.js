import { test, expect } from './fixtures/browser-audit';

test('rollback file clears from its workspace after confirmation', async ({ page }) => {
  const uploadedName = page.locator('.bulk-loaded-file-copy strong');
  await page.goto('/rollback');
  await expect(page.getByRole('button', { name: 'Upload rollback file' })).toBeEnabled();

  await page.getByRole('textbox', { name: 'School number' }).fill('914');
  await page.getByRole('button', { name: 'Verify school' }).click();
  await expect(page.getByRole('textbox', { name: 'School name' })).toHaveValue('Test School');
  await expect(page.getByRole('region', { name: 'Rollback database dump records' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download Excel' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Download CSV' })).toBeEnabled();

  await page.setViewportSize({ width: 390, height: 844 });
  const schoolInput = page.getByRole('textbox', { name: 'School number' });
  const verifyButton = page.getByRole('button', { name: 'Verify school' });
  await expect.poll(async () => {
    const inputBox = await schoolInput.boundingBox();
    const buttonBox = await verifyButton.boundingBox();
    return inputBox && buttonBox ? buttonBox.y - (inputBox.y + inputBox.height) : Infinity;
  }).toBeLessThanOrEqual(16);

  await page.getByRole('button', { name: 'Upload rollback file' }).setInputFiles({
    name: 'rollback-clear-qa.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('id,name\n1,Ada\n2,Grace\n'),
  });
  await expect(uploadedName).toHaveText('rollback-clear-qa.csv');
  await expect(page.getByRole('region', { name: 'Rollback input records' })).toBeVisible();

  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.getByRole('dialog', { name: 'Clear this file?' })
    .getByRole('button', { name: 'Cancel' }).click();
  await expect(uploadedName).toHaveText('rollback-clear-qa.csv');

  await page.getByRole('button', { name: 'Clear file' }).click();
  await page.getByRole('dialog', { name: 'Clear this file?' })
    .getByRole('button', { name: 'Confirm' }).click();
  await expect(page.getByRole('button', { name: 'Upload rollback file' })).toBeEnabled();
  await expect(uploadedName).toHaveCount(0);
  await expect(page.getByRole('region', { name: 'Rollback input records' })).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'School name' })).toHaveValue('Test School');

  const workspace = await page.request.get('http://127.0.0.1:8123/api/v1/bulk-reg/rollback/workspace');
  expect(workspace.ok()).toBe(true);
  expect((await workspace.json()).file).toBeNull();

  await page.reload();
  await expect(page.getByRole('button', { name: 'Upload rollback file' })).toBeEnabled();
  await expect(page.getByRole('textbox', { name: 'School name' })).toHaveValue('Test School');
  await expect(page.getByRole('region', { name: 'Rollback input records' })).toHaveCount(0);
});
