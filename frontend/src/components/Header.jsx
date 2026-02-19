import React from 'react'
import { motion } from 'framer-motion'
import { Dna, History, FileText, LayoutDashboard } from 'lucide-react'

function Header({ onHistoryClick, onDashboardClick }) {
  return (
    <motion.header
      className="sticky top-0 z-50 glass-dark border-b border-white/10"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <motion.a
            href="#"
            className="flex items-center gap-3 group"
            whileHover={{ scale: 1.05 }}
          >
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Dna className="w-8 h-8 text-dna-cyan" />
            </motion.div>
            <div>
              <h1 className="text-xl font-bold text-gradient">PharmaGuard AI</h1>
              <p className="text-xs text-slate-400">Precision Medicine Platform</p>
            </div>
          </motion.a>
          
          {/* Navigation */}
          <nav className="flex items-center gap-2">
            <motion.button
              onClick={onDashboardClick}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span className="text-sm font-medium">Dashboard</span>
            </motion.button>
            <motion.button
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <FileText className="w-4 h-4" />
              <span className="text-sm font-medium">Reports</span>
            </motion.button>
            <motion.button
              onClick={onHistoryClick}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <History className="w-4 h-4" />
              <span className="text-sm font-medium">History</span>
            </motion.button>
            <motion.div
              className="w-8 h-8 rounded-full bg-gradient-to-r from-dna-cyan to-dna-purple flex items-center justify-center ml-2"
              whileHover={{ scale: 1.1 }}
            >
              <span className="text-white text-sm font-semibold">U</span>
            </motion.div>
          </nav>
        </div>
      </div>
    </motion.header>
  )
}

export default Header
