'use client'

import { Table } from '@/components/ui/table'

const cohortData = [
  { cohort: 'Jan 2024', size: 1200, week1: 95, week2: 87, week3: 78, week4: 72, week5: 68, week6: 65 },
  { cohort: 'Feb 2024', size: 1450, week1: 94, week2: 85, week3: 76, week4: 70, week5: 66, week6: 62 },
  { cohort: 'Mar 2024', size: 1680, week1: 96, week2: 88, week3: 80, week4: 74, week5: 70, week6: 67 },
  { cohort: 'Apr 2024', size: 1820, week1: 97, week2: 90, week3: 82, week4: 76, week5: 72, week6: 69 },
  { cohort: 'May 2024', size: 2100, week1: 98, week2: 91, week3: 84, week4: 78, week5: 74, week6: 71 },
  { cohort: 'Jun 2024', size: 2350, week1: 97, week2: 89, week3: 81, week4: 75, week5: null, week6: null },
]

function getColorClass(value: number | null): string {
  if (value === null) return 'bg-gray-100 dark:bg-gray-800'
  if (value >= 90) return 'bg-green-500 text-white'
  if (value >= 80) return 'bg-green-400 text-white'
  if (value >= 70) return 'bg-yellow-400 text-black'
  if (value >= 60) return 'bg-orange-400 text-white'
  return 'bg-red-400 text-white'
}

export function CohortTable() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-3 font-semibold">Cohort</th>
            <th className="text-right p-3 font-semibold">Size</th>
            <th className="text-center p-3 font-semibold">Week 1</th>
            <th className="text-center p-3 font-semibold">Week 2</th>
            <th className="text-center p-3 font-semibold">Week 3</th>
            <th className="text-center p-3 font-semibold">Week 4</th>
            <th className="text-center p-3 font-semibold">Week 5</th>
            <th className="text-center p-3 font-semibold">Week 6</th>
          </tr>
        </thead>
        <tbody>
          {cohortData.map((row) => (
            <tr key={row.cohort} className="border-b hover:bg-muted/50">
              <td className="p-3 font-medium">{row.cohort}</td>
              <td className="p-3 text-right">{row.size.toLocaleString()}</td>
              <td className="p-2">
                <div className={`rounded text-center py-1 ${getColorClass(row.week1)}`}>
                  {row.week1}%
                </div>
              </td>
              <td className="p-2">
                <div className={`rounded text-center py-1 ${getColorClass(row.week2)}`}>
                  {row.week2}%
                </div>
              </td>
              <td className="p-2">
                <div className={`rounded text-center py-1 ${getColorClass(row.week3)}`}>
                  {row.week3}%
                </div>
              </td>
              <td className="p-2">
                <div className={`rounded text-center py-1 ${getColorClass(row.week4)}`}>
                  {row.week4}%
                </div>
              </td>
              <td className="p-2">
                {row.week5 !== null ? (
                  <div className={`rounded text-center py-1 ${getColorClass(row.week5)}`}>
                    {row.week5}%
                  </div>
                ) : (
                  <div className="rounded text-center py-1 bg-gray-100 dark:bg-gray-800 text-gray-400">
                    -
                  </div>
                )}
              </td>
              <td className="p-2">
                {row.week6 !== null ? (
                  <div className={`rounded text-center py-1 ${getColorClass(row.week6)}`}>
                    {row.week6}%
                  </div>
                ) : (
                  <div className="rounded text-center py-1 bg-gray-100 dark:bg-gray-800 text-gray-400">
                    -
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="mt-6 flex items-center gap-4 text-sm">
        <span className="font-medium">Retention Rate:</span>
        <div className="flex items-center gap-2">
          <div className="w-8 h-4 rounded bg-green-500" />
          <span>90%+</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-4 rounded bg-green-400" />
          <span>80-89%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-4 rounded bg-yellow-400" />
          <span>70-79%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-4 rounded bg-orange-400" />
          <span>60-69%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-4 rounded bg-red-400" />
          <span>&lt;60%</span>
        </div>
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h4 className="font-semibold mb-2">Key Insights</h4>
        <ul className="space-y-1 text-sm text-muted-foreground">
          <li>• Recent cohorts show improved retention rates</li>
          <li>• Week 1 retention consistently above 94%</li>
          <li>• Average 6-week retention rate: 68%</li>
          <li>• May 2024 cohort showing strongest performance</li>
        </ul>
      </div>
    </div>
  )
}
