import { useState } from 'react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { ArrowLeft, MapPin, Users, DollarSign, Store, Sparkles, MessageCircle, X, Send, Home } from 'lucide-react';
import type { FormData } from '../App';
import Chatbot from './Chatbot';
import { Map, MapMarker } from 'react-kakao-maps-sdk';

type ResultPageProps = {
  formData: FormData;
  onBack: () => void;
  onBackToMain: () => void;
};

type Location = {
  id: number;
  name: string;
  score: number;
  lat: number;
  lng: number;
  metrics: {
    location: number;
    footTraffic: number;
    rent: number;
    competition: number;
  };
  descriptions: {
    location: string;
    footTraffic: string;
    rent: string;
    competition: string;
  };
};

export default function ResultPage({ formData, onBack, onBackToMain }: ResultPageProps) {
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [selectedLocationId, setSelectedLocationId] = useState(1);
  
  // Mock data based on form input
  const locations: Location[] = [
    { 
      id: 1, 
      name: '역삼동 테헤란로 인근', 
      score: 92, 
      lat: 37.5013, 
      lng: 127.0396,
      metrics: { location: 95, footTraffic: 92, rent: 85, competition: 96 },
      descriptions: {
        location: '지하철역 도보 2분 거리로 접근성이 뛰어나고 대로변에 위치해 가시성이 매우 우수합니다',
        footTraffic: '평일 평균 18,000명의 유동인구로 직장인 고객층이 매우 풍부합니다',
        rent: '예산 대비 적정한 임대료 수준이며 투자 대비 수익성이 높습니다',
        competition: '동일 업종이 적절히 분산되어 있어 시너지 효과를 기대할 수 있습니다',
      }
    },
    { 
      id: 2, 
      name: '삼성동 코엑스 인근', 
      score: 87, 
      lat: 37.5115, 
      lng: 127.0595,
      metrics: { location: 88, footTraffic: 90, rent: 78, competition: 92 },
      descriptions: {
        location: '코엑스몰과 연결되어 유동인구 유입이 자연스럽고 주차 시설이 우수합니다',
        footTraffic: '주말 유동인구가 특히 높으며 관광객과 쇼핑객이 많은 상권입니다',
        rent: '초기 투자비용이 다소 높으나 높은 매출로 회수 가능합니다',
        competition: '경쟁업체가 많지만 유동인구가 충분해 공존 가능한 구조입니다',
      }
    },
    { 
      id: 3, 
      name: '논현동 학동사거리 인근', 
      score: 83, 
      lat: 37.5108, 
      lng: 127.0229,
      metrics: { location: 85, footTraffic: 82, rent: 88, competition: 78 },
      descriptions: {
        location: '주요 간선도로와 인접하고 주변 오피스와 주거지역이 균형있게 위치합니다',
        footTraffic: '주중과 주말 유동인구가 안정적이며 지역 주민 충성도가 높습니다',
        rent: '임대료가 합리적이며 장기 운영에 유리한 조건입니다',
        competition: '경쟁업체가 상대적으로 적어 초기 시장 점유가 용이합니다',
      }
    },
  ];

  const selectedLocation = locations.find(loc => loc.id === selectedLocationId) || locations[0];

  const metrics = [
    { icon: <MapPin className="w-5 h-5" />, label: '입지', score: selectedLocation.metrics.location, description: selectedLocation.descriptions.location },
    { icon: <Users className="w-5 h-5" />, label: '유동인구', score: selectedLocation.metrics.footTraffic, description: selectedLocation.descriptions.footTraffic },
    { icon: <DollarSign className="w-5 h-5" />, label: '임대료', score: selectedLocation.metrics.rent, description: selectedLocation.descriptions.rent },
    { icon: <Store className="w-5 h-5" />, label: '경쟁업체', score: selectedLocation.metrics.competition, description: selectedLocation.descriptions.competition },
  ];

  const getIndustryLabel = (value: string) => {
    const labels: Record<string, string> = {
      cafe: '카페',
      restaurant: '음식점',
      beauty: '미용실',
      convenience: '편의점',
      retail: '소매점',
      fitness: '헬스장',
    };
    return labels[value] || value;
  };

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex gap-2 mb-4 -ml-2">
            <Button
              variant="ghost"
              onClick={onBack}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              다시 분석하기
            </Button>
            <Button
              variant="ghost"
              onClick={onBackToMain}
            >
              <Home className="w-4 h-4 mr-2" />
              메인으로
            </Button>
          </div>
          
          <div className="flex items-center gap-2 mb-2">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-2 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-blue-900">JobFlex</span>
          </div>
          
          <h1 className="text-gray-900 mt-4 mb-2">
            분석 결과
          </h1>
          <p className="text-gray-600">
            {getIndustryLabel(formData.industry)} 창업을 위한 맞춤 입지 분석 결과입니다.
          </p>
        </div>

        {/* TOP 3 Location Selector */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h2 className="text-gray-900 mb-4">TOP 3 추천 입지</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {locations.map((location, index) => (
              <motion.div
                key={location.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -4 }}
              >
                <Card
                  className={`p-5 cursor-pointer transition-all duration-300 ${
                    selectedLocationId === location.id
                      ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg ring-2 ring-blue-400'
                      : 'bg-white hover:shadow-md border-gray-200'
                  }`}
                  onClick={() => setSelectedLocationId(location.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedLocationId === location.id
                          ? 'bg-white/20 text-white'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {index + 1}
                      </div>
                      <Badge 
                        variant="secondary" 
                        className={selectedLocationId === location.id 
                          ? 'bg-white/20 text-white' 
                          : 'bg-blue-100 text-blue-700'
                        }
                      >
                        {location.score}점
                      </Badge>
                    </div>
                  </div>
                  <h3 className={selectedLocationId === location.id ? 'text-white' : 'text-gray-900'}>
                    {location.name}
                  </h3>
                  <p className={`text-sm mt-2 ${
                    selectedLocationId === location.id ? 'text-blue-100' : 'text-gray-600'
                  }`}>
                    클릭하여 상세 분석 보기
                  </p>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Map */}
          <motion.div
            key={selectedLocationId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="p-6 h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-gray-900">{selectedLocation.name}</h2>
                <Badge className="bg-blue-600 text-white">
                  {selectedLocation.score}점
                </Badge>
              </div>
              
              {/* Kakao Map */}
              <Map
                center={{ lat: selectedLocation.lat, lng: selectedLocation.lng }}
                style={{ width: '100%', height: '500px', borderRadius: '0.5rem' }}
                level={3}
              >
                {locations.map((loc, index) => (
                  <MapMarker
                    key={loc.id}
                    position={{ lat: loc.lat, lng: loc.lng }}
                    image={{
                      src: selectedLocationId === loc.id
                        ? 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png'
                        : 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_number_blue.png',
                      size: {
                        width: selectedLocationId === loc.id ? 48 : 36,
                        height: selectedLocationId === loc.id ? 48 : 36,
                      },
                    }}
                    title={`${index + 1}순위: ${loc.name} (${loc.score}점)`}
                    onClick={() => setSelectedLocationId(loc.id)}
                  />
                ))}
              </Map>

              {/* Map Legend */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>📍 현재 위치:</strong> {selectedLocation.name} 상세 정보를 표시하고 있습니다.
                </p>
              </div>
            </Card>
          </motion.div>

          {/* Right Panel - Analysis Results */}
          <motion.div
            key={`metrics-${selectedLocationId}`}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* Overall Score */}
            <Card className="p-8 bg-gradient-to-br from-blue-600 to-blue-700 text-white">
              <div className="text-center">
                <p className="text-blue-100 mb-2">종합 적합도</p>
                <motion.div 
                  key={`score-${selectedLocationId}`}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                  className="text-6xl mb-4"
                >
                  {selectedLocation.score}
                </motion.div>
                <p className="text-blue-100">
                  이 지역은 {getIndustryLabel(formData.industry)} 창업에<br />
                  <strong className="text-white">{selectedLocation.score}점만큼 적합</strong>합니다.
                </p>
              </div>
            </Card>

            {/* Metrics */}
            <Card className="p-6">
              <h2 className="text-gray-900 mb-4">항목별 분석</h2>
              <div className="space-y-6">
                {metrics.map((metric, index) => (
                  <motion.div
                    key={`${metric.label}-${selectedLocationId}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="bg-blue-50 p-2 rounded-lg text-blue-600 mt-1">
                        {metric.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-900">{metric.label}</span>
                          <motion.span 
                            key={`score-${metric.label}-${selectedLocationId}`}
                            initial={{ scale: 1.2, color: '#2563eb' }}
                            animate={{ scale: 1, color: '#2563eb' }}
                            className="text-blue-600"
                          >
                            {metric.score}점
                          </motion.span>
                        </div>
                        <Progress value={metric.score} className="h-2 mb-2" />
                        <p className="text-sm text-gray-600">{metric.description}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Chatbot */}
      <Chatbot
        isOpen={isChatbotOpen}
        onToggle={() => setIsChatbotOpen(!isChatbotOpen)}
        formData={formData}
        locations={locations}
      />
    </div>
  );
}
