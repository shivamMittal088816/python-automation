import { test, expect } from './fixtures/browser-audit';

test('rollback file clears from its workspace after confirmation', async ({ page }) => {
  const uploadedName = page.locator('.bulk-loaded-file-copy strong');
  const sanityPanel = page.getByRole('region', { name: 'Input sanity check', exact: true });
  await page.goto('/rollback');
  await expect(page.getByRole('button', { name: 'Upload rollback file' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Sanity check', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Analyze rollback changes' })).toBeDisabled();

  await page.getByRole('textbox', { name: 'School number' }).fill('914');
  await page.getByRole('button', { name: 'Verify school' }).click();
  await expect(page.getByRole('textbox', { name: 'School name' })).toHaveValue('Test School');
  await expect(page.getByRole('region', { name: 'Rollback database dump records' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download Excel' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Download CSV' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Sanity check', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Analyze rollback changes' })).toBeDisabled();

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
    buffer: Buffer.from('USER_ID,FIRST NAME,unexpected\n1,Ada,value\n2,Grace,value\n'),
  });
  await expect(uploadedName).toHaveText('rollback-clear-qa.csv');
  await expect(page.getByRole('region', { name: 'Rollback input records' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sanity check', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Analyze rollback changes' })).toBeEnabled();

  await page.getByRole('button', { name: 'Sanity check', exact: true }).click();
  await expect(sanityPanel.getByRole('status')).toHaveAccessibleName('2 records checked · 2 with issues · 0 passed');
  await expect(sanityPanel.locator('.bulk-sanity-icon.is-failed')).toHaveCount(3);
  await expect(sanityPanel.locator('tbody tr')).toHaveCount(2);
  await expect(sanityPanel.getByText('user_id is required for rollback activity because it is the unique identifier', { exact: true })).toHaveCount(2);

  await page.getByRole('button', { name: 'Analyze rollback changes' }).click();
  await expect(page.getByRole('alert')).toContainText('user_id is required for rollback activity because it is the unique identifier.');
  await expect(page.locator('[aria-labelledby="rollback-action-title"]').getByRole('status')).toHaveCount(0);

  await page.getByRole('button', { name: 'Replace rollback file' }).setInputFiles({
    name: 'rollback-clear-qa.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('user_id,FIRST NAME\n1,Ada\n2,Grace\n'),
  });
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.getByRole('button', { name: 'Sanity check', exact: true }).click();
  await expect(sanityPanel.getByRole('status')).toHaveAccessibleName('2 records checked · 0 with issues · 2 passed');
  await expect(sanityPanel.getByText('All students passed')).toBeVisible();

  const crossTabReplacement = await page.request.post(
    'http://127.0.0.1:8123/api/v1/bulk-reg/rollback/files',
    { multipart: { file: {
      name: 'cross-tab-invalid.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('USER_ID,unexpected\n1,value\n'),
    } } },
  );
  expect(crossTabReplacement.ok()).toBe(true);
  await page.getByRole('button', { name: 'Analyze rollback changes' }).click();
  await expect(page.getByRole('alert')).toContainText('user_id is required for rollback activity because it is the unique identifier.');
  await expect(sanityPanel.getByRole('status')).toHaveAccessibleName('1 records checked · 1 with issues · 0 passed');

  await page.getByRole('button', { name: 'Replace rollback file' }).setInputFiles({
    name: 'rollback-clear-qa.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('user_id,FIRST NAME\n1,Ada\n2,Grace\n'),
  });
  await page.getByRole('button', { name: 'Sanity check', exact: true }).click();
  await page.getByRole('button', { name: 'Analyze rollback changes' }).click();
  const analysis = page.locator('.rollback-analysis');
  await expect(analysis).toContainText('5');
  await expect(analysis).toContainText('Will be updated');
  await expect(analysis).toContainText('2');
  await expect(analysis).toContainText('Protected by sheet');

  await page.getByRole('button', { name: 'Commit 5 changes' }).click();
  const commitDialog = page.getByRole('dialog', { name: 'Commit rollback changes?' });
  await expect(commitDialog).toContainText(/5\s*users will be updated/);
  await expect(commitDialog).toContainText(/2\s*sheet IDs remain unchanged/);
  await commitDialog.getByRole('button', { name: 'Cancel' }).click();
  await expect(analysis).toBeVisible();

  await page.getByRole('button', { name: 'Commit 5 changes' }).click();
  await commitDialog.getByRole('button', { name: 'Yes, commit changes' }).click();
  await expect(page.locator('.rollback-action-notice')).toHaveText(
    'Rollback completed: 2 uploaded user IDs were excluded and 5 non-supplied package-14 users changed.',
  );

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
  await expect(page.getByRole('button', { name: 'Sanity check', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Analyze rollback changes' })).toBeDisabled();
  await expect(page.locator('.rollback-action').getByRole('status')).toHaveCount(0);

  const workspace = await page.request.get('http://127.0.0.1:8123/api/v1/bulk-reg/rollback/workspace');
  expect(workspace.ok()).toBe(true);
  expect((await workspace.json()).file).toBeNull();

  await page.reload();
  await expect(page.getByRole('button', { name: 'Upload rollback file' })).toBeEnabled();
  await expect(page.getByRole('textbox', { name: 'School name' })).toHaveValue('Test School');
  await expect(page.getByRole('region', { name: 'Rollback input records' })).toHaveCount(0);
});
