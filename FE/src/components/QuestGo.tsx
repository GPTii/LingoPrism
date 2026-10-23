import { Button } from 'antd'
import { ArrowRightOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'

/** Where each daily quest kind (DailyQuest.Kind on the server) is done. */
const QUEST_LINK: Record<string, string> = {
  save_words: '/camera',
  reach_learn_goal: '/learn?kind=learn',
  reach_review_goal: '/learn?kind=review',
  post_community_image: '/community',
  engage_community: '/community',
}

/** The arrow beside an unfinished quest that takes the learner to where it is done. */
export function QuestGo({ kind, title }: { kind: string; title: string }) {
  const to = QUEST_LINK[kind]
  if (!to) return null
  return (
    <Link to={to} aria-label={`Làm nhiệm vụ: ${title}`} title="Làm ngay">
      <Button size="small" shape="circle" type="primary" ghost icon={<ArrowRightOutlined />} tabIndex={-1} />
    </Link>
  )
}
