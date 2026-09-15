import { Phone } from 'lucide-react'
import mascotAlert from '../../../assets/mascot/alert.png'
import '../styles/nfcAlam.css'

function NfcGuardianContactPage({ guardianPhone = '010-1234-5678' }) {
  const phoneHref = `tel:${guardianPhone.replace(/[^0-9+]/g, '')}`

  return (
    <main className="nfc-alarm-page">
      <section className="nfc-alarm nfc-alarm--contact" aria-labelledby="nfc-contact-title">
        <div className="nfc-alarm__content">
          <div className="nfc-alarm__image-wrap nfc-alarm__image-wrap--contact" aria-hidden="true">
            <span className="nfc-alarm__pulse nfc-alarm__pulse--first" />
            <span className="nfc-alarm__pulse nfc-alarm__pulse--second" />
            <img className="nfc-alarm__mascot" src={mascotAlert} alt="" />
          </div>

          <p className="nfc-alarm__eyebrow nfc-alarm__eyebrow--urgent">보호자 응답 없음</p>
          <h1 id="nfc-contact-title">
            보호자가 알림을<br />
            아직 확인하지 않았어요
          </h1>
          <p className="nfc-alarm__description">
            도움이 필요한 분의 안전을 위해<br />
            보호자 연락처를 공개했어요.
          </p>

          <div className="nfc-alarm__contact-card" aria-label="보호자 연락처">
            <span>보호자 연락처</span>
            <strong>{guardianPhone}</strong>
          </div>
        </div>

        <a className="nfc-alarm__button nfc-alarm__button--call" href={phoneHref}>
          <Phone aria-hidden="true" />
          보호자에게 전화하기
        </a>
      </section>
    </main>
  )
}

export default NfcGuardianContactPage
