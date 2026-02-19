import React from 'react'
import { motion } from 'framer-motion'
import { Dna, Sparkles, Zap } from 'lucide-react'
import DNAHelix from './backgrounds/DNAHelix'
import NucleotideParticles from './backgrounds/NucleotideParticles'

const HeroSection = ({ onGetStarted }) => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Background layers */}
      <div className="absolute inset-0 dna-pattern opacity-30" />
      <DNAHelix />
      <NucleotideParticles count={40} />
      
      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Logo/Brand */}
          <motion.div
            className="flex items-center justify-center gap-4 mb-8"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Dna className="w-16 h-16 text-dna-cyan" />
            </motion.div>
            <div className="text-left">
              <h1 className="text-6xl md:text-7xl font-black text-gradient mb-2">
                PharmaGuard
              </h1>
              <p className="text-xl text-slate-400 font-medium">
                AI-Powered Precision Pharmacogenomics
              </p>
            </div>
          </motion.div>
          
          {/* Tagline */}
          <motion.p
            className="text-2xl md:text-3xl text-slate-300 mb-4 font-light max-w-3xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            Transform DNA variant data into{' '}
            <span className="text-gradient-blue font-semibold">personalized drug risk predictions</span>
          </motion.p>
          
          {/* Features */}
          <motion.div
            className="flex flex-wrap items-center justify-center gap-6 mt-12 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            {[
              { icon: Sparkles, text: 'AI-Powered Analysis' },
              { icon: Dna, text: 'Clinical-Grade Accuracy' },
              { icon: Zap, text: 'Real-Time Insights' },
            ].map((feature, i) => (
              <motion.div
                key={i}
                className="glass-card px-6 py-3 rounded-xl flex items-center gap-3"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.7 + i * 0.1 }}
                whileHover={{ scale: 1.05, y: -4 }}
              >
                <feature.icon className="w-5 h-5 text-dna-cyan" />
                <span className="text-slate-200 font-medium">{feature.text}</span>
              </motion.div>
            ))}
          </motion.div>
          
          {/* Get Started Button */}
          {onGetStarted && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
              className="mt-8"
            >
              <motion.button
                onClick={onGetStarted}
                className="px-8 py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-dna-cyan via-dna-purple to-dna-pink hover:from-dna-blue hover:to-dna-purple transition-all flex items-center gap-2 mx-auto"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                animate={{
                  boxShadow: [
                    '0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(139, 92, 246, 0.3)',
                    '0 0 40px rgba(0, 212, 255, 0.8), 0 0 80px rgba(139, 92, 246, 0.5)',
                    '0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(139, 92, 246, 0.3)',
                  ],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <Sparkles className="w-5 h-5" />
                Get Started
              </motion.button>
            </motion.div>
          )}
          
          {/* Scroll indicator */}
          <motion.div
            className="absolute bottom-10 left-1/2 -translate-x-1/2"
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <div className="w-6 h-10 border-2 border-dna-cyan/50 rounded-full flex items-start justify-center p-2">
              <motion.div
                className="w-1.5 h-1.5 bg-dna-cyan rounded-full"
                animate={{ y: [0, 12, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

export default HeroSection
