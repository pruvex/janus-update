import { useEffect, useState } from 'react'
import { fetchBacklogItems } from '../lib/api'
import type { BacklogItem } from '@shared/types'
import { Card } from '../components/Card'
import { Loader2 } from 'lucide-react'

export function HistoryView() {
  const [items, setItems] = useState<BacklogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      setLoading(true)
      const response = await fetchBacklogItems()
      const historyItems = response.items.filter(item => item.status === 'DONE')
      setItems(historyItems)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load items')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground">History</h2>
        <p className="text-muted-foreground mt-2">{items.length} completed items</p>
      </div>

      <div className="grid gap-6">
        {items.map((item) => (
          <Card key={item.id} item={item} />
        ))}
      </div>
    </div>
  )
}
