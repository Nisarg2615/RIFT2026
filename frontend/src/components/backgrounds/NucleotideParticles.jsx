import React, { useMemo } from 'react'
import { motion } from 'framer-motion'

const nucleotides = ['A', 'T', 'C', 'G']

const NucleotideParticles = ({ count = 30 }) => {
  const particles = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      nucleotide: nucleotides[Math.floor(Math.random() * nucleotides.length)],
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 2,
      duration: 6 + Math.random() * 4,
    }))
  }, [count])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute text-dna-cyan font-mono font-bold text-sm opacity-30"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -30, 10, -20, 0],
            x: [0, 20, -20, 10, 0],
            rotate: [0, 120, 240, 360],
            opacity: [0.2, 0.5, 0.3, 0.4, 0.2],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          {particle.nucleotide}
        </motion.div>
      ))}
    </div>
  )
}

export default NucleotideParticles
