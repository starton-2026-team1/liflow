const emailPattern = /^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$/i

export function getEmailError(value) {
  const email = value.trim()

  if (!email) {
    return '이메일을 입력해 주세요.'
  }

  if (email !== value || email.length > 254) {
    return '올바른 이메일 주소를 입력해 주세요.'
  }

  const [localPart, domain, ...extraParts] = email.split('@')

  if (!localPart || !domain || extraParts.length > 0 || localPart.length > 64) {
    return '올바른 이메일 주소를 입력해 주세요.'
  }

  if (localPart.startsWith('.') || localPart.endsWith('.') || localPart.includes('..')) {
    return '올바른 이메일 주소를 입력해 주세요.'
  }

  const domainParts = domain.split('.')
  const topLevelDomain = domainParts.at(-1)

  if (
    !emailPattern.test(email) ||
    domainParts.some((part) => !part || part.length > 63) ||
    !topLevelDomain ||
    topLevelDomain.length < 2 ||
    !/^[A-Z]+$/i.test(topLevelDomain)
  ) {
    return '올바른 이메일 주소를 입력해 주세요.'
  }

  return ''
}

export function isValidEmail(value) {
  return getEmailError(value) === ''
}

export function shouldAutoConfirmEmail(value) {
  if (!isValidEmail(value)) {
    return false
  }

  const topLevelDomain = value.slice(value.lastIndexOf('.') + 1).toLowerCase()
  return topLevelDomain !== 'co'
}
