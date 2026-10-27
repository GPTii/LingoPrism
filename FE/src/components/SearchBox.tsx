import { Input } from 'antd'
import type { SearchProps } from 'antd/es/input'
import { useEffect, useRef } from 'react'

/** A search box that searches while you type: once typing pauses for `delay` ms (so Vietnamese typed with Telex,
 * several keys per letter, is one search, not one per key), and at once on Enter or when cleared. The same
 * search is never sent twice. */
export default function SearchBox({ onSearch, onChange, delay = 350, ...props }: Omit<SearchProps, 'onSearch'> & {
  onSearch: (value: string) => void
  delay?: number
}) {
  const timer = useRef<number | undefined>(undefined)
  const last = useRef<string | undefined>(undefined)
  const fire = (value: string) => {
    window.clearTimeout(timer.current)
    const term = value.trim()
    if (term === last.current) return
    last.current = term
    onSearch(term)
  }
  useEffect(() => () => window.clearTimeout(timer.current), [])
  return (
    <Input.Search {...props}
      onChange={(e) => {
        onChange?.(e)
        const value = e.target.value
        window.clearTimeout(timer.current)
        if (!value) return fire('')  // the clear button
        timer.current = window.setTimeout(() => fire(value), delay)
      }}
      onSearch={(value) => fire(value)} />
  )
}
