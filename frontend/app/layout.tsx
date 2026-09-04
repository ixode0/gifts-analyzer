export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body style={{ margin: 0, background: '#0d1117', color: '#e6edf3', fontFamily: 'system-ui,sans-serif' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: 16 }}>{children}</div>
      </body>
    </html>
  );
}
