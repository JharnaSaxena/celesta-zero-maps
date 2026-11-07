// Vercel's Express auto-detection entry point. Import Express directly so
// Vercel identifies this as an Express app during its build step.
import express from 'express';
import { app } from './server/server.js';

export { app };
export default app;
