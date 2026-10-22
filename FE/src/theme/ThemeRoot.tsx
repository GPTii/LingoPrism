import { useEffect, type ReactNode } from 'react'
import { ConfigProvider, theme } from 'antd'
import viVN from 'antd/locale/vi_VN'
import { useIsDark } from './store'

/** LingoPrism colours ("prism": one beam of light split into the three languages). */
export const PRISM = {
  blue: '#1899f0',
  blueDark: '#1899f0',
  cyan: '#06b6d4',
  mint: '#10c79a',
  amber: '#ffb020',
  coral: '#ff6b81',
}

/** antd theme (light / dark) + the `dark` class on <html> for the Tailwind side. */
export default function ThemeRoot({ children }: { children: ReactNode }) {
  const dark = useIsDark()
  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', dark)
    root.style.colorScheme = dark ? 'dark' : 'light'
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#0b111b' : '#f6f8fb')
  }, [dark])

  return (
    <ConfigProvider
      locale={viVN}
      theme={{
        algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: dark ? PRISM.blueDark : PRISM.blue,
          colorInfo: dark ? PRISM.blueDark : PRISM.blue,
          colorSuccess: PRISM.mint,
          colorWarning: PRISM.amber,
          colorError: '#f43f5e',
          colorText: dark ? '#e8edf3' : '#15233b',
          colorTextSecondary: dark ? '#9aa8bb' : '#556273',
          borderRadius: 10,
          fontFamily: '"Be Vietnam Pro", "Segoe UI", system-ui, sans-serif',
          colorBgLayout: dark ? '#0b111b' : '#f6f8fb',
          colorBgContainer: dark ? '#131b28' : '#ffffff',
          colorBgElevated: dark ? '#1a2433' : '#ffffff',
          colorBorder: dark ? '#33415a' : '#cdd6e1',
          colorBorderSecondary: dark ? '#243043' : '#e3e8ef',
          boxShadowSecondary: dark ? '0 14px 34px -14px rgb(0 0 0 / 0.7)' : '0 12px 32px -12px rgb(21 35 59 / 0.28)',
          motionEaseOut: 'cubic-bezier(0.22, 1, 0.36, 1)',
        },
        components: {
          Layout: { headerBg: dark ? '#131b28' : '#ffffff', siderBg: dark ? '#131b28' : '#ffffff', bodyBg: dark ? '#0b111b' : '#f6f8fb' },
          Menu: { itemBg: 'transparent', itemBorderRadius: 8, itemSelectedColor: dark ? '#8fd0fb' : '#0f7ac4' },
          Button: { primaryShadow: 'none', defaultShadow: 'none', dangerShadow: 'none', fontWeight: 600 },
          Card: { boxShadowTertiary: 'none' },
          Table: { headerBg: dark ? '#1a2433' : '#f6f8fb', headerColor: dark ? '#9aa8bb' : '#556273' },
        },
      }}
    >
      {children}
    </ConfigProvider>
  )
}
