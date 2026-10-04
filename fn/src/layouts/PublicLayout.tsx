import { Outlet } from 'react-router'
import { Footer } from './_components/Footer'
import { Header } from './_components/Header'

export default function PublicLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <Header />
      <Outlet />
      <Footer />
    </div>
  )
}
