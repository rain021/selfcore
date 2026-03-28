import "./globals.css";

export const metadata = {
  title: "SelfCore — Profile Editor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
