'use client'

import { Bell, LogOut, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/store/authStore'
import { useRouter } from 'next/navigation'

export function Header() {
  const { user, clearAuth } = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    clearAuth()
    router.push('/auth/login')
  }

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6 dark:bg-gray-900 dark:border-gray-800">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Admin Dashboard</h2>
      </div>
      
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <User className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <div className="px-2 py-1.5">
              <p className="text-sm font-medium">{user?.username || 'Admin'}</p>
              <p className="text-xs text-muted-foreground">{user?.email || ''}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/dashboard')}>
              <User className="mr-2 h-4 w-4" />
              User Dashboard
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
