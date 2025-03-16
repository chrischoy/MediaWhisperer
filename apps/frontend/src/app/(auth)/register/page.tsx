import { Metadata } from 'next';
import RegisterForm from '@/components/auth/RegisterForm';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Register | MediaWhisperer',
  description: 'Create a new MediaWhisperer account',
};

export default async function RegisterPage() {
  const session = await getSession();

  if (session) {
    redirect('/dashboard');
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <RegisterForm />
    </div>
  );
}
