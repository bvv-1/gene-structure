import "./globals.css";
import "boxicons/css/boxicons.min.css";
import { Open_Sans } from "next/font/google";
import Layout from "./components/Layout";

const openSans = Open_Sans({ subsets: ["latin"] });

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
      <body className={openSans.className}>
        <Layout>{children}</Layout>
      </body>
    </html>
  );
}
