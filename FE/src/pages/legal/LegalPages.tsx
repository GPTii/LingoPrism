import { useQuery } from '@tanstack/react-query'
import { Skeleton, Tag } from 'antd'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { Logo } from '../../components/brand/Brand'

/** Version (date) of these two texts: must equal LEGAL_VERSION in BE/config/settings/base.py, which records
 * the version each learner accepted. Change both when the wording changes. */
export const LEGAL_VERSION = '2026-10-28'
/** shown as the contact address of the policies; until set, the in-app Support chat is the contact */
export const CONTACT_EMAIL = ''

const day = (iso: string) => iso.split('-').reverse().join('/')

function LegalLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="learner min-h-screen">
      <header className="max-w-3xl mx-auto px-4 sm:px-6 pt-6 flex items-center justify-between">
        <Link to="/" aria-label="LingoPrism"><Logo /></Link>
        <nav className="flex gap-4 text-sm font-semibold">
          <Link to="/privacy">Quyền riêng tư</Link>
          <Link to="/terms">Điều khoản</Link>
          <Link to="/releases">Có gì mới</Link>
        </nav>
      </header>
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <article className="lp-card p-6 sm:p-10 legal-text">
          <h1 className="text-3xl font-extrabold text-slate-800 mt-0">{title}</h1>
          {children}
        </article>
      </main>
    </div>
  )
}

const contact = (
  <>qua mục <b>Hỗ trợ</b> trong ứng dụng (web và app){CONTACT_EMAIL && <> hoặc email <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a></>}</>
)

