function BackButton({ onClick }) {
  return (
    <button className="back-button" type="button" onClick={onClick} aria-label="이전">
      <span aria-hidden="true">‹</span>
    </button>
  )
}

export default BackButton
