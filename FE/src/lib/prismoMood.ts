import type { GameSummary } from '../api/app'
import type { Mood } from '../components/brand/Brand'

/**
 * How my Prismo feels about my learning today, with one line saying why:
 * sad right after a lost streak, sleepy while today's lesson is still waiting, happy once I have studied,
 * celebrating when every quest of the day is done.
 */
export function prismoMood(g: GameSummary | undefined, questsDone = false, name = 'Prismo'): { mood: Mood; line: string } {
  if (!g) return { mood: 'happy', line: '' }
  if (g.repairable_streak > 0 && !g.studied_today)
    return { mood: 'sad', line: `${name} buồn vì mất chuỗi ${g.repairable_streak} ngày. Hồi chuỗi trong Cửa hàng để nối lại.` }
  if (g.studied_today && questsDone) return { mood: 'celebrate', line: `Xong hết nhiệm vụ hôm nay, ${name} vui lắm!` }
  if (g.studied_today) return { mood: 'happy', line: `${name} vui vì hôm nay bạn đã học.` }
  if (g.streak > 0) return { mood: 'sleepy', line: `${name} đang ngủ gật. Học một bài để giữ chuỗi ${g.streak} ngày.` }
  return { mood: 'wow', line: `Học một bài để ${name} thức dậy nhé!` }
}
