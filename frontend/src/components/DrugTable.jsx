import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Zap, CheckCircle2, Info } from 'lucide-react'
import GlassCard from './ui/GlassCard'

function DrugTable({ results }) {
  const getRiskIcon = (riskLabel) => {
    const risk = (riskLabel || '').toLowerCase()
    if (risk === 'toxic' || risk === 'ineffective' || risk === 'contraindicated') {
      return { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/50' }
    }
    if (risk === 'adjust dosage' || risk === 'moderate') {
      return { icon: Zap, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/50' }
    }
    return { icon: CheckCircle2, color: 'text-dna-green', bg: 'bg-dna-green/10', border: 'border-dna-green/50' }
  }

  return (
    <GlassCard>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-dna-purple to-dna-pink flex items-center justify-center">
          <Info className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Drug Risk Assessment</h2>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-4 px-4 text-sm font-semibold text-slate-300">Drug Name</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-slate-300">Risk Level</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-slate-300">Recommendation</th>
              <th className="text-left py-4 px-4 text-sm font-semibold text-slate-300">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {results.map((item, idx) => {
              const drugName = item.drug || item.drug_name || 'Unknown'
              const riskLabel = item.risk_assessment?.risk_label || item.risk_level || 'Unknown'
              const clinicalRec = item.clinical_recommendation || {}
              const recText = clinicalRec.action || clinicalRec.monitoring || 'See details'
              const evidenceLevel = item.evidence_score?.evidence_level || 'A'
              
              const riskIcon = getRiskIcon(riskLabel)
              const Icon = riskIcon.icon

              return (
                <motion.tr
                  key={idx}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.05 }}
                  whileHover={{ x: 4 }}
                >
                  <td className="py-4 px-4">
                    <span className="font-semibold text-white">{drugName}</span>
                  </td>
                  <td className="py-4 px-4">
                    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${riskIcon.bg} ${riskIcon.border} border`}>
                      <Icon className={`w-4 h-4 ${riskIcon.color}`} />
                      <span className={`text-sm font-medium ${riskIcon.color}`}>{riskLabel}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-slate-300">{recText}</td>
                  <td className="py-4 px-4">
                    <span className="px-2 py-1 rounded text-xs font-semibold bg-dna-cyan/20 text-dna-cyan border border-dna-cyan/50">
                      CPIC Level {evidenceLevel}
                    </span>
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </GlassCard>
  )
}

export default DrugTable
