import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { askAiChat } from '../../../api/aiChat'
import qnaMascot from '../../../assets/mascot/qna.png'
import '../styles/aiChat.css'

const quickQuestions = [
  '일주일치 기록 정리해 줘',
  '최근 활동에 변화가 있어?',
  '환절기 건강관리 방법 알려줘',
  '민간요법 이용 시 주의할 점은?',
]

export default function AiChatPage({ people, onClose, onError }) {
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [pendingQuestion, setPendingQuestion] = useState('')
  const messagesRef = useRef(null)

  useEffect(() => {
    const messageArea = messagesRef.current
    if (messageArea) messageArea.scrollTop = messageArea.scrollHeight
  }, [messages, pendingQuestion, isSending])

  const needsPersonData = (text) => /(기록|활동|센서|알림|감지|일주일|지난주|최근\s*상태)/.test(text)

  const sendQuestion = async (text, selectedPersonId = null, alreadyAdded = false) => {
    const normalized = text.trim()
    if (!normalized || isSending) return
    if (needsPersonData(normalized) && !selectedPersonId) {
      setMessages((items) => [...items, { role: 'user', content: normalized }])
      setPendingQuestion(normalized)
      setQuestion('')
      return
    }
    if (!alreadyAdded) setMessages((items) => [...items, { role: 'user', content: normalized }])
    setQuestion('')
    setPendingQuestion('')
    setIsSending(true)
    try {
      const result = await askAiChat({ conversationId, personId: selectedPersonId, question: normalized })
      setConversationId(result.conversation_id)
      setMessages((items) => [...items, { role: 'assistant', content: result.answer }])
    } catch (error) {
      setMessages((items) => [
        ...items,
        {
          role: 'assistant',
          content: '답변을 불러오지 못했어요. 잠시 후 다시 질문해 주세요.',
          isError: true,
        },
      ])
      onError(error.message || 'AI 답변을 불러오지 못했어요.')
    } finally {
      setIsSending(false)
    }
  }

  return <div className="ai-chat-page">
    <div className="ai-chat-handle" aria-hidden="true" />
    <h1 className="ai-chat-title">AI 상담</h1>
    <section className="ai-chat-messages" aria-live="polite" ref={messagesRef}>
      <div className="ai-chat-greeting"><span><img src={qnaMascot} alt="살핌이" /></span><p>안녕하세요! 쌓인 생활 기록을 함께 살펴볼게요.<br />활동 변화나 건강 관련 궁금한 내용을 물어보세요.</p></div>
      {messages.length === 0 && !pendingQuestion && <div className="ai-chat-quick-questions">{quickQuestions.map((item) => <button type="button" key={item} onClick={() => sendQuestion(item)}>{item}</button>)}</div>}
      {messages.map((message, index) => <article className={`ai-chat-message ai-chat-message--${message.role}`} key={`${message.role}-${index}`}><span>{message.role === 'assistant' ? '살핌이' : '나'}</span><p>{message.content}</p></article>)}
      {pendingQuestion && <div className="ai-chat-person-request"><strong>누구의 기록을 확인할까요?</strong>{people.length > 0 ? <div>{people.map((person) => <button type="button" key={person.id} onClick={() => sendQuestion(pendingQuestion, person.id, true)}>{person.name} 님</button>)}</div> : <p>먼저 대상자를 등록해 주세요.</p>}</div>}
      {isSending && <article className="ai-chat-message ai-chat-message--assistant"><span>살핌이</span><p>기록을 살펴보고 있어요...</p></article>}
    </section>

    <form className="ai-chat-input" onSubmit={(event) => { event.preventDefault(); sendQuestion(question) }}>
      <textarea value={question} maxLength={2000} rows="1" placeholder="궁금한 내용을 입력하세요" onChange={(event) => setQuestion(event.target.value)} />
      <button type="submit" disabled={!question.trim() || isSending} aria-label="질문 보내기"><Send /></button>
    </form>
    <p className="ai-chat-disclaimer">AI 답변은 의료 진단이나 처방을 대신하지 않습니다. 응급 상황에는 119에 연락하세요.</p>
    <button className="ai-chat-close" type="button" onClick={onClose}>닫기</button>
  </div>
}
