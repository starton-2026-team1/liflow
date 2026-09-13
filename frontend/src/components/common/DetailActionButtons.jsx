import './detailActionButtons.css'

export default function DetailActionButtons({
  primaryLabel,
  onPrimary,
  secondaryLabel,
  onSecondary,
  secondaryDisabled = false,
}) {
  return (
    <div className="detail-action-buttons">
      <button type="button" onClick={onPrimary}>{primaryLabel}</button>
      <button
        className="detail-action-buttons__secondary"
        type="button"
        onClick={onSecondary}
        disabled={secondaryDisabled}
      >
        {secondaryLabel}
      </button>
    </div>
  )
}
