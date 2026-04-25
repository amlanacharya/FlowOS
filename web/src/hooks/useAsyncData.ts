import { useEffect, useState, type DependencyList } from 'react'
import type { Notice } from '../components/NoticeStack'
import { errorMessage } from '../utils'

type PushNotice = (tone: Notice['tone'], title: string, detail: string) => void

export function useAsyncData<T>(
  loader: () => Promise<T>,
  deps: DependencyList,
  onSuccess: (data: T) => void,
  pushNotice: PushNotice,
  errorTitle: string,
) {
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setLoading(true)
    try {
      onSuccess(await loader())
    } catch (error) {
      pushNotice('error', errorTitle, errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
    // The caller owns dependency selection for loader/onSuccess stability.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { loading, refresh }
}
