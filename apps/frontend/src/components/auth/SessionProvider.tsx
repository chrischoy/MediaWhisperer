'use client';

import { SessionProvider as NextAuthSessionProvider } from 'next-auth/react';
import { PropsWithChildren } from 'react';

export default function SessionProvider({ children }: PropsWithChildren) {
  return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
}
