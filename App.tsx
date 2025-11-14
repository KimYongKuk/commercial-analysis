import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import MainPage from './components/MainPage';
import InputPage from './components/InputPage';
import ResultPage from './components/ResultPage';
import HeatmapPage from './components/HeatmapPage';

export type FormData = {
  industry: string;
  budget: string;
  city: string;
  district: string;
  advancedEnabled: boolean;
  targetAge?: string;
  footTraffic?: string;
  competitors?: string;
};

function App() {
  const [currentPage, setCurrentPage] = useState<'main' | 'input' | 'result' | 'heatmap'>('main');
  const [formData, setFormData] = useState<FormData>({
    industry: '',
    budget: '',
    city: '',
    district: '',
    advancedEnabled: false,
  });

  const handleStartAnalysis = () => {
    setCurrentPage('input');
  };

  const handleStartHeatmap = () => {
    setCurrentPage('heatmap');
  };

  const handleSubmitForm = (data: FormData) => {
    setFormData(data);
    setCurrentPage('result');
  };

  const handleBackToInput = () => {
    setCurrentPage('input');
  };

  const handleBackToMain = () => {
    setCurrentPage('main');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50">
      <AnimatePresence mode="wait">
        {currentPage === 'main' && (
          <motion.div
            key="main"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <MainPage onStart={handleStartAnalysis} onHeatmap={handleStartHeatmap} />
          </motion.div>
        )}

        {currentPage === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <InputPage
              onSubmit={handleSubmitForm}
              onBack={handleBackToMain}
              initialData={formData}
            />
          </motion.div>
        )}

        {currentPage === 'result' && (
          <motion.div
            key="result"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <ResultPage
              formData={formData}
              onBack={handleBackToInput}
              onBackToMain={handleBackToMain}
            />
          </motion.div>
        )}

        {currentPage === 'heatmap' && (
          <motion.div
            key="heatmap"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <HeatmapPage onBack={handleBackToMain} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
