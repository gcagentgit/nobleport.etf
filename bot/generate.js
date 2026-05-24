#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  red: '\x1b[31m',
};

const TEMPLATES = {
  landing: {
    pages: ['index.html'],
    assets: ['styles.css', 'script.js'],
    description: 'Single-page landing site',
  },
  portfolio: {
    pages: ['index.html', 'projects.html', 'about.html', 'contact.html'],
    assets: ['styles.css', 'script.js'],
    description: 'Multi-page portfolio site',
  },
  blog: {
    pages: ['index.html', 'posts.html', 'post.html', 'about.html'],
    assets: ['styles.css', 'script.js', 'blog.css'],
    description: 'Blog with posts listing',
  },
  saas: {
    pages: ['index.html', 'features.html', 'pricing.html', 'login.html'],
    assets: ['styles.css', 'app.js', 'auth.js'],
    description: 'SaaS product landing page',
  },
};

function generateCSS(siteName, template) {
  return `/* ${siteName} - Generated Styles */
:root {
  --primary: #667eea;
  --primary-dark: #5a67d8;
  --secondary: #764ba2;
  --text: #2d3748;
  --text-light: #718096;
  --bg: #f7fafc;
  --white: #ffffff;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --radius: 8px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Navigation */
.nav {
  background: var(--white);
  box-shadow: var(--shadow);
  padding: 16px 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 24px;
  list-style: none;
}

.nav-links a {
  color: var(--text);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-links a:hover { color: var(--primary); }

/* Hero */
.hero {
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: white;
  padding: 100px 0;
  text-align: center;
}

.hero h1 {
  font-size: 3rem;
  margin-bottom: 16px;
  font-weight: 800;
}

.hero p {
  font-size: 1.25rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto 32px;
}

.btn {
  display: inline-block;
  padding: 12px 32px;
  border-radius: var(--radius);
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  border: none;
  font-size: 1rem;
}

.btn:hover { transform: translateY(-2px); box-shadow: var(--shadow); }

.btn-primary {
  background: var(--white);
  color: var(--primary);
}

.btn-secondary {
  background: transparent;
  color: var(--white);
  border: 2px solid var(--white);
  margin-left: 12px;
}

/* Sections */
.section { padding: 80px 0; }

.section-title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 48px;
  color: var(--text);
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
  transition: transform 0.2s;
}

.card:hover { transform: translateY(-4px); }

.card h3 {
  color: var(--primary);
  margin-bottom: 12px;
  font-size: 1.25rem;
}

.card p { color: var(--text-light); }

/* Footer */
.footer {
  background: var(--text);
  color: var(--white);
  padding: 48px 0;
  text-align: center;
}

.footer p { opacity: 0.7; }

/* Responsive */
@media (max-width: 768px) {
  .hero h1 { font-size: 2rem; }
  .hero { padding: 60px 0; }
  .nav-links { display: none; }
  .grid { grid-template-columns: 1fr; }
}
`;
}

function generateJS(siteName, template) {
  return `// ${siteName} - Generated Script
document.addEventListener('DOMContentLoaded', () => {
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Intersection Observer for scroll animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card, .section').forEach(el => {
    observer.observe(el);
  });

  // Mobile nav toggle
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  console.log('${siteName} loaded successfully');
});
`;
}

