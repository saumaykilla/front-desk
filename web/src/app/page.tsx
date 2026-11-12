export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-16">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">Front Desk Agent</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-tight sm:text-6xl">Development foundation</h1>
      <p className="mt-5 max-w-2xl text-lg leading-8 text-neutral-600">
        The web application is ready for future staff workflows. Backend health and API client wiring are configured; hospitality operations are not enabled yet.
      </p>
      <div className="mt-10 rounded-xl border border-neutral-200 bg-neutral-50 p-5 text-sm text-neutral-700">
        Configure <code className="font-mono">NEXT_PUBLIC_BACKEND_API_URL</code> to connect this app to a local backend.
      </div>
    </main>
  );
}
