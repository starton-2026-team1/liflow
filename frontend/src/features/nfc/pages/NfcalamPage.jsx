import mascotAlert from '../../../assets/mascot/alert.png'
import '../styles/nfcAlam.css'

function NfcalamPage({ onConfirm, waiting = false, error = '' }) {
  return (
    <main className="nfc-alarm-page">
      <section className="nfc-alarm" aria-labelledby="nfc-alarm-title">
        <div className="nfc-alarm__content">
          <div className="nfc-alarm__image-wrap" aria-hidden="true">
            <span className="nfc-alarm__pulse nfc-alarm__pulse--first" />
            <span className="nfc-alarm__pulse nfc-alarm__pulse--second" />
            <img className="nfc-alarm__mascot" src={mascotAlert} alt="" />
          </div>

          <p className="nfc-alarm__eyebrow">안심 알림 전송 완료</p>
          <h1 id="nfc-alarm-title">
            보호자에게<br />
            알림을 전송했어요
          </h1>
          <p className="nfc-alarm__description">
            {waiting ? <>5분 동안 보호자의 응답을 기다린 뒤<br />연락처를 안전하게 공개할게요.</> : <>보호자가 빠르게 확인할 수 있도록<br />현재 상황을 안전하게 전달했어요.</>}
          </p>
          {error && <p className="nfc-help-error" role="alert">{error}</p>}
        </div>

        <button className="nfc-alarm__button" type="button" onClick={onConfirm} disabled={waiting}>
          {waiting ? '보호자 응답 확인 중' : '확인'}
        </button>
      </section>
    </main>
  )
}

export default NfcalamPage
