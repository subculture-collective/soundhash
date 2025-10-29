'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { useTheme } from 'next-themes'
import { Moon, Sun, Menu } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useState } from 'react'
import { cn } from '@/lib/utils'

export function Header() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const { isAuthenticated, user, clearAuth } = useAuthStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isAuthPage = pathname?.startsWith('/auth')

  const handleLogout = () => {
    clearAuth()
    window.location.href = '/'
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <span className="text-xl font-bold hidden sm:inline">SoundHash</span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {!isAuthPage && !isAuthenticated && (
            <>
              <Link
                href="#features"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Features
              </Link>
              <Link
                href="#how-it-works"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                How It Works
              </Link>
            </>
          )}
          {isAuthenticated && (
            <>
              <Link
                href="/dashboard"
                className={cn(
                  "text-sm font-medium transition-colors",
                  pathname === '/dashboard'
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Dashboard
              </Link>
              <Link
                href="/matches"
                className={cn(
                  "text-sm font-medium transition-colors",
                  pathname === '/matches'
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Matches
              </Link>
            </>
          )}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Auth Buttons */}
          {!isAuthPage && (
            <>
              {isAuthenticated ? (
                <div className="hidden md:flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {user?.username}
                  </span>
                  <Button variant="outline" size="sm" onClick={handleLogout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <div className="hidden md:flex items-center gap-2">
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/auth/login">Sign In</Link>
                  </Button>
                  <Button size="sm" asChild>
                    <Link href="/auth/register">Get Started</Link>
                  </Button>
                </div>
              )}
            </>
          )}

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t">
          <nav className="container flex flex-col gap-2 py-4 px-4">
            {!isAuthPage && !isAuthenticated && (
              <>
                <Link
                  href="#features"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Features
                </Link>
                <Link
                  href="#how-it-works"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  How It Works
                </Link>
              </>
            )}
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <Link
                  href="/matches"
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Matches
                </Link>
                <div className="pt-2 border-t">
                  <span className="text-sm text-muted-foreground block mb-2">
                    {user?.username}
                  </span>
                  <Button variant="outline" size="sm" onClick={handleLogout} className="w-full">
                    Logout
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-2 border-t">
                <Button variant="outline" size="sm" asChild className="w-full">
                  <Link href="/auth/login" onClick={() => setMobileMenuOpen(false)}>
                    Sign In
                  </Link>
                </Button>
                <Button size="sm" asChild className="w-full">
                  <Link href="/auth/register" onClick={() => setMobileMenuOpen(false)}>
                    Get Started
                  </Link>
                </Button>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
