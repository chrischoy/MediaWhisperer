import { PropsWithChildren } from 'react';
import Link from 'next/link';

export default function AuthLayout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <Link href="/" className="text-xl font-bold text-gray-900">
            MediaWhisperer
          </Link>
        </div>
      </header>

      <main className="flex-grow">{children}</main>

      <footer className="bg-white border-t py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500 text-sm">
          © {new Date().getFullYear()} MediaWhisperer. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
