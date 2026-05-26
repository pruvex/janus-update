import type { BacklogItem } from '@shared/types'
import { Badge } from './Badge'

interface CardProps {
  item: BacklogItem
}

export function Card({ item }: CardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6 hover:border-accent transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">{item.title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{item.id}</p>
        </div>
        <Badge variant={getStatusVariant(item.status)}>{item.status}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Type</p>
          <p className="text-sm font-medium text-foreground">{item.type}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Importance</p>
          <p className="text-sm font-medium text-foreground">{item.importance}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Risk</p>
          <p className="text-sm font-medium text-foreground">{item.implementation_risk}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Effort</p>
          <p className="text-sm font-medium text-foreground">{item.effort}</p>
        </div>
      </div>

      <div className="border-t border-border pt-4 mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Entry Point</p>
            <p className="text-sm font-medium text-foreground">{item.entry_point}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Routing Confidence</p>
            <p className="text-sm font-medium text-foreground">{item.routing_confidence}</p>
          </div>
        </div>
      </div>

      {item.recommendation && (
        <div className="mt-4 p-3 bg-accent rounded">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Recommendation</p>
          <p className="text-sm text-accent-foreground">{item.recommendation}</p>
        </div>
      )}
    </div>
  )
}

function getStatusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'DONE':
      return 'default'
    case 'IN PROGRESS':
      return 'secondary'
    case 'BLOCKED':
      return 'destructive'
    default:
      return 'outline'
  }
}
