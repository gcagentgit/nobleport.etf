module.exports = {
  project: {
    name: 'nobleport-etf',
    root: '..',
    framework: 'nextjs',
  },
  build: {
    command: 'npm run build',
    outputDir: '.next',
    nodeVersion: '18',
  },
  deploy: {
    platform: 'vercel',
    region: 'iad1',
    environments: {
      preview: {
        branch: 'preview',
        domain: null,
      },
      production: {
        branch: 'main',
        domain: null,
      },
    },
  },
  checks: {
    lint: true,
    typeCheck: true,
    smokeTests: true,
    healthEndpoint: '/api/health',
  },
  notifications: {
    onSuccess: true,
    onFailure: true,
  },
};
