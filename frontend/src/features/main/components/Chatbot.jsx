import { useState } from 'react'
import { Send, X } from 'lucide-react'
import chatbotMascot from '../../../assets/mascot/qna.png'

const suggestedQuestions = [
  '일주일치 기록 정리해 줘',
  '최근 활동에 변화가 있어?',
  '환절기 건강관리 방법 알려줘',
  '민간요법 이용 시 주의할 점은?',
]

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: '안녕하세요! 쌓인 생활 기록을 함께 살펴볼게요. 활동 변화나 건강 관련 궁금한 내용을 물어보세요.',
    },
  ])

  const sendMessage = (text) => {
    const trimmedMessage = text.trim()
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

  const handleSubmit = (event) => {
    event.preventDefault()
    sendMessage(message)
  }

  const showSuggestions = !messages.some(({ sender }) => sender === 'user')

  return (
    <div className={`chatbot${isOpen ? ' chatbot--open' : ''}`}>
      {isOpen && (
        <section className="chatbot-panel" aria-label="살핌이 챗봇">
          <header className="chatbot-panel__header">
            <span className="chatbot-panel__avatar">
              <img src={chatbotMascot} alt="" />
            </span>
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
            {showSuggestions && (
              <div className="chatbot-suggestions" aria-label="추천 질문">
                {suggestedQuestions.map((question) => (
                  <button type="button" key={question} onClick={() => sendMessage(question)}>
                    {question}
                  </button>
                ))}
              </div>
            )}
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
        <img src={chatbotMascot} alt="" />
      </button>
    </div>
  )
}

export default Chatbot
