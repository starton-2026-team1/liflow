import { useState } from 'react'
import { MessageCircle, Send, X } from 'lucide-react'

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?' },
  ])

  const handleSubmit = (event) => {
    event.preventDefault()
    const trimmedMessage = message.trim()
    if (!trimmedMessage) return

    setMessages((current) => [
      ...current,
      { id: Date.now(), sender: 'user', text: trimmedMessage },
      {
        id: Date.now() + 1,
        sender: 'bot',
        text: '현재는 상담 기능을 준비하고 있어요. 곧 더 정확한 답변을 드릴게요.',
      },
    ])
    setMessage('')
  }

  return (
    <div className={`chatbot${isOpen ? ' chatbot--open' : ''}`}>
      {isOpen && (
        <section className="chatbot-panel" aria-label="살핌이 챗봇">
          <header className="chatbot-panel__header">
            <span className="chatbot-panel__avatar"><MessageCircle aria-hidden="true" /></span>
            <div>
              <strong>살핌이</strong>
              <span>무엇이든 물어보세요</span>
            </div>
            <button type="button" onClick={() => setIsOpen(false)} aria-label="챗봇 닫기">
              <X aria-hidden="true" />
            </button>
          </header>

          <div className="chatbot-panel__messages" aria-live="polite">
            {messages.map((item) => (
              <p className={`chatbot-message chatbot-message--${item.sender}`} key={item.id}>
                {item.text}
              </p>
            ))}
          </div>

          <form className="chatbot-panel__composer" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="chatbot-message">메시지 입력</label>
            <input
              id="chatbot-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="메시지를 입력해 주세요"
              autoComplete="off"
            />
            <button type="submit" disabled={!message.trim()} aria-label="메시지 보내기">
              <Send aria-hidden="true" />
            </button>
          </form>
        </section>
      )}

      <button
        className="chatbot-button"
        type="button"
        aria-label={isOpen ? '챗봇 닫기' : '챗봇 열기'}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        {isOpen ? <X aria-hidden="true" /> : <MessageCircle aria-hidden="true" />}
      </button>
    </div>
  )
}

export default Chatbot