function generateHTML(siteName, description, template) {
  const pages = {
    landing: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${siteName}</title>
  <meta name="description" content="${description}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <nav class="nav">
    <div class="container">
      <a href="/" class="nav-brand">${siteName}</a>
      <ul class="nav-links">
        <li><a href="#features">Features</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </div>
  </nav>

  <section class="hero">
    <div class="container">
      <h1>${siteName}</h1>
      <p>${description}</p>
      <a href="#features" class="btn btn-primary">Get Started</a>
      <a href="#about" class="btn btn-secondary">Learn More</a>
    </div>
  </section>

  <section id="features" class="section">
    <div class="container">
      <h2 class="section-title">Features</h2>
      <div class="grid">
        <div class="card">
          <h3>Fast & Reliable</h3>
          <p>Built with performance in mind. Lightning-fast load times and 99.9% uptime guarantee.</p>
        </div>
        <div class="card">
          <h3>Secure by Default</h3>
          <p>Enterprise-grade security with SSL, DDoS protection, and automatic backups.</p>
        </div>
        <div class="card">
          <h3>Easy to Manage</h3>
          <p>Intuitive dashboard for managing your content, analytics, and deployments.</p>
        </div>
      </div>
    </div>
  </section>

  <section id="about" class="section" style="background: white;">
    <div class="container">
      <h2 class="section-title">About</h2>
      <p style="text-align:center; max-width:700px; margin:0 auto; color:#718096; font-size:1.1rem;">
        ${siteName} is designed to help you build and deploy beautiful websites with ease.
        Our platform combines powerful tools with simple workflows.
      </p>
    </div>
  </section>

  <footer class="footer">
    <div class="container">
      <p>&copy; ${new Date().getFullYear()} ${siteName}. All rights reserved.</p>
    </div>
  </footer>

  <script src="script.js"></script>
</body>
</html>`,
  };

  return pages[template] || pages.landing;
}

function generateSite(options) {
  const { name, description, template, outputDir } = options;

  console.log(`\n${COLORS.bold}${COLORS.blue}Generating website: ${name}${COLORS.reset}`);
  console.log(`${COLORS.dim}Template: ${template} | Output: ${outputDir}${COLORS.reset}\n`);

  const targetDir = path.resolve(outputDir);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  // Generate HTML
  const html = generateHTML(name, description, template);
  fs.writeFileSync(path.join(targetDir, 'index.html'), html);
  console.log(`  ${COLORS.green}✓${COLORS.reset} Created index.html`);

  // Generate CSS
  const css = generateCSS(name, template);
  fs.writeFileSync(path.join(targetDir, 'styles.css'), css);
  console.log(`  ${COLORS.green}✓${COLORS.reset} Created styles.css`);

  // Generate JS
  const js = generateJS(name, template);
  fs.writeFileSync(path.join(targetDir, 'script.js'), js);
  console.log(`  ${COLORS.green}✓${COLORS.reset} Created script.js`);

  // Generate package.json for the site
  const pkg = {
    name: name.toLowerCase().replace(/\s+/g, '-'),
    version: '1.0.0',
    description,
    scripts: {
      dev: 'npx serve .',
      build: 'echo "Static site - no build needed"',
    },
  };
  fs.writeFileSync(path.join(targetDir, 'package.json'), JSON.stringify(pkg, null, 2));
  console.log(`  ${COLORS.green}✓${COLORS.reset} Created package.json`);

  console.log(`\n${COLORS.green}${COLORS.bold}Website generated successfully!${COLORS.reset}`);
  console.log(`${COLORS.dim}Run 'npx serve ${outputDir}' to preview locally${COLORS.reset}\n`);

  return targetDir;
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    console.log(`
${COLORS.bold}Nobleport Website Generator${COLORS.reset}

${COLORS.dim}Usage:${COLORS.reset}
  node generate.js <name> [options]

${COLORS.dim}Options:${COLORS.reset}
  --template <type>    Template: landing, portfolio, blog, saas (default: landing)
  --description <text> Site description
  --output <dir>       Output directory (default: ./generated-site)
  --help               Show this help

${COLORS.dim}Examples:${COLORS.reset}
  node generate.js "My Portfolio" --template portfolio --output ./my-site
  node generate.js "Startup Landing" --template saas
`);
    process.exit(0);
  }

  const name = args[0];
  const templateIdx = args.indexOf('--template');
  const descIdx = args.indexOf('--description');
  const outIdx = args.indexOf('--output');

  const template = templateIdx !== -1 ? args[templateIdx + 1] : 'landing';
  const description = descIdx !== -1 ? args[descIdx + 1] : `Welcome to ${name}`;
  const outputDir = outIdx !== -1 ? args[outIdx + 1] : './generated-site';

  generateSite({ name, description, template, outputDir });
}

module.exports = { generateSite, generateHTML, generateCSS, generateJS, TEMPLATES };
