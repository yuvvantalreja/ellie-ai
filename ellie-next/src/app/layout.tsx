import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ["latin"],
  variable: "--font-roboto",
});

export const metadata: Metadata = {
  title: "Ellie - CMU AI Teaching Assistant",
  description: "Carnegie Mellon University's AI Teaching Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/svg+xml" href="/images/favicon.svg" />
      </head>
      <body className={`${roboto.variable} font-sans antialiased`}>
        <div className="page-transition"></div>
        {children}
      </body>
    </html>
  );
}
