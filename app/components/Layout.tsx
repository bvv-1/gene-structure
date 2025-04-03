"use client";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 gradient-bg">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <header className="mb-12">
          <nav className="flex justify-between items-center">
            <div className="flex items-center">
              <i className="bx bx-dna text-4xl text-blue-600"></i>
              <h1 className="text-2xl font-bold ml-2 text-black">
                Gene Structure Visualizer
              </h1>
            </div>
            <div className="flex space-x-6">
              <a
                href="/"
                className="text-black hover:text-blue-600 transition-colors"
              >
                Home
              </a>
              <a
                href="/docs"
                className="text-black hover:text-blue-600 transition-colors"
              >
                Docs
              </a>
              <a
                href="/faq"
                className="text-black hover:text-blue-600 transition-colors"
              >
                FAQ
              </a>
            </div>
          </nav>
        </header>
        {children}
        <div className="mt-8 text-sm text-gray-500 dark:text-gray-400 text-center">
          <p>© 2025 geneSTRUCTURE</p>
        </div>
      </div>
    </main>
  );
}
