import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import healthRouter from './routes/health';
import intakeRouter from './routes/intake';
import proposalsRouter from './routes/proposals';
import webhooksRouter from './routes/webhooks';
import { requestLogger } from './middleware/logger';

const app = express();
const PORT = parseInt(process.env.API_PORT ?? '8000', 10);
const HOST = process.env.API_HOST ?? '0.0.0.0';

app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN ?? '*' }));
app.use(express.json({ limit: '1mb' }));
app.use(requestLogger);

app.use(healthRouter);
app.use(intakeRouter);
app.use(proposalsRouter);
app.use(webhooksRouter);

app.use((_req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.listen(PORT, HOST, () => {
  console.log(`Stephanie API listening on ${HOST}:${PORT}`);
  console.log(`Environment: ${process.env.APP_ENV ?? 'development'}`);
});

export default app;
