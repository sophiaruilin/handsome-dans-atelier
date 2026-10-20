// Mirrors password_problems() in backend/auth.py. The back end is the real check; this gives live feedback.
export const PASSWORD_MIN = 12

export interface Rule {
  label: string
  ok: boolean
}

export function passwordRules(password: string, email: string, firstName: string, lastName: string): Rule[] {
  const lower = password.toLowerCase()
  const personal = [email.split('@')[0], firstName, lastName].filter((p) => p.trim().length >= 3)
  return [
    { label: `At least ${PASSWORD_MIN} characters`, ok: password.length >= PASSWORD_MIN },
    { label: 'At least one letter and one number', ok: /[A-Za-z]/.test(password) && /\d/.test(password) },
    {
      label: "Doesn't include your name or email",
      ok: password.length > 0 && !personal.some((p) => lower.includes(p.trim().toLowerCase())),
    },
  ]
}
