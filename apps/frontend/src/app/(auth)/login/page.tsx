import { Metadata } from 'next';
import LoginForm from '@/components/auth/LoginForm';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Login | MediaWhisperer',
  description: 'Login to your MediaWhisperer account',
};

export default async function LoginPage() {
  const session = await getSession();

  if (session) {
    redirect('/dashboard');
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoginForm />
    </div>
  );
}
