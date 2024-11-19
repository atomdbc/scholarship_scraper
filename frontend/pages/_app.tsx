// pages/_app.tsx
import { Layout } from '../components/layout/Layout';
import '../styles/globals.css';
import type { AppProps } from 'next/app';
console.log(process.env.PORT);


export default function App({ Component, pageProps }: AppProps) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}