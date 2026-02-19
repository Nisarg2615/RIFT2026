import React from 'react'
import { motion } from 'framer-motion'
import { Dna, Sparkles } from 'lucide-react'
import GlassCard from './ui/GlassCard'

function LoadingState() {
  return (
    <GlassCard>
      <div className="flex flex-col items-center justify-center py-20">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="mb-8"
        >
          <Dna className="w-16 h-16 text-dna-cyan" />
        </motion.div>
        
        <motion.div
          className="flex items-center gap-2 mb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Sparkles className="w-5 h-5 text-dna-purple" />
          <h3 className="text-xl font-semibold text-white">
            Analyzing your genetic data...
          </h3>
        </motion.div>
        
        <p className="text-slate-400 text-center max-w-md">
          Generating clinical recommendations using AI-powered pharmacogenomic analysis
        </p>
        
        {/* Loading dots */}
        <div className="flex gap-2 mt-8">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-3 h-3 rounded-full bg-dna-cyan"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </GlassCard>
  )
}

export default LoadingState
