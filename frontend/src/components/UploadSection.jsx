import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileCheck, X, CheckCircle2, FileCode, User, Heart, Pill, AlertTriangle, Activity, Cigarette, Sparkles } from 'lucide-react'
import GlassCard from './ui/GlassCard'
import GenomeScanAnimation from './backgrounds/GenomeScanAnimation'
import AIGlowButton from './ui/AIGlowButton'

const AVAILABLE_DRUGS = ['Codeine', 'Clopidogrel', 'Warfarin', 'Simvastatin', 'Azathioprine', 'Fluorouracil']

const COMMON_CONDITIONS = ['Diabetes', 'Hypertension', 'Liver Disease', 'Kidney Disease', 'Heart Failure', 'Asthma', 'Peptic Ulcer', 'Epilepsy', 'Depression', 'Pregnancy']

const COMMON_MEDICATIONS = ['Aspirin', 'Omeprazole', 'Metformin', 'Amlodipine', 'Fluoxetine', 'Ibuprofen', 'Diazepam', 'Allopurinol', 'Amiodarone', 'Clarithromycin']

function UploadSection({ 
  selectedFile, 
  setSelectedFile, 
  selectedDrugs, 
  setSelectedDrugs,
  patientHistory,
  setPatientHistory,
  onSubmit, 
  onUseSampleVCF, 
  onLoadSampleData 
}) {
  const [dragActive, setDragActive] = useState(false)
  const [fileStatus, setFileStatus] = useState('')
  const [customDrugs, setCustomDrugs] = useState('')

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = (file) => {
    if (!file.name.endsWith('.vcf')) {
      alert('Please select a valid VCF file (.vcf format)')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('File is too large. Maximum size is 5 MB')
      return
    }
    setSelectedFile(file)
    setFileStatus(`✓ ${file.name} selected (${(file.size / 1024).toFixed(2)} KB)`)
  }

  const handleDrugToggle = (drug) => {
    if (selectedDrugs.includes(drug)) {
      setSelectedDrugs(selectedDrugs.filter(d => d !== drug))
    } else {
      setSelectedDrugs([...selectedDrugs, drug])
    }
  }

  const handleSelectAll = () => {
    setSelectedDrugs([...AVAILABLE_DRUGS])
  }

  const handleClearAll = () => {
    setSelectedDrugs([])
  }

  const handleCustomDrugsChange = (value) => {
    setCustomDrugs(value)
    const drugs = value.split(',').map(d => d.trim()).filter(d => d)
    setSelectedDrugs([...new Set([...selectedDrugs.filter(d => AVAILABLE_DRUGS.includes(d)), ...drugs])])
  }

  const handleConditionToggle = (condition) => {
    const conditions = patientHistory.conditions || []
    if (conditions.includes(condition)) {
      setPatientHistory({
        ...patientHistory,
        conditions: conditions.filter(c => c !== condition)
      })
    } else {
      setPatientHistory({
        ...patientHistory,
        conditions: [...conditions, condition]
      })
    }
  }

  const handleMedicationToggle = (medication) => {
    const medications = patientHistory.currentMedications || []
    if (medications.includes(medication)) {
      setPatientHistory({
        ...patientHistory,
        currentMedications: medications.filter(m => m !== medication)
      })
    } else {
      setPatientHistory({
        ...patientHistory,
        currentMedications: [...medications, medication]
      })
    }
  }

  return (
    <div className="space-y-8">
      {/* Upload VCF & Select Drugs Section */}
      <GlassCard>
        <h2 className="text-2xl font-bold text-white mb-6">Upload VCF & Select Drugs</h2>
        
        {/* VCF File Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-white mb-2">
            VCF File (v4.2, ≤ 5 MB)
          </label>
          <div className="relative">
            <motion.div
              className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragActive 
                  ? 'border-dna-cyan bg-dna-cyan/10 scale-105' 
                  : selectedFile 
                  ? 'border-dna-green bg-dna-green/10' 
                  : 'border-white/20 hover:border-dna-cyan/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput').click()}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              <GenomeScanAnimation isActive={dragActive || !!selectedFile} />
              
              {selectedFile ? (
                <div className="flex flex-col items-center gap-3">
                  <FileCheck className="w-12 h-12 text-dna-green" />
                  <div>
                    <p className="text-lg font-semibold text-white">{selectedFile.name}</p>
                    <p className="text-sm text-slate-400">{(selectedFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                  <motion.button
                    className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors flex items-center gap-2"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedFile(null)
                      setFileStatus('')
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <X className="w-4 h-4" />
                    Remove
                  </motion.button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="w-12 h-12 text-dna-cyan" />
                  <div>
                    <p className="text-white font-medium">Drag and drop VCF file or click to browse</p>
                    <p className="text-sm text-slate-400 mt-1">Accepted: .vcf files with INFO tags GENE, STAR, RS</p>
                  </div>
                </div>
              )}
              
              <input
                type="file"
                id="fileInput"
                accept=".vcf"
                className="hidden"
                onChange={(e) => e.target.files && handleFile(e.target.files[0])}
              />
            </motion.div>
          </div>
        </div>

        {/* Quick-select drugs */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-white mb-3">Quick-select drugs</label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_DRUGS.map((drug) => (
              <motion.button
                key={drug}
                onClick={() => handleDrugToggle(drug)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedDrugs.includes(drug)
                    ? 'bg-gradient-to-r from-dna-cyan to-dna-purple text-white'
                    : 'bg-white/10 text-slate-300 hover:bg-white/20'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {drug}
              </motion.button>
            ))}
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleSelectAll}
              className="text-xs text-slate-400 hover:text-white"
            >
              Select All
            </button>
            <span className="text-slate-600">|</span>
            <button
              onClick={handleClearAll}
              className="text-xs text-slate-400 hover:text-white"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Type Drug Names */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-white mb-2">
            Or type drug names (comma-separated)
          </label>
          <input
            type="text"
            value={customDrugs}
            onChange={(e) => handleCustomDrugsChange(e.target.value)}
            placeholder="WARFARIN, CLOPIDOGREL, SIMVASTATIN"
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan focus:ring-1 focus:ring-dna-cyan"
          />
        </div>

        {/* Patient ID */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-white mb-2">
            Patient ID (optional)
          </label>
          <input
            type="text"
            value={patientHistory.patientId || ''}
            onChange={(e) => setPatientHistory({ ...patientHistory, patientId: e.target.value })}
            placeholder="1005"
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan focus:ring-1 focus:ring-dna-cyan"
          />
        </div>
      </GlassCard>

      {/* Patient Clinical History Section */}
      <GlassCard>
        <div className="flex items-center gap-3 mb-2">
          <FileCode className="w-5 h-5 text-dna-cyan" />
          <h2 className="text-2xl font-bold text-white">Patient Clinical History</h2>
        </div>
        <p className="text-sm text-slate-400 mb-6">
          Fill in available patient information for personalised risk assessment, interaction checking, and more accurate clinical recommendations.
        </p>

        {/* DEMOGRAPHICS */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">DEMOGRAPHICS</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Age (years)</label>
              <input
                type="number"
                value={patientHistory.age || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, age: e.target.value })}
                placeholder="68"
                className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Gender</label>
              <select
                value={patientHistory.gender || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, gender: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Weight (kg)</label>
              <input
                type="number"
                value={patientHistory.weight || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, weight: e.target.value })}
                placeholder="72"
                className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Ethnicity</label>
              <select
                value={patientHistory.ethnicity || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, ethnicity: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="Caucasian / European">Caucasian / European</option>
                <option value="Asian">Asian</option>
                <option value="African">African</option>
                <option value="Hispanic">Hispanic</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Blood Group</label>
              <select
                value={patientHistory.bloodGroup || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, bloodGroup: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
              </select>
            </div>
          </div>
        </div>

        {/* MEDICAL CONDITIONS */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">MEDICAL CONDITIONS</h3>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-white mb-2">Common conditions (click to add)</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_CONDITIONS.map((condition) => (
                <motion.button
                  key={condition}
                  onClick={() => handleConditionToggle(condition)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    (patientHistory.conditions || []).includes(condition)
                      ? 'bg-gradient-to-r from-dna-cyan to-dna-purple text-white'
                      : 'bg-white/10 text-slate-300 hover:bg-white/20'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {condition}
                </motion.button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Other conditions (comma-separated)</label>
            <input
              type="text"
              value={patientHistory.otherConditions || ''}
              onChange={(e) => setPatientHistory({ ...patientHistory, otherConditions: e.target.value })}
              placeholder="Type 2 Diabetes, Atrial Fibrillation, hypertension"
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan"
            />
          </div>
        </div>

        {/* CURRENT MEDICATIONS */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Pill className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">CURRENT MEDICATIONS</h3>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-white mb-2">Common medications (click to add)</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_MEDICATIONS.map((medication) => (
                <motion.button
                  key={medication}
                  onClick={() => handleMedicationToggle(medication)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    (patientHistory.currentMedications || []).includes(medication)
                      ? 'bg-gradient-to-r from-dna-cyan to-dna-purple text-white'
                      : 'bg-white/10 text-slate-300 hover:bg-white/20'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {medication}
                </motion.button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Other medications (comma-separated)</label>
            <input
              type="text"
              value={patientHistory.otherMedications || ''}
              onChange={(e) => setPatientHistory({ ...patientHistory, otherMedications: e.target.value })}
              placeholder="Metformin, Omeprazole, Aspirin"
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan"
            />
          </div>
        </div>

        {/* ALLERGIES & ADVERSE REACTIONS */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">ALLERGIES & ADVERSE REACTIONS</h3>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-white mb-2">Drug Allergies (comma-separated)</label>
            <input
              type="text"
              value={patientHistory.drugAllergies || ''}
              onChange={(e) => setPatientHistory({ ...patientHistory, drugAllergies: e.target.value })}
              placeholder="Codeine, Penicillin"
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white mb-2">Prior Adverse Drug Reactions</label>
            <textarea
              value={patientHistory.adverseReactions || ''}
              onChange={(e) => setPatientHistory({ ...patientHistory, adverseReactions: e.target.value })}
              placeholder="e.g. Codeine → severe nausea, Warfarin → bleeding episode"
              rows={3}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-500 focus:outline-none focus:border-dna-cyan resize-none"
            />
          </div>
        </div>

        {/* ORGAN FUNCTION */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">ORGAN FUNCTION</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Kidney Function</label>
              <select
                value={patientHistory.kidneyFunction || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, kidneyFunction: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="Normal">Normal</option>
                <option value="Mild Impairment">Mild Impairment</option>
                <option value="Moderate Impairment">Moderate Impairment</option>
                <option value="Severe Impairment">Severe Impairment</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">Liver Function</label>
              <select
                value={patientHistory.liverFunction || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, liverFunction: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="Normal">Normal</option>
                <option value="Mild Impairment">Mild Impairment</option>
                <option value="Moderate Impairment">Moderate Impairment</option>
                <option value="Severe Impairment">Severe Impairment</option>
              </select>
            </div>
          </div>
        </div>

        {/* LIFESTYLE FACTORS */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Cigarette className="w-4 h-4 text-dna-cyan" />
            <h3 className="text-lg font-semibold text-dna-cyan uppercase">LIFESTYLE FACTORS</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Smoking Status</label>
              <select
                value={patientHistory.smokingStatus || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, smokingStatus: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="Never Smoker">Never Smoker</option>
                <option value="Current Smoker">Current Smoker</option>
                <option value="Former Smoker">Former Smoker</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">Alcohol Use</label>
              <select
                value={patientHistory.alcoholUse || ''}
                onChange={(e) => setPatientHistory({ ...patientHistory, alcoholUse: e.target.value })}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-dna-cyan"
              >
                <option value="">Select</option>
                <option value="None">None</option>
                <option value="Occasional">Occasional</option>
                <option value="Regular">Regular</option>
                <option value="Heavy">Heavy</option>
              </select>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Submit Button */}
      <motion.div
        className="flex justify-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <AIGlowButton
          onClick={onSubmit}
          disabled={!selectedFile || selectedDrugs.length === 0}
          className="text-lg px-8 py-4"
        >
          <Sparkles className="w-5 h-5" />
          Analyze Pharmacogenomic Risk
        </AIGlowButton>
      </motion.div>
    </div>
  )
}

export default UploadSection
