import "./globals.css";
import "boxicons/css/boxicons.min.css";
import { Inter } from "next/font/google";
import Layout from "./components/Layout";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "geneSTRUCTURE",
  description: "geneSTRUCTURE is a tool for visualizing gene structures.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        <Layout>{children}</Layout>
      </body>
    </html>
  );
}
