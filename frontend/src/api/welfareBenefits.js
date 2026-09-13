import { apiRequest } from './client'

const provinceAliases = {
  서울: '서울특별시', 부산: '부산광역시', 대구: '대구광역시', 인천: '인천광역시',
  광주: '광주광역시', 대전: '대전광역시', 울산: '울산광역시', 세종: '세종특별자치시',
  경기: '경기도', 강원: '강원특별자치도', 충북: '충청북도', 충남: '충청남도',
  전북: '전북특별자치도', 전남: '전라남도', 경북: '경상북도', 경남: '경상남도',
  제주: '제주특별자치도',
}

export const parseRegion = (livingSpace = '') => {
  const parts = livingSpace.trim().split(/\s+/)
  const province = provinceAliases[parts[0]] || (
    /(?:특별시|광역시|특별자치시|특별자치도|도)$/.test(parts[0] || '') ? parts[0] : ''
  )
  const district = /(?:시|군|구)$/.test(parts[1] || '') ? parts[1] : ''
  return province ? { province, district } : null
}

export async function getWelfareBenefits(regionOrLivingSpace) {
  const region = typeof regionOrLivingSpace === 'string'
    ? parseRegion(regionOrLivingSpace)
    : regionOrLivingSpace
  if (!region) throw new Error('대상자의 생활공간에 시·도와 시·군·구를 함께 입력해 주세요.')
  const params = new URLSearchParams()
  params.set('ctpv_name', region.province)
  if (region.district) params.set('sgg_name', region.district)
  const benefits = await apiRequest(`/welfare-benefits${params.size ? `?${params}` : ''}`)
  return benefits.map((benefit) => ({
    id: benefit.id,
    category: benefit.category,
    title: benefit.title,
    description: benefit.description,
    organization: benefit.organization,
    eligibility: benefit.eligibility,
    applicationMethod: benefit.application_method,
    officialUrl: benefit.official_url,
  }))
}
