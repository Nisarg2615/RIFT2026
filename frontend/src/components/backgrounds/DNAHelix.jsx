import React from 'react'
import { motion } from 'framer-motion'

const DNAHelix = ({ className = '' }) => {
  const helixVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: 20,
        repeat: Infinity,
        ease: 'linear',
      },
    },
  }

  return (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      <motion.svg
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] opacity-20"
        viewBox="0 0 400 400"
        variants={helixVariants}
        animate="animate"
      >
        {/* DNA Double Helix Structure */}
        <g>
          {/* Left strand */}
          <motion.path
            d="M 100 50 Q 120 100, 100 150 Q 80 200, 100 250 Q 120 300, 100 350"
            stroke="url(#dnaGradient1)"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2, ease: 'easeInOut' }}
          />
          {/* Right strand */}
          <motion.path
            d="M 300 50 Q 280 100, 300 150 Q 320 200, 300 250 Q 280 300, 300 350"
            stroke="url(#dnaGradient2)"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2, ease: 'easeInOut', delay: 0.2 }}
          />
          {/* Base pairs */}
          {[...Array(8)].map((_, i) => {
            const y = 50 + i * 40
            const x1 = 100 + Math.sin((i * Math.PI) / 4) * 20
            const x2 = 300 - Math.sin((i * Math.PI) / 4) * 20
            return (
              <motion.line
                key={i}
                x1={x1}
                y1={y}
                x2={x2}
                y2={y}
                stroke="url(#dnaGradient3)"
                strokeWidth="2"
                opacity={0.6}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              />
            )
          })}
        </g>
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="dnaGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00D4FF" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#EC4899" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="dnaGradient2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EC4899" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#00D4FF" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="dnaGradient3" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#00D4FF" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#EC4899" stopOpacity="0.6" />
          </linearGradient>
        </defs>
      </motion.svg>
    </div>
  )
}

export default DNAHelix
