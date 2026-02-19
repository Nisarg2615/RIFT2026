import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, TrendingUp, Dna, Activity } from 'lucide-react'
import GlassCard from './ui/GlassCard'

function SummaryDashboard({ results }) {
  const stats = useMemo(() => {
    let highRiskCount = 0
    let mediumRiskCount = 0
    const genes = new Set()

    results.forEach(item => {
      const riskLabel = item.risk_assessment?.risk_label || item.risk_level || ''
      const pharmaProfile = item.pharmacogenomic_profile || {}
      const primaryGene = pharmaProfile.primary_gene || 'Unknown'

      genes.add(primaryGene)

      const risk = (riskLabel || '').toLowerCase()
      if (risk === 'toxic' || risk === 'ineffective' || risk === 'contraindicated') {
        highRiskCount++
      } else if (risk === 'adjust dosage' || risk === 'moderate') {
        mediumRiskCount++
      }
    })

    const overallRisk = highRiskCount > 0 ? 'High' : mediumRiskCount > 0 ? 'Medium' : 'Low'
    return { genes, highRiskCount, mediumRiskCount, overallRisk }
  }, [results])

  const getRiskWidgetClass = () => {
    if (stats.overallRisk === 'High') return 'border-red-500/50 bg-red-500/10'
    if (stats.overallRisk === 'Medium') return 'border-amber-500/50 bg-amber-500/10'
    return 'border-dna-green/50 bg-dna-green/10'
  }

  const getRiskDisplay = () => {
    if (stats.overallRisk === 'High') {
      return { 
        icon: AlertTriangle, 
        text: 'HIGH', 
        detail: `${stats.highRiskCount} critical drug(s)`,
        color: 'text-red-400'
      }
    }
    if (stats.overallRisk === 'Medium') {
      return { 
        icon: TrendingUp, 
        text: 'MEDIUM', 
        detail: `${stats.mediumRiskCount} medications need adjustment`,
        color: 'text-amber-400'
      }
    }
    return { 
      icon: Activity, 
      text: 'LOW', 
      detail: 'All medications safe',
      color: 'text-dna-green'
    }
  }

  const riskDisplay = getRiskDisplay()
  const RiskIcon = riskDisplay.icon

  const widgets = [
    {
      label: 'Overall Risk Level',
      value: riskDisplay.text,
      detail: riskDisplay.detail,
      icon: RiskIcon,
      color: riskDisplay.color,
      className: getRiskWidgetClass(),
      delay: 0,
    },
    {
      label: 'Genes Analyzed',
      value: stats.genes.size,
      detail: 'Pharmacogenomic markers',
      icon: Dna,
      color: 'text-dna-cyan',
      delay: 0.1,
    },
    {
      label: 'Drugs Analyzed',
      value: results.length,
      detail: 'Medications reviewed',
      icon: Activity,
      color: 'text-dna-purple',
      delay: 0.2,
    },
    {
      label: 'Clinical Alerts',
      value: stats.highRiskCount + stats.mediumRiskCount,
      detail: 'Actions required',
      icon: AlertTriangle,
      color: 'text-amber-400',
      delay: 0.3,
    },
  ]

  return (
    <GlassCard>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-dna-cyan to-dna-blue flex items-center justify-center">
          <TrendingUp className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Summary Dashboard</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {widgets.map((widget, idx) => {
          const Icon = widget.icon
          return (
            <motion.div
              key={idx}
              className={`glass-card rounded-xl p-6 border-2 ${widget.className || 'border-white/10'}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: widget.delay }}
              whileHover={{ scale: 1.05, y: -4 }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg bg-white/5`}>
                  <Icon className={`w-5 h-5 ${widget.color}`} />
                </div>
              </div>
              <div className="mb-2">
                <div className="text-sm text-slate-400 font-medium mb-1">{widget.label}</div>
                <motion.div
                  className={`text-3xl font-bold ${widget.color || 'text-white'}`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.5, delay: widget.delay + 0.2, type: 'spring' }}
                >
                  {widget.value}
                </motion.div>
              </div>
              <div className="text-xs text-slate-400">{widget.detail}</div>
            </motion.div>
          )
        })}
      </div>
    </GlassCard>
  )
}

export default SummaryDashboard
