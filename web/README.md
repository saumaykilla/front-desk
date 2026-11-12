# Web application

Next.js App Router application using TypeScript, Tailwind CSS v4, ESLint, and shadcn/ui configuration. Hospitality workflows are not implemented.

```bash
cp .env.example .env.local
npm ci
npm run dev
```

Set `NEXT_PUBLIC_BACKEND_API_URL` to the FastAPI base URL. It is public browser configuration; never put secrets in `NEXT_PUBLIC_` variables.

Checks: `npm run typecheck`, `npm run lint`, `npm run build`.
