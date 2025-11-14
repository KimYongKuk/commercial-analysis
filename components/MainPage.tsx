import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Sparkles, TrendingUp, MapPin, BarChart3, Flame } from 'lucide-react';

type MainPageProps = {
  onStart: () => void;
  onHeatmap: () => void;
};

export default function MainPage({ onStart, onHeatmap }: MainPageProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="px-6 py-6">
        <motion.div
          className="flex items-center gap-2"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-2 rounded-lg">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-blue-900 tracking-tight">JobFlex</span>
        </motion.div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 pb-20">
        <div className="max-w-4xl w-full text-center">
          <motion.div
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h1 className="text-blue-900 mb-4">
              내 입맛에 맞는 창업,<br />AI가 도와드립니다.
            </h1>
            <p className="text-gray-600 mb-12 max-w-2xl mx-auto">
              상권 데이터 기반 인공지능이 당신의 조건에 딱 맞는 창업 입지를 추천해드립니다.
            </p>
          </motion.div>

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex gap-4 justify-center"
          >
            <Button
              onClick={onStart}
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-12 py-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <BarChart3 className="mr-2 w-5 h-5" />
              상권 분석하기
            </Button>
            <Button
              onClick={onHeatmap}
              size="lg"
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-12 py-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Flame className="mr-2 w-5 h-5" />
              히트맵 분석
            </Button>
          </motion.div>

          {/* Feature Cards */}
          <motion.div 
            className="grid md:grid-cols-3 gap-6 mt-20"
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <FeatureCard 
              icon={<MapPin className="w-6 h-6" />}
              title="맞춤 입지 추천"
              description="업종과 예산에 맞는 최적의 위치를 찾아드립니다"
            />
            <FeatureCard 
              icon={<TrendingUp className="w-6 h-6" />}
              title="실시간 상권 분석"
              description="유동인구, 경쟁업체 등 핵심 데이터를 제공합니다"
            />
            <FeatureCard 
              icon={<Sparkles className="w-6 h-6" />}
              title="AI 기반 예측"
              description="성공 가능성을 정량적으로 분석해드립니다"
            />
          </motion.div>
        </div>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <motion.div 
      className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-300"
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <div className="bg-blue-50 w-12 h-12 rounded-lg flex items-center justify-center text-blue-600 mb-4 mx-auto">
        {icon}
      </div>
      <h3 className="text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </motion.div>
  );
}
