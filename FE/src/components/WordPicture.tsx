import { useState } from 'react'
import { Tooltip } from 'antd'

interface Props {
  image?: string | null
  emoji?: string
  credit?: string
  source?: string
  alt?: string
  /** Tailwind height class of the picture, e.g. h-28 */
  height?: string
}

/** Real photo of a word (Wikimedia Commons, credited); the emoji only when there is no photo or it fails to load. */
export default function WordPicture({ image, emoji, credit, source, alt = '', height = 'h-32' }: Props) {
  const [broken, setBroken] = useState(false)
  if (image && !broken) {
    return (
      <figure className={`relative m-0 ${height} flex items-center justify-center`}>
        <img src={image} alt={alt} loading="lazy" onError={() => setBroken(true)}
          className="h-full max-w-full object-contain rounded-xl" />
        {credit && (
          <Tooltip title={`Ảnh: ${credit} – Wikimedia Commons`}>
            <a href={source || undefined} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
              className="absolute bottom-1 right-1 rounded-full bg-black/40 text-white text-[10px] leading-none px-1.5 py-1 no-underline">
              ©
            </a>
          </Tooltip>
        )}
      </figure>
    )
  }
  if (!emoji) return null
  return <div className={`${height} flex items-center justify-center text-6xl`}>{emoji}</div>
}
