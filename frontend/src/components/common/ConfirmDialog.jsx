import { useEffect } from 'react'
import './confirmDialog.css'

function ConfirmDialog({
  cancelLabel = '취소',
  confirmLabel = '확인',
  confirmingLabel = '삭제 중...',
  description,
  isConfirming = false,
  onCancel,
  onConfirm,
  title,
}) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && !isConfirming) onCancel()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isConfirming, onCancel])

  return (
    <div className="confirm-dialog-backdrop" role="presentation" onMouseDown={() => !isConfirming && onCancel()}>
      <section
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby={description ? 'confirm-dialog-description' : undefined}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="confirm-dialog-title">{title}</h2>
        {description && <p id="confirm-dialog-description">{description}</p>}
        <div className="confirm-dialog__actions">
          <button type="button" onClick={onCancel} disabled={isConfirming}>{cancelLabel}</button>
          <button className="confirm-dialog__confirm" type="button" onClick={onConfirm} disabled={isConfirming} autoFocus>
            {isConfirming ? confirmingLabel : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  )
}

export default ConfirmDialog
