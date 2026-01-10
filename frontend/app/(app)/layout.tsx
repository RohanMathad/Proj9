import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

export default async function Layout({ children }: LayoutProps) {
  const hdrs = await headers();

  // Keep this call so nothing upstream breaks,
  // even though we no longer use the values.
  await getAppConfig(hdrs);

  return (
    <>
      {children}
      <>
      Footer 
      </>

    </>
  );
}
