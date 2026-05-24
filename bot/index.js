#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { generateSite, TEMPLATES } = require('./generate');

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  red: '\x1b[31m',
};

function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function printBanner() {
  console.log(`
${COLORS.bold}${COLORS.cyan}
  ╔═══════════════════════════════════════════════════════╗
  ║                                                       ║
  ║   🤖  NOBLEPORT WEBSITE DEPLOYMENT BOT               ║
  ║                                                       ║
  ║   Generate • Build • Deploy • Monitor                 ║
  ║                                                       ║
  ╚═══════════════════════════════════════════════════════╝
${COLORS.reset}
  ${COLORS.dim}Commands:${COLORS.reset}
    ${COLORS.cyan}generate${COLORS.reset}  - Create a new website from template
    ${COLORS.cyan}deploy${COLORS.reset}    - Deploy current project to production
    ${COLORS.cyan}preview${COLORS.reset}   - Deploy to preview environment
    ${COLORS.cyan}status${COLORS.reset}    - Check deployment status
    ${COLORS.cyan}logs${COLORS.reset}      - View recent deployment logs
    ${COLORS.cyan}rollback${COLORS.reset}  - Rollback to previous deployment
    ${COLORS.cyan}help${COLORS.reset}      - Show this help menu
    ${COLORS.cyan}exit${COLORS.reset}      - Exit the bot
`);
}

async function handleGenerate() {
  console.log(`\n${COLORS.bold}Website Generator${COLORS.reset}\n`);
  console.log(`${COLORS.dim}Available templates:${COLORS.reset}`);
  Object.entries(TEMPLATES).forEach(([key, val]) => {
    console.log(`  ${COLORS.cyan}${key}${COLORS.reset} - ${val.description}`);
  });

  const name = await prompt(`\n  ${COLORS.yellow}Site name:${COLORS.reset} `);
  if (!name) {
    console.log(`  ${COLORS.red}Name is required${COLORS.reset}`);
    return;
  }

  const template = await prompt(`  ${COLORS.yellow}Template (landing/portfolio/blog/saas):${COLORS.reset} `) || 'landing';
  const description = await prompt(`  ${COLORS.yellow}Description:${COLORS.reset} `) || `Welcome to ${name}`;
  const outputDir = await prompt(`  ${COLORS.yellow}Output dir (./generated-site):${COLORS.reset} `) || './generated-site';

  generateSite({ name, description, template, outputDir });

  const shouldDeploy = await prompt(`\n  ${COLORS.yellow}Deploy now? (y/n):${COLORS.reset} `);
  if (shouldDeploy.toLowerCase() === 'y') {
    await handleDeploy(outputDir);
  }
}

async function handleDeploy(customDir) {
  console.log(`\n${COLORS.bold}Starting deployment pipeline...${COLORS.reset}\n`);

  const deployScript = path.join(__dirname, 'deploy.js');
  const args = customDir ? `--project-dir ${customDir}` : '';

  try {
    execSync(`node ${deployScript} --production ${args}`, {
      cwd: __dirname,
      stdio: 'inherit',
    });
  } catch (err) {
    console.log(`\n  ${COLORS.red}Deployment encountered issues. Check output above.${COLORS.reset}`);
  }
}

async function handlePreview() {
  console.log(`\n${COLORS.bold}Starting preview deployment...${COLORS.reset}\n`);

  const deployScript = path.join(__dirname, 'deploy.js');
  try {
    execSync(`node ${deployScript} --preview`, {
      cwd: __dirname,
      stdio: 'inherit',
    });
  } catch (err) {
    console.log(`\n  ${COLORS.red}Preview deployment failed.${COLORS.reset}`);
  }
}

function handleStatus() {
  console.log(`\n${COLORS.bold}Deployment Status${COLORS.reset}\n`);

  const projectRoot = path.resolve(__dirname, '..');
  const branch = execSync('git branch --show-current', { cwd: projectRoot, encoding: 'utf-8' }).trim();
  const lastCommit = execSync('git log -1 --oneline', { cwd: projectRoot, encoding: 'utf-8' }).trim();
  const remoteUrl = execSync('git remote get-url origin 2>/dev/null || echo "no remote"', { cwd: projectRoot, encoding: 'utf-8' }).trim();

  console.log(`  ${COLORS.dim}Branch:${COLORS.reset}      ${branch}`);
  console.log(`  ${COLORS.dim}Last commit:${COLORS.reset} ${lastCommit}`);
  console.log(`  ${COLORS.dim}Remote:${COLORS.reset}      ${remoteUrl}`);
  console.log(`  ${COLORS.dim}Status:${COLORS.reset}      ${COLORS.green}● Active${COLORS.reset}`);
  console.log('');
}

function handleLogs() {
  console.log(`\n${COLORS.bold}Recent Deployment Logs${COLORS.reset}\n`);

  const projectRoot = path.resolve(__dirname, '..');
  const logs = execSync('git log --oneline -10', { cwd: projectRoot, encoding: 'utf-8' }).trim();

  logs.split('\n').forEach((line, i) => {
    const color = i === 0 ? COLORS.green : COLORS.dim;
    console.log(`  ${color}${line}${COLORS.reset}`);
  });
  console.log('');
}

function handleRollback() {
  console.log(`\n${COLORS.bold}Rollback${COLORS.reset}\n`);
  console.log(`  ${COLORS.yellow}⚠ Rollback would revert to previous deployment.${COLORS.reset}`);
  console.log(`  ${COLORS.dim}In production, this switches the CDN pointer to the prior build artifact.${COLORS.reset}`);
  console.log(`  ${COLORS.dim}Use 'git revert HEAD' + deploy for a code-level rollback.${COLORS.reset}\n`);
}

async function main() {
  const args = process.argv.slice(2);

  // Non-interactive mode
  if (args.length > 0) {
    const command = args[0];
    switch (command) {
      case 'generate':
        await handleGenerate();
        break;
      case 'deploy':
        await handleDeploy();
        break;
      case 'preview':
        await handlePreview();
        break;
      case 'status':
        handleStatus();
        break;
      case 'logs':
        handleLogs();
        break;
      case 'rollback':
        handleRollback();
        break;
      default:
        printBanner();
    }
    return;
  }

  // Interactive mode
  printBanner();

  while (true) {
    const input = await prompt(`${COLORS.cyan}bot>${COLORS.reset} `);
    const command = input.toLowerCase();

    switch (command) {
      case 'generate':
      case 'gen':
      case 'new':
        await handleGenerate();
        break;
      case 'deploy':
      case 'd':
        await handleDeploy();
        break;
      case 'preview':
      case 'p':
        await handlePreview();
        break;
      case 'status':
      case 's':
        handleStatus();
        break;
      case 'logs':
      case 'l':
        handleLogs();
        break;
      case 'rollback':
      case 'rb':
        handleRollback();
        break;
      case 'help':
      case 'h':
      case '?':
        printBanner();
        break;
      case 'exit':
      case 'quit':
      case 'q':
        console.log(`\n  ${COLORS.dim}Goodbye! 👋${COLORS.reset}\n`);
        process.exit(0);
        break;
      case '':
        break;
      default:
        console.log(`  ${COLORS.dim}Unknown command: ${input}. Type 'help' for options.${COLORS.reset}`);
    }
  }
}

main().catch(console.error);