export function PrivacyPage() {
  return (
    <LegalLayout title="Chính sách quyền riêng tư">
      <p className="text-slate-500">Phiên bản {day(LEGAL_VERSION)}. Áp dụng cho website lingoprism.id.vn và ứng dụng LingoPrism.</p>
      <p>LingoPrism là ứng dụng học từ vựng tiếng Việt, tiếng Anh và tiếng Trung qua hình ảnh. Trang này nói rõ chúng tôi thu thập dữ liệu gì, dùng vào việc gì, chia sẻ với ai, giữ bao lâu và bạn có những quyền gì, theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.</p>

      <h2>1. Dữ liệu chúng tôi thu thập</h2>
      <ul>
        <li><b>Tài khoản:</b> email, mật khẩu (chỉ lưu dạng đã mã hoá một chiều), tên hiển thị, ảnh đại diện. Nếu đăng nhập bằng Google: email và tên Google cung cấp.</li>
        <li><b>Hồ sơ học:</b> ngôn ngữ đang học, mục tiêu, và nếu bạn tự điền: ngày sinh, giới tính, mục đích học.</li>
        <li><b>Quá trình học:</b> từ đã lưu, kết quả từng câu trả lời, lịch ôn, bài kiểm tra, XP, huy hiệu, vật phẩm.</li>
        <li><b>Ảnh bạn chụp để nhận diện và ảnh bài đăng:</b> trước khi lưu, máy chủ <b>xoá toàn bộ thông tin EXIF (gồm toạ độ GPS nơi chụp)</b>, đổi tên ngẫu nhiên và thu nhỏ ảnh.</li>
        <li><b>Vị trí</b> (chỉ khi bạn cho phép và dùng tính năng Học theo vị trí): khi bạn tới gần một địa điểm học (POI), chúng tôi lưu toạ độ và khoảng cách lúc đó để gợi ý từ và tính lượt ghé.</li>
        <li><b>Cộng đồng:</b> bài đăng, bình luận, tin nhắn nhóm, tin nhắn riêng, lời mời kết bạn, báo cáo vi phạm (kèm bản sao các tin nhắn gần nhất để người kiểm duyệt xem xét).</li>
        <li><b>Thiết bị:</b> mã nhận thông báo đẩy (khi bạn bật thông báo), địa chỉ IP trong nhật ký bảo mật (đăng nhập sai, chống spam).</li>
      </ul>
      <p><b>Giọng nói</b> khi luyện phát âm được nhận dạng bởi trình duyệt hoặc điện thoại của bạn (dịch vụ nhận dạng giọng nói của Google hoặc Apple); LingoPrism không nhận và không lưu bản ghi âm.</p>

      <h2>2. Chúng tôi dùng dữ liệu để làm gì</h2>
      <ul>
        <li>Cung cấp tính năng: học, ôn tập đúng lúc, nhận diện đồ vật, bảng xếp hạng, nhóm và tin nhắn.</li>
        <li>Đồng bộ tiến độ giữa web và app, gửi thông báo nhắc học (bạn tắt được trong Hồ sơ).</li>
        <li>Giữ an toàn: chống spam, chặn đăng nhập trái phép, kiểm duyệt nội dung bị báo cáo.</li>
        <li>Cải thiện mô hình nhận diện: chỉ dùng những lần bạn <b>tự báo lỗi</b> nhận diện (phần ảnh của đồ vật đó).</li>
      </ul>
      <p>Chúng tôi <b>không bán dữ liệu</b>, <b>không hiển thị quảng cáo</b> và <b>không dùng mã quảng cáo</b> của thiết bị.</p>

      <h2>3. Bên thứ ba xử lý dữ liệu</h2>
      <ul>
        <li><b>Microsoft Azure</b> (máy chủ, khu vực Đông Á): lưu toàn bộ dữ liệu ở trên. Dữ liệu vì vậy được lưu ngoài lãnh thổ Việt Nam.</li>
        <li><b>Cloudflare:</b> chuyển tiếp và bảo vệ kết nối tới website (chống tấn công).</li>
        <li><b>Google:</b> đăng nhập bằng Google, gửi thông báo đẩy (Firebase), gửi email (Gmail).</li>
        <li><b>Google Gemini</b> (khi bạn tạo hội thoại AI từ ảnh): chỉ gửi <b>danh sách từ</b> và trình độ, không gửi ảnh hay thông tin của bạn.</li>
      </ul>

      <h2>4. Trẻ em</h2>
      <p>Với tài khoản trẻ em hoặc người dưới 16 tuổi, LingoPrism chỉ cho dùng sau khi <b>cha, mẹ hoặc người giám hộ đồng ý</b>: chúng tôi gửi mã xác nhận tới email của phụ huynh, kèm đường dẫn tới chính sách này. Chế độ trẻ em ẩn bảng tin, kết bạn, nhóm và tin nhắn. Phụ huynh có thể yêu cầu xem hoặc xoá dữ liệu của con bất cứ lúc nào {contact}.</p>

      <h2>5. Thời gian lưu</h2>
      <ul>
        <li>Dữ liệu được giữ đến khi bạn xoá nó hoặc xoá tài khoản.</li>
        <li>Bản sao lưu hằng đêm được giữ 14 ngày trên máy chủ và tối đa 60 ngày trong kho sao lưu ngoài máy chủ, rồi tự xoá. Dữ liệu đã xoá sẽ biến mất khỏi bản sao lưu sau thời gian đó.</li>
      </ul>

      <h2>6. Quyền của bạn</h2>
      <ul>
        <li><b>Xem và sửa</b> thông tin trong Hồ sơ.</li>
        <li><b>Xoá</b> từng từ đã lưu, ảnh, thông báo, bài đăng; hoặc <Link to="/delete-account">xoá toàn bộ tài khoản</Link>.</li>
        <li><b>Rút lại đồng ý, yêu cầu bản sao dữ liệu</b> hoặc khiếu nại: liên hệ {contact}. Chúng tôi trả lời trong vòng 72 giờ.</li>
      </ul>

      <h2>7. Bảo mật</h2>
      <p>Kết nối luôn mã hoá (HTTPS); mật khẩu được băm; ứng dụng điện thoại cất thông tin đăng nhập trong kho bảo mật của máy; mọi thao tác của quản trị viên đều được ghi nhật ký.</p>

      <h2>8. Thay đổi chính sách</h2>
      <p>Khi chính sách thay đổi, ngày phiên bản ở đầu trang thay đổi và mục <Link to="/releases">Có gì mới</Link> ghi lại thay đổi.</p>
    </LegalLayout>
  )
}

