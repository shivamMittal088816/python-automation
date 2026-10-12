import { test, expect } from './fixtures/browser-audit';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const python = fileURLToPath(new URL('../../backend/.venv/Scripts/python.exe', import.meta.url));
const dump = fileURLToPath(new URL('./fixtures/dump.csv', import.meta.url));
function workbook(name, sheets) {
  const buffer = execFileSync(python, ['-c', `
import io, json, sys
from openpyxl import Workbook
book = Workbook()
book.remove(book.active)
for name, rows in json.loads(sys.stdin.read()):
    sheet = book.create_sheet(name)
    for row in rows:
        sheet.append(row)
output = io.BytesIO()
book.save(output)
sys.stdout.buffer.write(output.getvalue())
`], { input: JSON.stringify(sheets) });
  return { name, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer };
}

test('school viewer resets sheet-dependent columns and keeps statistics usable', async ({ page }) => {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(workbook('classes.xlsx', [
    ['Original', [['name', 'class', 'section'], ['Ada', '1', 'A']]],
    ['Other', [['student', 'grade', 'group'], ['Grace', '2', 'B']]],
  ]));
  await expect(page.getByTestId('school-input').locator('span').filter({ hasText: /^classes\.xlsx$/ })).toBeVisible();
  await page.goto('/school_file_page');
  await page.getByLabel('Class column', { exact: true }).selectOption('class');
  await page.getByLabel('Section column', { exact: true }).selectOption('section');
  await page.locator('label').filter({ hasText: /^Selected columns$/ }).click();
  await page.locator('summary').filter({ hasText: 'Columns to search' }).click();
  await page.getByRole('checkbox', { name: 'name', exact: true }).check();
  await page.getByLabel('Search selected columns', { exact: true }).fill('Ada');
  await page.getByLabel('Choose worksheet').selectOption('Other');
  await expect(page.getByLabel('Class column', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('Section column', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('Search selected columns', { exact: true })).toBeDisabled();
  await expect(page.getByRole('cell', { name: 'Grace', exact: true })).toBeVisible();
  await page.getByLabel('Class column', { exact: true }).selectOption('grade');
  await page.getByLabel('Section column', { exact: true }).selectOption('group');
  await expect(page.getByText('Class and section values are displayed exactly as provided in the school file.')).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Choose worksheet')).toHaveValue('Other');
  await expect(page.getByLabel('Class column', { exact: true })).toHaveValue('grade');
  await expect(page.getByRole('cell', { name: 'Grace', exact: true })).toBeVisible();
});

test('mapping can recover from an empty first worksheet and subsequent invalid selections', async ({ page }) => {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add school file').setInputFiles(workbook('students.xlsx', [
    ['Empty', []], ['Students', [['admission_number', 'first_name'], ['001', 'Alice']]],
  ]));
  await expect(page.getByTestId('school-input').locator('span').filter({ hasText: /^students\.xlsx$/ })).toBeVisible();
  await page.getByLabel('School sheet', { exact: true }).selectOption('Students');
  await expect(page.getByLabel('School sheet', { exact: true })).toHaveValue('Students');
  await page.getByLabel('Add dump file').setInputFiles(dump);
  await expect(page.getByLabel('School sheet', { exact: true })).toHaveValue('Students');
  await expect(page.getByLabel('School admission number column', { exact: true })).toHaveValue('admission_number');
  await page.getByLabel('School index', { exact: true }).fill('914');
  await page.getByRole('button', { name: 'Save school index', exact: true }).click();
  await expect(page.getByText('Saved school index: 914', { exact: true })).toBeVisible();
  await page.getByLabel('School sheet', { exact: true }).selectOption('Students');
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  await expect(page.getByText('Both files must contain column headers.', { exact: true })).toHaveCount(0);
  await page.getByLabel('School sheet', { exact: true }).selectOption('Empty');
  await expect(page.getByText(/Both files must contain column headers/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toHaveCount(0);
  await page.getByLabel('School sheet', { exact: true }).selectOption('Students');
  await expect(page.getByRole('button', { name: 'Run mapping', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Run mapping', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Preview matched', exact: true })).toBeVisible();
});

test('CSV download uses the replacement workbook sheet without reloading', async ({ page }) => {
  await page.goto('/admission_file_page');
  await page.getByLabel('Add dump file').setInputFiles(workbook('old.xlsx', [
    ['Old', [['user_name'], ['Ada']]],
  ]));
  await expect(page.getByTestId('dump-input').locator('span').filter({ hasText: /^old\.xlsx$/ })).toBeVisible();
  await page.getByLabel('Replace dump file').setInputFiles(workbook('new.xlsx', [
    ['New', [['user_name'], ['Grace']]],
  ]));
  await expect(page.getByTestId('dump-input').locator('span').filter({ hasText: /^new\.xlsx$/ })).toBeVisible();
  await page.locator('summary').filter({ hasText: /^Download dump$/ }).click();
  const pending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download dump file', exact: true }).click();
  const download = await pending;
  expect(await download.failure()).toBeNull();
  const csv = await readFile(await download.path(), 'utf8');
  expect(csv).toContain('Grace');
  expect(csv).not.toContain('Ada');
});


test('bulk school file tab switches input rows before school verification', async ({ page }) => {
  await page.goto('/bulk-reg');
  await page.getByLabel('Upload registration file').setInputFiles(workbook('school-tabs.xlsx', [
    ['First', [['FIRST NAME'], ['Ada']]],
    ['Second', [['FIRST NAME'], ['Grace'], ['Alice']]],
  ]));
  await expect(page.getByLabel('School file tab')).toHaveValue('First');
  await page.getByLabel('School file tab').selectOption('Second');
  await expect(page.getByLabel('School file tab')).toHaveValue('Second');
  await expect(page.getByRole('region', { name: 'Load registration file' }).getByRole('status')).toContainText('2 rows');
  await page.reload();
  await expect(page.getByLabel('School file tab')).toHaveValue('Second');
});
