import type { ReactNode } from 'react'
import type { BacklogItem } from '@shared/types'

export const TYPE_COLUMNS = [
  'BUG',
  'ÄNDERUNG',
  'ERWEITERUNG',
  'VERBESSERUNG',
  'TECHNISCHE SCHULDEN',
  'UNKLAR',
  'SPEC FEATURE',
] as const

export const COLUMN_TYPE_MAPPING: Record<string, string> = {
  BUG: 'BUG',
  ÄNDERUNG: 'CHANGE',
  ERWEITERUNG: 'ENHANCEMENT',
  VERBESSERUNG: 'IMPROVEMENT',
  'TECHNISCHE SCHULDEN': 'TECH_DEBT',
  UNKLAR: 'UNCLEAR',
  'SPEC FEATURE': 'SPEC FEATURE',
}

interface TypeKanbanBoardProps<T> {
  items: T[]
  getItemType: (item: T) => string
  getItemKey: (item: T) => string
  renderItem: (item: T) => ReactNode
  emptyText?: string
}

export function getBacklogItemType(item: BacklogItem): string {
  return item.type
}

export function TypeKanbanBoard<T>({
  items,
  getItemType,
  getItemKey,
  renderItem,
  emptyText = 'No items',
}: TypeKanbanBoardProps<T>) {
  const getColumnItems = (columnType: string) => {
    const itemType = COLUMN_TYPE_MAPPING[columnType] || columnType
    return items.filter((item) => getItemType(item) === itemType)
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="h-full w-full grid grid-cols-7 gap-3">
        {TYPE_COLUMNS.map((column) => {
          const columnItems = getColumnItems(column)
          return (
            <div key={column} className="flex flex-col bg-card border border-border rounded-lg min-w-0">
              <div className="p-3 border-b border-border bg-muted/50">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-foreground text-sm truncate">{column}</h3>
                  <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full flex-shrink-0">
                    {columnItems.length}
                  </span>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {columnItems.map((item) => (
                  <div key={getItemKey(item)}>{renderItem(item)}</div>
                ))}
                {columnItems.length === 0 && (
                  <div className="text-center text-muted-foreground text-xs py-6">
                    {emptyText}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
