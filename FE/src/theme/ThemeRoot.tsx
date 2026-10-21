import { useEffect, type ReactNode } from 'react'
import { ConfigProvider, theme } from 'antd'
import viVN from 'antd/locale/vi_VN'
import { useIsDark } from './store'

/** LingoPrism colours ("prism": one beam of light split into the three languages). */
export const PRISM = {
  violet: '#6d4aff',
  violetDark: '#8b74ff',
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
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#0c0a17' : '#f5f4f9')
  }, [dark])

  return (
    <ConfigProvider
      locale={viVN}
      theme={{
        algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: dark ? PRISM.violetDark : PRISM.violet,
          colorInfo: dark ? PRISM.violetDark : PRISM.violet,
          colorSuccess: PRISM.mint,
          colorWarning: PRISM.amber,
          colorError: '#f43f5e',
          colorText: dark ? '#eeedf6' : '#1b1538',
          colorTextSecondary: dark ? '#a8a3c4' : '#5d5878',
          borderRadius: 10,
          fontFamily: '"Be Vietnam Pro", "Segoe UI", system-ui, sans-serif',
          colorBgLayout: dark ? '#0c0a17' : '#f5f4f9',
          colorBgContainer: dark ? '#15122a' : '#ffffff',
          colorBgElevated: dark ? '#1d1934' : '#ffffff',
          colorBorder: dark ? '#3a3458' : '#d3cee3',
          colorBorderSecondary: dark ? '#29243f' : '#e7e4f0',
          boxShadowSecondary: dark ? '0 14px 34px -14px rgb(0 0 0 / 0.7)' : '0 12px 32px -12px rgb(27 21 56 / 0.28)',
          motionEaseOut: 'cubic-bezier(0.22, 1, 0.36, 1)',
        },
        components: {
          Layout: { headerBg: dark ? '#15122a' : '#ffffff', siderBg: dark ? '#15122a' : '#ffffff', bodyBg: dark ? '#0c0a17' : '#f5f4f9' },
          Menu: { itemBg: 'transparent', itemBorderRadius: 8, itemSelectedColor: dark ? '#c3b6ff' : '#5533e0' },
          Button: { primaryShadow: 'none', defaultShadow: 'none', dangerShadow: 'none', fontWeight: 600 },
          Card: { boxShadowTertiary: 'none' },
          Table: { headerBg: dark ? '#1d1934' : '#f5f4f9', headerColor: dark ? '#a8a3c4' : '#5d5878' },
        },
      }}
    >
      {children}
    </ConfigProvider>
  )
}
