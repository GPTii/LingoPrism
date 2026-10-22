/**
 * LingoPrism's own UI icons: chunky, filled, each shape on a darker lip like the buttons.
 * The SVGs live in public/icons/ui and are shared with the app (MOBILE/assets/icons/ui);
 * both copies come from one generator, so a fix is made there, not in a single file.
 */
export type AppIconName =
  | 'home' | 'learn' | 'vocab' | 'camera' | 'community' | 'trophy' | 'chat' | 'bell'
  | 'sparkle' | 'review' | 'tiles' | 'mic' | 'pencil' | 'exam' | 'shapes' | 'bookmark'
  | 'photo' | 'pin' | 'news' | 'group' | 'podium' | 'mail' | 'chart' | 'target'
  | 'calendar' | 'medal' | 'bag' | 'cap' | 'profile' | 'check' | 'book' | 'more'

export function AppIcon({ name, size = 24, className = '' }: { name: AppIconName; size?: number; className?: string }) {
  return (
    <img src={`/icons/ui/${name}.svg`} width={size} height={size} alt="" aria-hidden draggable={false}
      className={`inline-block shrink-0 select-none ${className}`} />
  )
}
