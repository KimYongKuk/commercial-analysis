import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { ArrowLeft, Coffee, UtensilsCrossed, Scissors, ShoppingBag, Dumbbell, Store } from 'lucide-react';
import { Map, CustomOverlayMap } from 'react-kakao-maps-sdk';
import Chatbot from './Chatbot';
import { transformHeatmapToLocations } from './utils/heatmapUtils';

type HeatmapPageProps = {
  onBack: () => void;
};

type Industry = {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
};

type HeatmapData = {
  district: string;
  lat: number;
  lng: number;
  count: number;
  density: number;
  avgRent: number;
};

const industries: Industry[] = [
  { id: 'cafe', name: '카페', icon: <Coffee className="w-5 h-5" />, color: 'from-amber-500 to-amber-600' },
  { id: 'restaurant', name: '음식점', icon: <UtensilsCrossed className="w-5 h-5" />, color: 'from-red-500 to-red-600' },
  { id: 'beauty', name: '미용실', icon: <Scissors className="w-5 h-5" />, color: 'from-pink-500 to-pink-600' },
  { id: 'convenience', name: '편의점', icon: <Store className="w-5 h-5" />, color: 'from-green-500 to-green-600' },
  { id: 'retail', name: '소매점', icon: <ShoppingBag className="w-5 h-5" />, color: 'from-purple-500 to-purple-600' },
  { id: 'fitness', name: '헬스장', icon: <Dumbbell className="w-5 h-5" />, color: 'from-blue-500 to-blue-600' },
];

// Mock 데이터
const mockHeatmapData: Record<string, HeatmapData[]> = {
  cafe: [
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 850, density: 95, avgRent: 300 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 720, density: 88, avgRent: 250 },
    { district: '용산구 이태원', lat: 37.5345, lng: 126.9947, count: 520, density: 75, avgRent: 280 },
    { district: '서대문구 신촌', lat: 37.5559, lng: 126.9364, count: 480, density: 70, avgRent: 220 },
    { district: '강남구 청담동', lat: 37.5240, lng: 127.0476, count: 420, density: 65, avgRent: 350 },
    { district: '송파구 잠실', lat: 37.5133, lng: 127.1028, count: 380, density: 60, avgRent: 240 },
    { district: '영등포구 여의도', lat: 37.5219, lng: 126.9245, count: 350, density: 55, avgRent: 320 },
    { district: '종로구 삼청동', lat: 37.5825, lng: 126.9825, count: 320, density: 50, avgRent: 280 },
  ],
  restaurant: [
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 1200, density: 98, avgRent: 350 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 980, density: 92, avgRent: 280 },
    { district: '용산구 이태원', lat: 37.5345, lng: 126.9947, count: 750, density: 82, avgRent: 320 },
    { district: '강남구 신사동', lat: 37.5217, lng: 127.0200, count: 680, density: 78, avgRent: 380 },
    { district: '종로구 인사동', lat: 37.5735, lng: 126.9850, count: 550, density: 70, avgRent: 260 },
    { district: '송파구 잠실', lat: 37.5133, lng: 127.1028, count: 520, density: 68, avgRent: 270 },
  ],
  beauty: [
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 450, density: 88, avgRent: 250 },
    { district: '강남구 청담동', lat: 37.5240, lng: 127.0476, count: 380, density: 80, avgRent: 320 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 320, density: 72, avgRent: 220 },
    { district: '강남구 신사동', lat: 37.5217, lng: 127.0200, count: 280, density: 65, avgRent: 290 },
    { district: '서초구 반포', lat: 37.5047, lng: 127.0050, count: 250, density: 58, avgRent: 270 },
  ],
  convenience: [
    { district: '송파구 잠실', lat: 37.5133, lng: 127.1028, count: 180, density: 75, avgRent: 200 },
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 160, density: 70, avgRent: 250 },
    { district: '영등포구 여의도', lat: 37.5219, lng: 126.9245, count: 140, density: 65, avgRent: 280 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 130, density: 60, avgRent: 220 },
  ],
  retail: [
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 620, density: 85, avgRent: 320 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 550, density: 78, avgRent: 260 },
    { district: '강남구 청담동', lat: 37.5240, lng: 127.0476, count: 480, density: 72, avgRent: 380 },
    { district: '용산구 이태원', lat: 37.5345, lng: 126.9947, count: 420, density: 65, avgRent: 300 },
  ],
  fitness: [
    { district: '강남구 역삼동', lat: 37.5013, lng: 127.0396, count: 280, density: 78, avgRent: 280 },
    { district: '송파구 잠실', lat: 37.5133, lng: 127.1028, count: 220, density: 68, avgRent: 240 },
    { district: '영등포구 여의도', lat: 37.5219, lng: 126.9245, count: 180, density: 58, avgRent: 290 },
    { district: '마포구 홍대입구', lat: 37.5563, lng: 126.9227, count: 150, density: 50, avgRent: 230 },
  ],
};

// 밀집도에 따른 색상 계산
const getDensityColor = (density: number): string => {
  if (density >= 90) return 'rgba(239, 68, 68, 0.7)';   // 빨강 (매우 높음)
  if (density >= 75) return 'rgba(249, 115, 22, 0.7)';  // 주황 (높음)
  if (density >= 60) return 'rgba(234, 179, 8, 0.7)';   // 노랑 (중간)
  if (density >= 45) return 'rgba(34, 197, 94, 0.7)';   // 초록 (낮음)
  return 'rgba(59, 130, 246, 0.7)';                      // 파랑 (매우 낮음)
};

