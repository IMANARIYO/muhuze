export interface User {
  id: number
  name: string
  email: string
  role: string
  /** Shop name, when the user sells on Muhuze. */
  shop?: string
  referralCode: string
  permissions: string[]
}
