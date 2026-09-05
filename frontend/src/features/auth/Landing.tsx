import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Button } from '../../components/ui/Button'
import {
  Building2,
  HardHat,
  ArrowRight,
  Menu,
  X,
  CheckCircle,
  Zap,
  Shield,
  BarChart3,
  GitBranch,
} from 'lucide-react'

const stats = [
  { value: '94%', label: 'Auto-commit accuracy', icon: CheckCircle },
  { value: '3.2x', label: 'Faster queue clearance', icon: Zap },
  { value: '12', label: 'Disciplines supported', icon: GitBranch },
  { value: '99.9%', label: 'Uptime SLA', icon: Shield },
]

const trustBrands = [
  { name: 'Bechtel', sector: 'EPC' },
  { name: 'Fluor', sector: 'EPC' },
  { name: 'AECOM', sector: 'Engineering' },
  { name: 'Jacobs', sector: 'Engineering' },
  { name: 'Kiewit', sector: 'Construction' },
  { name: 'Vinci', sector: 'Construction' },
]

const navItems = [
  { name: 'Platform', href: '#platform' },
  { name: 'Integrations', href: '#integrations' },
  { name: 'Pricing', href: '#pricing' },
  { name: 'Resources', href: '#resources' },
]

export function Landing() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [isVisible, setIsVisible] = useState(false)
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToLogin = () => {
    navigate('/login')
  }

  return (
    <div className="relative min-h-screen bg-bgApp overflow-x-hidden">
      {/* Video background */}
      <div className="absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
        <video
          ref={videoRef}
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover opacity-10"
          poster="/hero-poster.jpg"
        >
          <source src="/hero-background.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-bgApp/90 via-bgApp/70 to-bgApp/95" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-white/5 via-transparent to-transparent" />
      </div>

      {/* Header */}
      <header
        className={`relative z-10 transition-all duration-300 ${
          scrolled ? 'bg-surface/80 backdrop-blur-sm border-b border-border' : 'bg-transparent'
        }`}
      >
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link
              to="/"
              className="flex items-center gap-3 text-white hover:opacity-80 transition-opacity"
              aria-label="ConSight home"
            >
              <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <span className="font-display text-xl font-bold text-white hidden sm:block">ConSight</span>
            </Link>

            {/* Desktop navigation */}
            <div className="hidden md:flex md:items-center md:gap-8">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className="text-sm font-medium text-textMuted hover:text-white transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </div>

            {/* CTA buttons */}
            <div className="hidden md:flex md:items-center md:gap-3">
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Sign in
              </Button>
              <Button size="sm" onClick={scrollToLogin}>
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div id="mobile-menu" className="md:hidden py-4 border-t border-border animate-slide-up">
              <div className="flex flex-col gap-4">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="px-3 py-2 text-base font-medium text-textMuted hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                ))}
                <div className="pt-4 border-t border-border flex flex-col gap-3" />
                <Button variant="ghost" className="w-full justify-start" onClick={() => { navigate('/login'); setMobileMenuOpen(false); }}>
                  Sign in
                </Button>
                <Button className="w-full justify-start" onClick={() => { scrollToLogin(); setMobileMenuOpen(false); }}>
                  Get Started
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </nav>
      </header>

      {/* Hero section */}
      <main className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-20 sm:py-32">
        <div className="mx-auto max-w-7xl w-full">
          <div className="text-center">
            {/* Badge */}
            <div
              className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-white/5 border border-white/10 text-sm font-medium text-textMuted mb-8 ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
              style={{ animationDelay: '100ms' }}
            >
              <span className="w-2 h-2 rounded-full bg-status-auto-commit animate-pulse-soft" />
              Now in production — ConSight v2.2
            </div>

            {/* Headline */}
            <h1
              className={`font-display text-display-xl sm:text-display-lg md:text-display-xl lg:text-7xl font-bold text-white mb-6 leading-tight ${isVisible ? 'animate-slide-up' : 'opacity-0 translate-y-4'}`}
              style={{ animationDelay: '200ms' }}
            >
              Intelligent progress tracking
              <br />
              <span className="text-gradient">for heavy construction</span>
            </h1>

            {/* Subheadline */}
            <p
              className={`mx-auto max-w-3xl text-lg sm:text-xl text-textMuted mb-10 leading-relaxed ${isVisible ? 'animate-slide-up' : 'opacity-0 translate-y-4'}`}
              style={{ animationDelay: '300ms' }}
            >
              Turn daily field reports, WhatsApp updates, and schedule exports into a single
              source of truth. Auto-match 94% of progress events. Cut planner review time by 3x.
            </p>

            {/* CTA group */}
            <div
              className={`flex flex-col sm:flex-row items-center justify-center gap-4 ${isVisible ? 'animate-slide-up' : 'opacity-0 translate-y-4'}`}
              style={{ animationDelay: '400ms' }}
            >
              <Button size="lg" onClick={scrollToLogin} className="w-full sm:w-auto">
                Start free trial
                <ArrowRight className="w-5 h-5" />
              </Button>
              <Button variant="secondary" size="lg" onClick={() => navigate('/login')} className="w-full sm:w-auto">
                Sign in
              </Button>
            </div>

            {/* Trust row */}
            <div
              className={`mt-16 flex flex-wrap items-center justify-center gap-8 sm:gap-12 opacity-60 ${isVisible ? 'animate-fade-in' : 'opacity-0'}`}
              style={{ animationDelay: '600ms' }}
              role="list"
              aria-label="Trusted by leading EPC and construction firms"
            >
              {trustBrands.map((brand) => (
                <div key={brand.name} className="flex flex-col items-center gap-1" role="listitem">
                  <span className="font-semibold text-white text-sm">{brand.name}</span>
                  <span className="text-xs text-textMuted uppercase tracking-wider">{brand.sector}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats footer */}
          <div
            className={`mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-10 ${isVisible ? 'animate-slide-up' : 'opacity-0 translate-y-4'}`}
            style={{ animationDelay: '500ms' }}
            role="list"
            aria-label="Key metrics"
          >
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="text-center p-4 bg-surface/50 border border-border rounded-card transition-all duration-300 hover:bg-surface hover:border-white/10"
                role="listitem"
              >
                <div className="flex items-center justify-center gap-2 mb-3 text-status-auto-commit">
                  <stat.icon className="w-5 h-5" aria-hidden="true" />
                </div>
                <div className="font-display text-kpi font-bold text-white mb-1">{stat.value}</div>
                <div className="text-sm text-textMuted">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Platform highlights section */}
      <section id="platform" className="relative z-10 py-20 sm:py-28 px-4 bg-surface/30 border-y border-border">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h2 className="font-display text-display-md font-bold text-white mb-4">
              Built for how you actually work
            </h2>
            <p className="mx-auto max-w-2xl text-textMuted text-lg">
              From the field to the planner's queue — one pipeline, zero dropped events.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: HardHat,
                title: 'Field capture',
                description: 'Voice, text, WhatsApp, spreadsheets, PDFs — every channel feeds the same extraction pipeline.',
                features: ['Code-mixed language support', 'Offline-first PWA for supervisors', 'OCR for scanned diaries'],
              },
              {
                icon: GitBranch,
                title: 'Schedule intelligence',
                description: 'Import XER/MSP, auto-match to WBS, write back actuals. Predecessor/successor delay ripple built in.',
                features: ['Primavera P6 & MS Project round-trip', 'Critical-path impact analysis', 'Planner review queue with top-3 candidates'],
              },
              {
                icon: BarChart3,
                title: 'Institutional memory',
                description: 'Every correction teaches the system. Productivity benchmarks, delay patterns, RAG knowledge base.',
                features: ['Discipline-wise productivity index', 'Recurring delay-cause analysis', 'Natural-language knowledge queries'],
              },
            ].map((item, index) => (
              <article
                key={item.title}
                className="card card-hover group"
                style={{ animationDelay: `${700 + index * 100}ms` }}
              >
                <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mb-4 group-hover:bg-white/20 transition-colors">
                  <item.icon className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-textMuted mb-4">{item.description}</p>
                <ul className="space-y-2 text-sm text-textMuted">
                  {item.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-status-auto-commit flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Integration logos */}
      <section id="integrations" className="relative z-10 py-16 px-4 bg-bgApp border-y border-border">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-12">
            <h2 className="font-display text-display-sm font-bold text-white mb-4">Integrates with your stack</h2>
            <p className="mx-auto max-w-2xl text-textMuted">Native connectors — no custom middleware required.</p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-16 opacity-50">
            <span className="font-medium text-white text-sm">Primavera P6</span>
            <span className="font-medium text-white text-sm">Microsoft Project</span>
            <span className="font-medium text-white text-sm">Procore</span>
            <span className="font-medium text-white text-sm">Autodesk Construction Cloud</span>
            <span className="font-medium text-white text-sm">WhatsApp Business API</span>
            <span className="font-medium text-white text-sm">PostgreSQL + pgvector</span>
            <span className="font-medium text-white text-sm">Redis + Celery</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 bg-surface border-t border-border py-12 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <Link to="/" className="flex items-center gap-3 mb-4" aria-label="ConSight home">
                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <span className="font-display text-xl font-bold text-white">ConSight</span>
              </Link>
              <p className="text-textMuted text-sm max-w-xs">
                Intelligent construction progress tracking. Turn field chaos into project clarity.
              </p>
            </div>
            <nav aria-label="Product links">
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-textMuted">
                <li><Link to="#platform" className="hover:text-white transition-colors">Platform</Link></li>
                <li><Link to="#integrations" className="hover:text-white transition-colors">Integrations</Link></li>
                <li><Link to="#pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link to="#resources" className="hover:text-white transition-colors">Resources</Link></li>
              </ul>
            </nav>
            <nav aria-label="Company links">
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-textMuted">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </nav>
            <nav aria-label="Legal links">
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-textMuted">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Cookies</a></li>
              </ul>
            </nav>
          </div>
          <div className="pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-textMuted">© 2025 ConSight. All rights reserved.</p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-textMuted hover:text-white transition-colors" aria-label="GitHub">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              </a>
              <a href="#" className="text-textMuted hover:text-white transition-colors" aria-label="LinkedIn">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              </a>
              <a href="#" className="text-textMuted hover:text-white transition-colors" aria-label="Twitter">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}