export function TermsPage() {
  return (
    <LegalLayout title="Điều khoản sử dụng">
      <p className="text-slate-500">Phiên bản {day(LEGAL_VERSION)}.</p>
      <h2>1. Tài khoản</h2>
      <ul>
        <li>Bạn cung cấp email thật và giữ mật khẩu của mình. Mỗi người một tài khoản.</li>
        <li>Người dưới 16 tuổi chỉ dùng khi có cha, mẹ hoặc người giám hộ đồng ý (xem <Link to="/privacy">Chính sách quyền riêng tư</Link>).</li>
      </ul>
      <h2>2. Nội dung bạn đăng</h2>
      <ul>
        <li>Bạn chịu trách nhiệm về ảnh, bài đăng, bình luận và tin nhắn của mình, và cho LingoPrism quyền hiển thị chúng cho những người bạn đã chọn chia sẻ.</li>
        <li>Không đăng nội dung vi phạm pháp luật, bạo lực, khiêu dâm, quấy rối, lừa đảo, spam, hay ảnh của người khác khi chưa được phép.</li>
        <li>Nội dung bị báo cáo có thể bị ẩn; tài khoản vi phạm có thể bị khoá ngay.</li>
      </ul>
      <h2>3. Dùng dịch vụ</h2>
      <ul>
        <li>Không dò mật khẩu, không gửi tự động số lượng lớn yêu cầu, không tìm cách vượt qua giới hạn hay phân quyền.</li>
        <li>XP, ngọc, vảy và vật phẩm chỉ có giá trị trong ứng dụng, không quy đổi ra tiền.</li>
      </ul>
      <h2>4. Nội dung học</h2>
      <p>Từ vựng và câu ví dụ được đối chiếu với các nguồn từ điển mở; kết quả nhận diện ảnh có thể sai. Bạn có thể báo lỗi ngay trong ứng dụng.</p>
      <h2>5. Ngừng dùng</h2>
      <p>Bạn có thể <Link to="/delete-account">xoá tài khoản</Link> bất cứ lúc nào. Dịch vụ có thể thay đổi hoặc tạm ngừng để bảo trì; khi có thay đổi lớn, chúng tôi thông báo trong ứng dụng.</p>
      <h2>6. Liên hệ</h2>
      <p>Mọi câu hỏi, liên hệ {contact}.</p>
    </LegalLayout>
  )
}

/** Public page Google Play asks for: how to delete the account, and what goes with it. */
export function DeleteAccountInfoPage() {
  return (
    <LegalLayout title="Xoá tài khoản LingoPrism">
      <h2>Cách xoá</h2>
      <ol>
        <li>Đăng nhập trên web (<Link to="/profile">lingoprism.id.vn/profile</Link>) hoặc mở ứng dụng → <b>Hồ sơ</b>.</li>
        <li>Kéo xuống mục <b>Xoá tài khoản</b>, nhập mật khẩu (tài khoản Google: gõ <b>XOA</b>) rồi xác nhận.</li>
      </ol>
      <p>Không đăng nhập được? Hãy liên hệ {contact}, ghi rõ email của tài khoản. Phụ huynh có thể yêu cầu xoá tài khoản của con theo cách này.</p>
      <h2>Những gì bị xoá</h2>
      <p>Ngay lập tức và vĩnh viễn: hồ sơ, tiến độ học, từ đã lưu, ảnh đã chụp, bài đăng, bình luận, tin nhắn, bạn bè, huy hiệu, vật phẩm và mọi thiết bị đang đăng nhập. Bản sao lưu chứa dữ liệu cũ tự xoá sau tối đa 60 ngày. Nhật ký bảo mật (không chứa nội dung) được giữ theo quy định.</p>
    </LegalLayout>
  )
}

/** "Có gì mới": every version's notes, from the server (BE/apps/core/releases.json). */
export function ReleasesPage() {
  const q = useQuery({ queryKey: ['releases'], queryFn: authApi.releases })
  return (
    <LegalLayout title="Có gì mới">
      {q.isLoading ? <Skeleton active /> : q.data?.results.map((r) => (
        <section key={r.version} className="mb-8">
          <h2 className="flex flex-wrap items-center gap-2">
            <Tag color="blue" className="!text-base !px-2 !py-0.5">{r.version}</Tag> {r.title}
          </h2>
          <p className="text-slate-500 -mt-2">{day(r.date)}</p>
          <ReleaseLists r={r} />
        </section>
      ))}
    </LegalLayout>
  )
}

export function ReleaseLists({ r }: { r: { new: string[]; improved: string[]; fixed: string[] } }) {
  return (
    <>
      {([['new', 'Mới'], ['improved', 'Cải thiện'], ['fixed', 'Sửa lỗi']] as const).map(([key, label]) => r[key].length > 0 && (
        <div key={key}>
          <h3 className="text-base font-bold text-slate-700 mb-1">{label}</h3>
          <ul className="mt-0">{r[key].map((line) => <li key={line}>{line}</li>)}</ul>
        </div>
      ))}
    </>
  )
}
