'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MapPin, TrendingUp, Users } from 'lucide-react'

// Mock geographic data
const geographicData = [
  { country: 'United States', users: 4532, requests: 125840, revenue: 12500, growth: 15.3 },
  { country: 'United Kingdom', users: 2341, requests: 78920, revenue: 8900, growth: 12.1 },
  { country: 'Germany', users: 1876, requests: 62340, revenue: 7200, growth: 18.5 },
  { country: 'Canada', users: 1523, requests: 51230, revenue: 5800, growth: 10.2 },
  { country: 'France', users: 1342, requests: 45670, revenue: 5100, growth: 8.9 },
  { country: 'Australia', users: 987, requests: 32450, revenue: 3600, growth: 14.7 },
  { country: 'Japan', users: 876, requests: 28900, revenue: 3200, growth: 22.1 },
  { country: 'Netherlands', users: 654, requests: 21890, revenue: 2400, growth: 11.3 },
  { country: 'Brazil', users: 543, requests: 18230, revenue: 1900, growth: 25.8 },
  { country: 'Singapore', users: 432, requests: 14560, revenue: 1600, growth: 19.4 },
]

const topCities = [
  { city: 'San Francisco', country: 'US', users: 1234, percentage: 27.2 },
  { city: 'London', country: 'UK', users: 987, percentage: 42.1 },
  { city: 'Berlin', country: 'DE', users: 756, percentage: 40.3 },
  { city: 'Toronto', country: 'CA', users: 654, percentage: 42.9 },
  { city: 'Paris', country: 'FR', users: 543, percentage: 40.5 },
]

function getColorIntensity(value: number, max: number): string {
  const intensity = Math.floor((value / max) * 100)
  if (intensity >= 80) return 'bg-blue-600 dark:bg-blue-500'
  if (intensity >= 60) return 'bg-blue-500 dark:bg-blue-400'
  if (intensity >= 40) return 'bg-blue-400 dark:bg-blue-300'
  if (intensity >= 20) return 'bg-blue-300 dark:bg-blue-200'
  return 'bg-blue-200 dark:bg-blue-100'
}

export function GeographicMap() {
  const maxUsers = Math.max(...geographicData.map((d) => d.users))

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Countries</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">42</div>
            <p className="text-xs text-muted-foreground">
              Active in the last 30 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Region</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">North America</div>
            <p className="text-xs text-muted-foreground">
              47.3% of total traffic
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fastest Growing</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Brazil</div>
            <p className="text-xs text-muted-foreground">
              +25.8% month over month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Map Visualization (Simplified) */}
      <Card>
        <CardHeader>
          <CardTitle>Geographic Distribution</CardTitle>
          <CardDescription>
            User activity by country (top 10)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {geographicData.map((country) => (
              <div key={country.country} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{country.country}</span>
                  <span className="text-muted-foreground">
                    {country.users.toLocaleString()} users
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getColorIntensity(
                        country.users,
                        maxUsers
                      )} transition-all flex items-center justify-end pr-2`}
                      style={{
                        width: `${(country.users / maxUsers) * 100}%`,
                      }}
                    >
                      <span className="text-xs text-white font-medium">
                        {((country.users / maxUsers) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground whitespace-nowrap">
                    {country.growth > 0 ? '+' : ''}
                    {country.growth}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Stats Table */}
      <Card>
        <CardHeader>
          <CardTitle>Country Statistics</CardTitle>
          <CardDescription>
            Detailed breakdown of activity by country
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold">Country</th>
                  <th className="text-right p-3 font-semibold">Users</th>
                  <th className="text-right p-3 font-semibold">Requests</th>
                  <th className="text-right p-3 font-semibold">Revenue</th>
                  <th className="text-right p-3 font-semibold">Growth</th>
                </tr>
              </thead>
              <tbody>
                {geographicData.map((country, i) => (
                  <tr key={country.country} className="border-b hover:bg-muted/50">
                    <td className="p-3 font-medium">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground text-xs">
                          #{i + 1}
                        </span>
                        {country.country}
                      </div>
                    </td>
                    <td className="p-3 text-right">
                      {country.users.toLocaleString()}
                    </td>
                    <td className="p-3 text-right">
                      {country.requests.toLocaleString()}
                    </td>
                    <td className="p-3 text-right">
                      ${country.revenue.toLocaleString()}
                    </td>
                    <td className="p-3 text-right">
                      <span
                        className={
                          country.growth > 15
                            ? 'text-green-600 dark:text-green-400'
                            : country.growth > 0
                            ? 'text-blue-600 dark:text-blue-400'
                            : 'text-red-600 dark:text-red-400'
                        }
                      >
                        {country.growth > 0 ? '+' : ''}
                        {country.growth}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Top Cities */}
      <Card>
        <CardHeader>
          <CardTitle>Top Cities</CardTitle>
          <CardDescription>
            Most active cities by user count
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topCities.map((city, i) => (
              <div key={city.city} className="flex items-center gap-4">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-sm font-semibold text-blue-600 dark:text-blue-400">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium">
                    {city.city}, {city.country}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {city.users.toLocaleString()} users • {city.percentage}% of
                    country
                  </div>
                </div>
                <div className="text-right">
                  <div className="h-2 w-24 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500"
                      style={{ width: `${city.percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Regional Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Regional Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">North America</h4>
              <div className="text-2xl font-bold">47.3%</div>
              <p className="text-sm text-muted-foreground">
                Highest revenue per user: $8.23
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Europe</h4>
              <div className="text-2xl font-bold">34.8%</div>
              <p className="text-sm text-muted-foreground">
                Most active region with 6,213 users
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Asia Pacific</h4>
              <div className="text-2xl font-bold">12.6%</div>
              <p className="text-sm text-muted-foreground">
                Fastest growing: +22.1% this month
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Latin America</h4>
              <div className="text-2xl font-bold">5.3%</div>
              <p className="text-sm text-muted-foreground">
                Emerging market with high engagement
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
