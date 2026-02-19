import React from 'react'
import { motion } from 'framer-motion'
import { AlertCircle, X } from 'lucide-react'

function ErrorMessage({ message, onClose }) {
  if (!message) return null

  return (
    <motion.div
      className="glass-card border-2 border-red-500/50 bg-red-500/10 rounded-xl p-4 mb-6"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="text-red-400 font-semibold mb-1">Error</div>
          <div className="text-slate-300 text-sm">{message}</div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  )
}

export default ErrorMessage
