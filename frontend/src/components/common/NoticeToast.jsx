import './noticeToast.css'

function NoticeToast({ children }) {
  return <div className="notice-toast" role="status">{children}</div>
}

export default NoticeToast
