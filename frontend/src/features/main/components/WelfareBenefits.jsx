import { useEffect, useState } from 'react'
import { ChevronRight, ExternalLink } from 'lucide-react'
import BackButton from '../../../components/common/BackButton'
import { getWelfareBenefits, parseRegion } from '../../../api/welfareBenefits'
import { koreanRegions } from '../data/koreanRegions'
import analyzingMascot from '../../../assets/mascot/analyzing.png'
import emptyMascot from '../../../assets/mascot/empty.png'
import '../styles/welfareBenefits.css'

const categories = ['전체', '돌봄', '건강·의료', '생활지원', '주거']

export function WelfareBenefitsCard({ onClick, person }) {
  const region = parseRegion(person?.livingSpace)
  return (
    <button className="welfare-preview" type="button" onClick={onClick}>
      <span className="welfare-preview__content">
        <strong>우리 동네 복지 혜택</strong>
        <small>{region ? `${region.province} ${region.district}`.trim() : '거주지역을 등록하면'} 받을 수 있는 지원을 확인해 보세요</small>
        <span className="welfare-preview__tags" aria-hidden="true">
          <i>돌봄</i><i>건강·의료</i><i>생활지원</i>
        </span>
      </span>
      <ChevronRight aria-hidden="true" />
    </button>
  )
}

export function WelfareBenefitsPage({ onBack, person }) {
  const savedRegion = parseRegion(person?.livingSpace)
  const initialProvince = savedRegion?.province || '서울특별시'
  const initialDistrict = savedRegion?.district || koreanRegions[initialProvince]?.[0] || ''
  const [category, setCategory] = useState('전체')
  const [region, setRegion] = useState({ province: initialProvince, district: initialDistrict })
  const [benefits, setBenefits] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let isActive = true
    getWelfareBenefits(region)
      .then((items) => { if (isActive) setBenefits(items) })
      .catch((requestError) => {
        if (isActive) setError(requestError.message || '복지 혜택을 불러오지 못했어요.')
      })
      .finally(() => { if (isActive) setIsLoading(false) })
    return () => { isActive = false }
  }, [region, refreshKey])

  const changeProvince = (event) => {
    const province = event.target.value
    setBenefits([])
    setError('')
    setIsLoading(true)
    setRegion({ province, district: koreanRegions[province]?.[0] || '' })
  }

  const changeDistrict = (event) => {
    setBenefits([])
    setError('')
    setIsLoading(true)
    setRegion((current) => ({ ...current, district: event.target.value }))
  }

  const retry = () => {
    setError('')
    setIsLoading(true)
    setRefreshKey((key) => key + 1)
  }

  const visibleBenefits = category === '전체'
    ? benefits
    : benefits.filter((benefit) => benefit.category === category)

  return (
    <div className="welfare-page">
      <header className="welfare-page__header">
        <BackButton onClick={onBack} />
        <div>
          <h1>우리 동네 복지 혜택</h1>
        </div>
      </header>

      <section className="welfare-region" aria-label="지역 선택">
        <div className="welfare-region__selects">
          <label>
            <span>시·도</span>
            <select value={region.province} onChange={changeProvince}>
              {Object.keys(koreanRegions).map((province) => <option key={province}>{province}</option>)}
            </select>
          </label>
          <label>
            <span>시·군·구</span>
            <select value={region.district} onChange={changeDistrict}>
              {koreanRegions[region.province].map((district) => <option key={district}>{district}</option>)}
            </select>
          </label>
        </div>
      </section>

      <div className="welfare-filters" role="tablist" aria-label="복지 혜택 분야">
        {categories.map((item) => (
          <button
            type="button"
            role="tab"
            aria-selected={category === item}
            className={category === item ? 'is-active' : ''}
            onClick={() => setCategory(item)}
            key={item}
          >
            {item}
          </button>
        ))}
      </div>

      <section className="welfare-list" aria-live="polite">
        {!isLoading && !error && visibleBenefits.length > 0 && (
          <p className="welfare-list__count">확인 가능한 혜택 {visibleBenefits.length}개</p>
        )}
        {isLoading && (
          <div className="welfare-list__loading" role="status" aria-label="복지 혜택 불러오는 중">
            <img src={analyzingMascot} alt="" />
          </div>
        )}
        {error && (
          <div className="welfare-list__state" role="alert">
            <p>{error}</p>
            <button type="button" onClick={retry}>다시 시도</button>
          </div>
        )}
        {!isLoading && !error && visibleBenefits.length === 0 && (
          <div className="welfare-list__empty">
            <img src={emptyMascot} alt="" />
            <strong>해당하는 복지 혜택이 없어요</strong>
            <p>다른 지역이나 분야를 선택해 보세요.</p>
          </div>
        )}
        {!isLoading && !error && visibleBenefits.map((benefit) => (
          <article className="welfare-benefit-card" key={benefit.id}>
            <span>{benefit.category}</span>
            <h2>{benefit.title}</h2>
            <p>{benefit.description}</p>
            <div>
              <small>{benefit.organization}</small>
              {benefit.officialUrl ? (
                <a href={benefit.officialUrl} target="_blank" rel="noreferrer">
                  조건 확인하기<ExternalLink aria-hidden="true" />
                </a>
              ) : <span className="welfare-benefit-card__pending">상세 정보 준비 중</span>}
            </div>
          </article>
        ))}
      </section>

      <p className="welfare-page__disclaimer">
        실제 지원 대상과 신청 방법은 복지로 또는 담당 기관에서 최종 확인해 주세요.
      </p>
    </div>
  )
}
