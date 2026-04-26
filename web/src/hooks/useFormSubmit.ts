import { useState, useCallback } from 'react'
import { errorMessage } from '../utils'
import type { Notice } from '../components/NoticeStack'

type FormSubmitHandler = () => Promise<any>

export function useFormSubmit(
  onSubmit: FormSubmitHandler,
  onSuccess: () => void | Promise<void>,
  pushNotice: (tone: Notice['tone'], title: string, detail: string) => void,
  successTitle: string = 'Success',
  successMessage: string = 'Operation completed successfully',
  errorTitle: string = 'Operation failed',
) {
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = useCallback(async () => {
    setSubmitting(true)
    try {
      await onSubmit()
      pushNotice('success', successTitle, successMessage)
      await onSuccess()
    } catch (error) {
      pushNotice('error', errorTitle, errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }, [onSubmit, onSuccess, pushNotice, successTitle, successMessage, errorTitle])

  return { submitting, handleSubmit }
}
