export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl">
          CodeForge AI
        </h1>
        <p className="mt-4 text-lg text-gray-600 md:text-xl">
          AI-Powered Collaborative Coding Platform
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Combining LeetCode, GitHub Copilot, Replit, and CodeSandbox
        </p>
      </div>
    </main>
  );
}
