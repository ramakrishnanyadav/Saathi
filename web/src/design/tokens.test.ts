import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('SAATH UI v5 Ujjwal — Light-Only Theme & Contrast Policy Guard', () => {
  it('should verify that no dark: Tailwind classes or data-theme selectors exist in src/', () => {
    const srcDir = path.resolve(__dirname, '..');
    const files = getFilesRecursive(srcDir);

    const forbiddenPatterns = [/data-theme/i, /\bdark:/i];
    const offendingFiles: string[] = [];

    for (const file of files) {
      if ((file.endsWith('.tsx') || file.endsWith('.ts') || file.endsWith('.css')) && !file.includes('.test.')) {
        const content = fs.readFileSync(file, 'utf-8');
        for (const pattern of forbiddenPatterns) {
          if (pattern.test(content)) {
            offendingFiles.push(`${path.relative(srcDir, file)} (matched ${pattern})`);
          }
        }
      }
    }

    expect(offendingFiles).toEqual([]);
  });

  it('should verify that tokens.css sets color-scheme: light', () => {
    const cssPath = path.resolve(__dirname, 'tokens.css');
    const content = fs.readFileSync(cssPath, 'utf-8');
    expect(content).toContain('color-scheme: light');
    expect(content).not.toContain('[data-theme=');
  });
});

function getFilesRecursive(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  list.forEach((file: string) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getFilesRecursive(filePath));
    } else {
      results.push(filePath);
    }
  });
  return results;
}
