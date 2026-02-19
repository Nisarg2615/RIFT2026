import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

const GlassCard = ({ 
  children, 
  className = '', 
  hover = true,
  delay = 0,
  ...props 
}) => {
  return (
    <motion.div
      className={cn(
        'glass-card rounded-2xl p-6',
        hover && 'hover:bg-white/10 transition-all duration-300',
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={hover ? { scale: 1.02, y: -4 } : {}}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default GlassCard
