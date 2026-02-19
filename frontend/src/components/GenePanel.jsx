import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Dna, AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react'
import GlassCard from './ui/GlassCard'

function GenePanel({ results }) {
  const uniqueGenes = useMemo(() => {
    const genes = {}
    results.forEach(item => {
      const pharmaProfile = item.pharmacogenomic_profile || {}
      const primaryGene = pharmaProfile.primary_gene || 'Unknown'
      const phenotype = pharmaProfile.phenotype || 'Unknown'
      const drugName = item.drug || item.drug_name || 'Unknown'

      if (!genes[primaryGene]) {
        genes[primaryGene] = { phenotype, drug: drugName }
      }
    })
    return genes
  }, [results])

  const getGeneStatus = (geneResult) => {
    const riskLabel = geneResult?.risk_assessment?.risk_label || geneResult?.risk_level || ''
    const risk = (riskLabel || '').toLowerCase()
    
    if (risk === 'toxic' || risk === 'ineffective' || risk === 'contraindicated') {
      return {
        icon: AlertCircle,
        status: 'Action Required',
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/50',
        dot: 'bg-red-400'
      }
    }
    if (risk === 'adjust dosage' || risk === 'moderate') {
      return {
        icon: AlertTriangle,
        status: 'Caution',
        color: 'text-amber-400',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/50',
        dot: 'bg-amber-400'
      }
    }
    return {
      icon: CheckCircle2,
      status: 'Normal',
      color: 'text-dna-green',
      bg: 'bg-dna-green/10',
      border: 'border-dna-green/50',
      dot: 'bg-dna-green'
    }
  }

  return (
    <GlassCard>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-dna-teal to-dna-green flex items-center justify-center">
          <Dna className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Gene Analysis Panel</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(uniqueGenes).map(([gene, info], idx) => {
          const geneResult = results.find(r => {
            const pg = r.pharmacogenomic_profile || {}
            return pg.primary_gene === gene
          })
          
          const status = getGeneStatus(geneResult)
          const StatusIcon = status.icon

          return (
            <motion.div
              key={gene}
              className={`glass-card rounded-xl p-5 border-2 ${status.border} ${status.bg}`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: idx * 0.1 }}
              whileHover={{ scale: 1.05, y: -4 }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="text-2xl font-bold text-white mb-1">{gene}</div>
                  <div className="text-sm text-slate-400">{info.phenotype}</div>
                </div>
                <StatusIcon className={`w-6 h-6 ${status.color}`} />
              </div>
              
              <div className="flex items-center gap-2 mb-3">
                <div className={`w-2 h-2 rounded-full ${status.dot}`} />
                <span className={`text-sm font-medium ${status.color}`}>{status.status}</span>
              </div>
              
              <div className="text-xs text-slate-400 pt-3 border-t border-white/10">
                Affects metabolism of <span className="text-white font-medium">{info.drug}</span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </GlassCard>
  )
}

export default GenePanel
