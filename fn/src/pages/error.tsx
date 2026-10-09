import { useEffect } from 'react'
import { useRouteError } from 'react-router'
import { Button } from '@/components/ui/button'

const KEY = 'reloaded-at'

// A page's code could not be downloaded: the dev server restarted or a new version was deployed
// while this tab was open, so the file names it knows are out of date.
const isLoadError = (error: unknown) =>
  error instanceof TypeError && /import/i.test(error.message) && /module/i.test(error.message)

export default function RouteError() {
  const outdated = isLoadError(useRouteError())

  useEffect(() => {
    // Reload once to pick up the current files; the time check stops a reload loop.
    if (!outdated || Date.now() - Number(sessionStorage.getItem(KEY)) < 10_000) return
    sessionStorage.setItem(KEY, String(Date.now()))
    location.reload()
  }, [outdated])

  return (
    <div className="grid min-h-svh place-items-center px-4 text-center">
      <div className="space-y-4">
        <p className="font-heading text-3xl font-bold">{outdated ? 'This page was updated' : 'Something went wrong'}</p>
        <p className="text-muted-foreground">
          {outdated ? 'Reload to get the latest version.' : 'Please reload the page and try again.'}
        </p>
        <Button onClick={() => location.reload()}>Reload</Button>
      </div>
    </div>
  )
}
