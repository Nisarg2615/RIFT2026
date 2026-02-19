import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './components/Header'
import HeroSection from './components/HeroSection'
import UploadSection from './components/UploadSection'
import LoadingState from './components/LoadingState'
import ErrorMessage from './components/ErrorMessage'
import SummaryDashboard from './components/SummaryDashboard'
import DrugTable from './components/DrugTable'
import GenePanel from './components/GenePanel'
import DetailedReports from './components/DetailedReports'
import DownloadSection from './components/DownloadSection'
import HistoryModal from './components/HistoryModal'
import NucleotideParticles from './components/backgrounds/NucleotideParticles'
import { saveToHistory } from './utils/historyManager'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedDrugs, setSelectedDrugs] = useState([])
  const [patientHistory, setPatientHistory] = useState({
    patientId: '',
    age: '',
    gender: '',
    weight: '',
    ethnicity: '',
    bloodGroup: '',
    conditions: [],
    otherConditions: '',
    currentMedications: [],
    otherMedications: '',
    drugAllergies: '',
    adverseReactions: '',
    kidneyFunction: '',
    liverFunction: '',
    smokingStatus: '',
    alcoholUse: '',
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showHero, setShowHero] = useState(true)
  const [showHistory, setShowHistory] = useState(false)

  // Load sample data handler
  const handleLoadSampleData = () => {
    // This would typically load sample data from your backend
    // For now, we'll just show a message
    alert('Sample data loading feature - connect to your backend API')
  }

  // Use sample VCF handler
  const handleUseSampleVCF = () => {
    // Create a mock file object for sample VCF
    const sampleFile = new File(['##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n'], 'sample.vcf', { type: 'text/vcf' })
    setSelectedFile(sampleFile)
  }

  // Submit analysis
  const handleSubmit = async () => {
    if (!selectedFile || selectedDrugs.length === 0) {
      setError('Please select a VCF file and at least one drug')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)
    setShowHero(false)

    try {
      const formData = new FormData()
      formData.append('vcf_file', selectedFile)
      formData.append('drugs', selectedDrugs.join(','))
      
      // Add patient history to form data
      if (patientHistory.patientId) formData.append('patient_id', patientHistory.patientId)
      if (patientHistory.age) formData.append('age', patientHistory.age)
      if (patientHistory.gender) formData.append('gender', patientHistory.gender)
      if (patientHistory.weight) formData.append('weight', patientHistory.weight)
      if (patientHistory.ethnicity) formData.append('ethnicity', patientHistory.ethnicity)
      if (patientHistory.bloodGroup) formData.append('blood_group', patientHistory.bloodGroup)
      if (patientHistory.conditions?.length > 0) formData.append('conditions', patientHistory.conditions.join(','))
      if (patientHistory.otherConditions) formData.append('other_conditions', patientHistory.otherConditions)
      if (patientHistory.currentMedications?.length > 0) formData.append('current_medications', patientHistory.currentMedications.join(','))
      if (patientHistory.otherMedications) formData.append('other_medications', patientHistory.otherMedications)
      if (patientHistory.drugAllergies) formData.append('drug_allergies', patientHistory.drugAllergies)
      if (patientHistory.adverseReactions) formData.append('adverse_reactions', patientHistory.adverseReactions)
      if (patientHistory.kidneyFunction) formData.append('kidney_function', patientHistory.kidneyFunction)
      if (patientHistory.liverFunction) formData.append('liver_function', patientHistory.liverFunction)
      if (patientHistory.smokingStatus) formData.append('smoking_status', patientHistory.smokingStatus)
      if (patientHistory.alcoholUse) formData.append('alcohol_use', patientHistory.alcoholUse)

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Backend API not found. Please ensure the backend server is running on http://localhost:8000')
        }
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Handle both array and object responses
      let resultsData = null
      if (Array.isArray(data)) {
        resultsData = data
      } else if (data.results) {
        resultsData = data.results
      } else {
        throw new Error('Invalid response format')
      }
      
      setResults(resultsData)
      
      // Save to history
      if (resultsData) {
        saveToHistory(resultsData)
      }
    } catch (err) {
      setError(err.message || 'Error analyzing file. Please try again.')
      console.error('Analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Scroll to top when results are shown
  useEffect(() => {
    if (results) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [results])

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Background particles for non-hero sections */}
      {!showHero && <NucleotideParticles count={20} />}
      
      {!showHero && (
        <Header
          onHistoryClick={() => setShowHistory(true)}
          onDashboardClick={() => {
            setShowHistory(false)
            setResults(null)
            setShowHero(false)
            setError(null)
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        />
      )}
      
      <HistoryModal
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onLoadHistoryItem={(historyData) => {
          setResults(historyData)
          setShowHero(false)
          setError(null)
        }}
      />
      
      <main className="min-h-screen">
        {/* Hero Section */}
        <AnimatePresence>
          {showHero && !results && !loading && (
            <motion.div
              initial={{ opacity: 1 }}
              exit={{ opacity: 0, y: -100 }}
              transition={{ duration: 0.5 }}
            >
              <HeroSection onGetStarted={() => setShowHero(false)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-6 py-12">
          <AnimatePresence mode="wait">
            {!results && !loading && !showHero && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <UploadSection
                  selectedFile={selectedFile}
                  setSelectedFile={setSelectedFile}
                  selectedDrugs={selectedDrugs}
                  setSelectedDrugs={setSelectedDrugs}
                  patientHistory={patientHistory}
                  setPatientHistory={setPatientHistory}
                  onSubmit={handleSubmit}
                  onUseSampleVCF={handleUseSampleVCF}
                  onLoadSampleData={handleLoadSampleData}
                />
              </motion.div>
            )}

            {loading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <LoadingState />
              </motion.div>
            )}

            {error && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <ErrorMessage 
                  message={error} 
                  onClose={() => setError(null)} 
                />
                {!loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <UploadSection
                      selectedFile={selectedFile}
                      setSelectedFile={setSelectedFile}
                      selectedDrugs={selectedDrugs}
                      setSelectedDrugs={setSelectedDrugs}
                      patientHistory={patientHistory}
                      setPatientHistory={setPatientHistory}
                      onSubmit={handleSubmit}
                      onUseSampleVCF={handleUseSampleVCF}
                      onLoadSampleData={handleLoadSampleData}
                    />
                  </motion.div>
                )}
              </motion.div>
            )}

            {results && !loading && (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="space-y-8"
              >
                {/* Back to upload button */}
                <motion.button
                  className="px-6 py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all flex items-center gap-2"
                  onClick={() => {
                    setResults(null)
                    setSelectedFile(null)
                    setSelectedDrugs([])
                    setShowHero(true)
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  ← New Analysis
                </motion.button>

                {/* Results Sections */}
                <SummaryDashboard results={results} />
                <DrugTable results={results} />
                <GenePanel results={results} />
                <DetailedReports results={results} />
                <DownloadSection results={results} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      {!showHero && (
        <footer className="border-t border-white/10 mt-20 py-8">
          <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm">
            <p>PharmaGuard AI - Precision Pharmacogenomics Platform</p>
            <p className="mt-2">Clinical-grade AI-powered drug risk analysis</p>
          </div>
        </footer>
      )}
    </div>
  )
}

export default App
