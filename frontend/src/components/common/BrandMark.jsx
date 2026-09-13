import { Activity, ShieldCheck } from 'lucide-react'

function BrandMark() {
  return (
    <div className="brand-mark" aria-label="app service">
      <span className="brand-mark__icon" aria-hidden="true">
        <ShieldCheck />
        <Activity />
      </span>
      <span className="brand-mark__name">app name</span>
    </div>
  )
}

export default BrandMark
