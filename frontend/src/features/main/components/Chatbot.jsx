import { useState } from 'react'
import { Send, X } from 'lucide-react'
import { askAiChat } from '../../../api/aiChat'
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
  const [conversationId, setConversationId] = useState(null)
  const [isSending, setIsSending] = useState(false)
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: '안녕하세요! 쌓인 생활 기록을 함께 살펴볼게요. 활동 변화나 건강 관련 궁금한 내용을 물어보세요.',
    },
  ])

  const sendMessage = async (text) => {
    const trimmedMessage = text.trim()
    if (!trimmedMessage || isSending) return

    setMessages((current) => [
      ...current,
      { id: Date.now(), sender: 'user', text: trimmedMessage },
    ])
    setMessage('')
    if (/(기록|활동|센서|알림|감지|일주일|지난주|최근\s*상태)/.test(trimmedMessage)) {
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        sender: 'bot',
        text: '대상자 기록 분석은 개인정보 보호를 위한 로컬 모델이 준비된 후 제공할게요.',
      }])
      return
    }

    setIsSending(true)
    try {
      const result = await askAiChat({ conversationId, question: trimmedMessage })
      setConversationId(result.conversation_id)
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        sender: 'bot',
        text: result.answer,
      }])
    } catch (error) {
      setMessages((current) => [...current, {
        id: Date.now() + 1,
        sender: 'bot',
        text: error.message || '답변을 불러오지 못했어요. 잠시 후 다시 질문해 주세요.',
      }])
    } finally {
      setIsSending(false)
    }
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
              <span>
                AI 답변은 의료진의 진단·처방을 대신하지 않습니다.<br />
                응급 상황에는 즉시 119에 연락해주세요.
              </span>
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
            {isSending && <p className="chatbot-message chatbot-message--bot">답변을 준비하고 있어요...</p>}
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
            <button type="submit" disabled={!message.trim() || isSending} aria-label="메시지 보내기">
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