export default function HeatmapPage({ onBack }: HeatmapPageProps) {
  const [selectedIndustry, setSelectedIndustry] = useState<string>('cafe');
  const [hoveredDistrict, setHoveredDistrict] = useState<HeatmapData | null>(null);
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);

  const currentData = mockHeatmapData[selectedIndustry] || [];
  const selectedIndustryInfo = industries.find(ind => ind.id === selectedIndustry);

  // 지도 중심 계산 (서울 중심)
  const mapCenter = { lat: 37.5394, lng: 127.0007 };

  // Chatbot에 전달할 Location 데이터 생성
  const chatbotLocations = useMemo(() => {
    return transformHeatmapToLocations(currentData, selectedIndustry);
  }, [currentData, selectedIndustry]);

  // Chatbot 환영 메시지 커스터마이징
  const industryName = selectedIndustryInfo?.name || '업종';
  const chatbotWelcomeMessage = `안녕하세요! 히트맵 분석 AI입니다. 선택하신 ${industryName} 업종의 밀집도 및 트렌드에 대해 궁금하신 점을 물어보세요! 📊`;
  const chatbotTitle = `${industryName} 히트맵 AI`;

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={onBack}
            className="mb-4 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            메인으로
          </Button>

          <h1 className="text-gray-900 mb-2">업종별 히트맵 분석</h1>
          <p className="text-gray-600">
            업종을 선택하면 매장 밀집도를 한눈에 확인할 수 있습니다.
          </p>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-[280px_1fr] gap-6">
          {/* Left Sidebar - Industry Selector */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="p-6 sticky top-6">
              <h2 className="text-gray-900 mb-4">업종 선택</h2>
              <div className="space-y-3">
                {industries.map((industry) => (
                  <motion.button
                    key={industry.id}
                    onClick={() => setSelectedIndustry(industry.id)}
                    className={`w-full p-4 rounded-lg flex items-center gap-3 transition-all ${
                      selectedIndustry === industry.id
                        ? `bg-gradient-to-r ${industry.color} text-white shadow-md`
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {industry.icon}
                    <span className="font-medium">{industry.name}</span>
                    {selectedIndustry === industry.id && (
                      <Badge className="ml-auto bg-white/20 text-white">
                        {currentData.length}곳
                      </Badge>
                    )}
                  </motion.button>
                ))}
              </div>

              {/* Legend */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-3">밀집도</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'rgba(239, 68, 68, 0.7)' }} />
                    <span className="text-xs text-gray-600">매우 높음 (90+)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'rgba(249, 115, 22, 0.7)' }} />
                    <span className="text-xs text-gray-600">높음 (75-89)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'rgba(234, 179, 8, 0.7)' }} />
                    <span className="text-xs text-gray-600">중간 (60-74)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'rgba(34, 197, 94, 0.7)' }} />
                    <span className="text-xs text-gray-600">낮음 (45-59)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'rgba(59, 130, 246, 0.7)' }} />
                    <span className="text-xs text-gray-600">매우 낮음 (&lt;45)</span>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Right Content - Map */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-gray-900">{selectedIndustryInfo?.name} 밀집도 지도</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    총 {currentData.length}개 지역 분석
                  </p>
                </div>
              </div>

              {/* Kakao Map */}
              <div className="relative">
                <Map
                  center={mapCenter}
                  style={{ width: '100%', height: '600px', borderRadius: '0.5rem' }}
                  level={9}
                >
                  {currentData.map((data) => (
                    <CustomOverlayMap
                      key={data.district}
                      position={{ lat: data.lat, lng: data.lng }}
                    >
                      <div
                        className="relative cursor-pointer"
                        onMouseEnter={() => setHoveredDistrict(data)}
                        onMouseLeave={() => setHoveredDistrict(null)}
                      >
                        {/* 히트맵 원형 */}
                        <div
                          style={{
                            width: `${data.density}px`,
                            height: `${data.density}px`,
                            backgroundColor: getDensityColor(data.density),
                            borderRadius: '50%',
                            border: '2px solid rgba(255, 255, 255, 0.8)',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                            transition: 'transform 0.2s',
                            transform: hoveredDistrict?.district === data.district ? 'scale(1.1)' : 'scale(1)',
                          }}
                        />

                        {/* 호버 시 정보 표시 */}
                        {hoveredDistrict?.district === data.district && (
                          <div
                            className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 bg-white p-3 rounded-lg shadow-xl border border-gray-200 whitespace-nowrap z-50"
                          >
                            <div className="text-sm font-medium text-gray-900 mb-1">
                              {data.district}
                            </div>
                            <div className="text-xs text-gray-600 space-y-1">
                              <div>매장 수: <span className="font-medium">{data.count}개</span></div>
                              <div>밀집도: <span className="font-medium">{data.density}점</span></div>
                              <div>평균 임대료: <span className="font-medium">{data.avgRent}만원</span></div>
                            </div>
                          </div>
                        )}
                      </div>
                    </CustomOverlayMap>
                  ))}
                </Map>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Chatbot */}
      <Chatbot
        isOpen={isChatbotOpen}
        onToggle={() => setIsChatbotOpen(!isChatbotOpen)}
        locations={chatbotLocations}
        title={chatbotTitle}
        welcomeMessage={chatbotWelcomeMessage}
      />
    </div>
  );
}
