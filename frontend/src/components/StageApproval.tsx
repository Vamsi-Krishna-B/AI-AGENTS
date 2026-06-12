import { approveStage } from '../api/client'

interface Props {
  jobId: string
  stage: string
  status: string
  onApproved: () => void
}

export function StageApproval({ jobId, stage, status, onApproved }: Props) {
  if (status !== 'awaiting_approval') return null

  const handleApprove = async () => {
    await approveStage(jobId, stage)
    onApproved()
  }

  return (
    <button
      onClick={handleApprove}
      className="mt-1 px-3 py-1 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition"
    >
      Approve {stage}
    </button>
  )
}
