import React from 'react'
import { motion } from 'framer-motion'

const GenomeScanAnimation = ({ isActive = false }) => {
  if (!isActive) return null

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Scanning line */}
      <motion.div
        className="absolute top-0 bottom-0 w-1 bg-gradient-to-b from-transparent via-dna-cyan to-transparent opacity-60"
        initial={{ left: '-10px' }}
        animate={{ left: '100%' }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'linear',
        }}
        style={{
          boxShadow: '0 0 20px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 212, 255, 0.4)',
        }}
      />
      
      {/* Scanning particles */}
      {[...Array(5)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 bg-dna-cyan rounded-full"
          style={{
            top: `${20 + i * 15}%`,
            boxShadow: '0 0 10px rgba(0, 212, 255, 0.8)',
          }}
          initial={{ left: '-10px', opacity: 0 }}
          animate={{ 
            left: '100%',
            opacity: [0, 1, 1, 0],
          }}
          transition={{
            duration: 3,
            delay: i * 0.2,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      ))}
      
      {/* Grid overlay */}
      <div className="absolute inset-0 biotech-grid opacity-20" />
    </div>
  )
}

export default GenomeScanAnimation
