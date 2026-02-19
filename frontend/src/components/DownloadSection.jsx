import React from 'react'
import { motion } from 'framer-motion'
import { Download, Copy, Check } from 'lucide-react'
import GlassCard from './ui/GlassCard'
import { useState } from 'react'

function DownloadSection({ results }) {
  const [copied, setCopied] = useState(false)

  const handleDownloadJSON = () => {
    const json = JSON.stringify(results, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `PharmaGuard_Report_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleCopyJSON = async () => {
    const json = JSON.stringify(results, null, 2)
    try {
      await navigator.clipboard.writeText(json)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      alert('Failed to copy JSON')
    }
  }

  return (
    <GlassCard>
      <div className="flex flex-wrap gap-4 justify-center">
        <motion.button
          className="px-8 py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-dna-cyan to-dna-blue hover:from-dna-blue hover:to-dna-purple transition-all flex items-center gap-2"
          onClick={handleDownloadJSON}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Download className="w-5 h-5" />
          Download JSON Report
        </motion.button>
        <motion.button
          className="px-8 py-4 rounded-xl font-semibold text-white bg-white/10 hover:bg-white/20 border border-white/20 transition-all flex items-center gap-2"
          onClick={handleCopyJSON}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {copied ? (
            <>
              <Check className="w-5 h-5 text-dna-green" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-5 h-5" />
              Copy JSON to Clipboard
            </>
          )}
        </motion.button>
      </div>
    </GlassCard>
  )
}

export default DownloadSection
