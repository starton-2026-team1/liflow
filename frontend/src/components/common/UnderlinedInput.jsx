function UnderlinedInput({ action, error, id, ...inputProps }) {
  return (
    <div className="input-group">
      <div className={`underlined-input${error ? ' underlined-input--error' : ''}`}>
        <input id={id} {...inputProps} />
        {action}
      </div>
      {error && <p className="input-error" id={`${id}-error`}>{error}</p>}
    </div>
  )
}

export default UnderlinedInput
