import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, History, Calendar, Dna } from 'lucide-react'
import { loadHistory } from '../utils/historyManager'

function HistoryModal({ isOpen, onClose, onLoadHistoryItem }) {
  const history = loadHistory()

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="glass-card max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <History className="w-6 h-6 text-dna-cyan" />
                  <h2 className="text-2xl font-bold text-white">Analysis History</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {history.length === 0 ? (
                  <div className="text-center py-12">
                    <Dna className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No analysis history found</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {history.map((item) => (
                      <motion.div
                        key={item.id}
                        className="glass-dark p-4 rounded-lg border border-white/10 hover:border-dna-cyan/50 transition-all cursor-pointer"
                        whileHover={{ scale: 1.02 }}
                        onClick={() => {
                          if (onLoadHistoryItem) {
                            onLoadHistoryItem(item.data)
                            onClose()
                          }
                        }}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Calendar className="w-4 h-4 text-slate-400" />
                              <span className="text-sm text-slate-400">
                                {new Date(item.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <div className="text-white font-medium">
                              {Array.isArray(item.data) 
                                ? `${item.data.length} drug(s) analyzed`
                                : 'Analysis result'}
                            </div>
                            {Array.isArray(item.data) && item.data.length > 0 && (
                              <div className="text-sm text-slate-400 mt-1">
                                Drugs: {item.data.map(d => d.drug || d.drug_name).filter(Boolean).join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default HistoryModal
