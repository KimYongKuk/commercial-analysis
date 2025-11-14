import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card } from './ui/card';
import { Progress } from './ui/progress';
import { ArrowLeft, ArrowRight, Sparkles, Check, Coffee, UtensilsCrossed, Scissors, ShoppingBag, Store, Dumbbell } from 'lucide-react';
import type { FormData } from '../App';

type InputPageProps = {
  onSubmit: (data: FormData) => void;
  onBack: () => void;
  initialData: FormData;
};

const industries = [
  { value: 'cafe', label: '카페', icon: Coffee },
  { value: 'restaurant', label: '음식점', icon: UtensilsCrossed },
  { value: 'beauty', label: '미용실', icon: Scissors },
  { value: 'convenience', label: '편의점', icon: ShoppingBag },
  { value: 'retail', label: '소매점', icon: Store },
  { value: 'fitness', label: '헬스장', icon: Dumbbell },
];

const cities = [
  { value: 'seoul', label: '서울특별시' },
  { value: 'busan', label: '부산광역시' },
  { value: 'incheon', label: '인천광역시' },
  { value: 'daegu', label: '대구광역시' },
  { value: 'gwangju', label: '광주광역시' },
];

const districts: Record<string, { value: string; label: string }[]> = {
  seoul: [
    { value: 'gangnam', label: '강남구' },
    { value: 'seocho', label: '서초구' },
    { value: 'songpa', label: '송파구' },
    { value: 'mapo', label: '마포구' },
    { value: 'yongsan', label: '용산구' },
  ],
  busan: [
    { value: 'haeundae', label: '해운대구' },
    { value: 'busanjin', label: '부산진구' },
    { value: 'dongrae', label: '동래구' },
  ],
  incheon: [
    { value: 'namdong', label: '남동구' },
    { value: 'bupyeong', label: '부평구' },
  ],
  daegu: [
    { value: 'suseong', label: '수성구' },
    { value: 'jung', label: '중구' },
  ],
  gwangju: [
    { value: 'seo', label: '서구' },
    { value: 'gwangsan', label: '광산구' },
  ],
};

const ageGroups = [
  { value: '20s', label: '20대', emoji: '🎓' },
  { value: '30s', label: '30대', emoji: '💼' },
  { value: '40s', label: '40대', emoji: '👨‍👩‍👧' },
  { value: '50s', label: '50대 이상', emoji: '👴' },
];

const footTrafficLevels = [
  { value: 'high', label: '높음', description: '시간당 500명 이상' },
  { value: 'medium', label: '보통', description: '시간당 200-500명' },
  { value: 'low', label: '낮음', description: '시간당 200명 미만' },
];

const competitorLevels = [
  { value: 'few', label: '적음', description: '반경 500m 내 5개 미만' },
  { value: 'medium', label: '보통', description: '반경 500m 내 5-10개' },
  { value: 'many', label: '많음', description: '반경 500m 내 10개 이상' },
];

export default function InputPage({ onSubmit, onBack, initialData }: InputPageProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<FormData>(initialData);
  const [direction, setDirection] = useState(1); // 1 for forward, -1 for backward

  const totalSteps = formData.advancedEnabled ? 7 : 5;
  const progress = (currentStep / totalSteps) * 100;

  const handleNext = () => {
    setDirection(1);
    setCurrentStep(currentStep + 1);
  };

  const handlePrevious = () => {
    setDirection(-1);
    setCurrentStep(currentStep - 1);
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.industry !== '';
      case 2:
        return formData.budget !== '';
      case 3:
        return formData.city !== '';
      case 4:
        return formData.district !== '';
      case 5:
        return true; // Advanced options toggle
      case 6:
        return formData.targetAge !== undefined && formData.targetAge !== '';
      case 7:
        return formData.footTraffic !== undefined && formData.footTraffic !== '';
      default:
        return true;
    }
  };

  const availableDistricts = formData.city ? districts[formData.city] || [] : [];

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction > 0 ? -300 : 300,
      opacity: 0,
    }),
  };

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={onBack}
            className="mb-4 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            메인으로
          </Button>
          
          <div className="flex items-center gap-2 mb-2">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-2 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-blue-900">JobFlex</span>
          </div>
          
          <h1 className="text-gray-900 mt-4 mb-2">
            창업 정보를 입력해주세요
          </h1>
          <p className="text-gray-600">
            단계별로 정보를 입력하시면 최적의 창업 입지를 분석해드립니다.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">진행률</span>
            <span className="text-sm text-blue-600">
              {currentStep} / {totalSteps}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Form Steps */}
        <Card className="p-8 shadow-lg border-gray-200 overflow-hidden">
          <div className="min-h-[400px] flex flex-col">
            <AnimatePresence mode="wait" custom={direction}>
              {/* Step 1: Industry Selection */}
              {currentStep === 1 && (
                <motion.div
                  key="step1"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">어떤 업종으로 창업하시나요?</h2>
                    <p className="text-gray-600 text-sm">업종을 선택해주세요</p>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {industries.map((industry) => {
                      const Icon = industry.icon;
                      return (
                        <motion.div
                          key={industry.value}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Card
                            className={`p-6 cursor-pointer transition-all ${
                              formData.industry === industry.value
                                ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                                : 'bg-white hover:shadow-md border-gray-200'
                            }`}
                            onClick={() => setFormData({ ...formData, industry: industry.value })}
                          >
                            <Icon className={`w-8 h-8 mb-3 ${
                              formData.industry === industry.value ? 'text-white' : 'text-blue-600'
                            }`} />
                            <p className={formData.industry === industry.value ? 'text-white' : 'text-gray-900'}>
                              {industry.label}
                            </p>
                          </Card>
                        </motion.div>
                      );
                    })}
                  </div>
                </motion.div>
              )}

              {/* Step 2: Budget */}
              {currentStep === 2 && (
                <motion.div
                  key="step2"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">창업 비용은 얼마인가요?</h2>
                    <p className="text-gray-600 text-sm">예상 창업 비용을 입력해주세요</p>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="budget">창업 비용 (만원)</Label>
                      <Input
                        id="budget"
                        type="number"
                        placeholder="예: 5000"
                        value={formData.budget}
                        onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                        className="mt-2 text-lg h-14"
                        autoFocus
                      />
                    </div>
                    
                    {/* Quick Select Buttons */}
                    <div className="grid grid-cols-3 gap-3">
                      {[3000, 5000, 10000].map((amount) => (
                        <Button
                          key={amount}
                          type="button"
                          variant="outline"
                          onClick={() => setFormData({ ...formData, budget: amount.toString() })}
                          className={formData.budget === amount.toString() ? 'border-blue-600 bg-blue-50' : ''}
                        >
                          {amount.toLocaleString()}만원
                        </Button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Step 3: City Selection */}
              {currentStep === 3 && (
                <motion.div
                  key="step3"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">어느 지역에서 창업하시나요?</h2>
                    <p className="text-gray-600 text-sm">시/도를 선택해주세요</p>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-3">
                    {cities.map((city) => (
                      <motion.div
                        key={city.value}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                      >
                        <Card
                          className={`p-5 cursor-pointer transition-all ${
                            formData.city === city.value
                              ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                              : 'bg-white hover:shadow-md border-gray-200'
                          }`}
                          onClick={() => setFormData({ ...formData, city: city.value, district: '' })}
                        >
                          <div className="flex items-center justify-between">
                            <p className={formData.city === city.value ? 'text-white' : 'text-gray-900'}>
                              {city.label}
                            </p>
                            {formData.city === city.value && (
                              <Check className="w-5 h-5 text-white" />
                            )}
                          </div>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Step 4: District Selection */}
              {currentStep === 4 && (
                <motion.div
                  key="step4"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">구/군을 선택해주세요</h2>
                    <p className="text-gray-600 text-sm">
                      {cities.find(c => c.value === formData.city)?.label}의 구/군을 선택해주세요
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-3">
                    {availableDistricts.map((district) => (
                      <motion.div
                        key={district.value}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                      >
                        <Card
                          className={`p-5 cursor-pointer transition-all ${
                            formData.district === district.value
                              ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                              : 'bg-white hover:shadow-md border-gray-200'
                          }`}
                          onClick={() => setFormData({ ...formData, district: district.value })}
                        >
                          <div className="flex items-center justify-between">
                            <p className={formData.district === district.value ? 'text-white' : 'text-gray-900'}>
                              {district.label}
                            </p>
                            {formData.district === district.value && (
                              <Check className="w-5 h-5 text-white" />
                            )}
                          </div>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Step 5: Advanced Options Toggle */}
              {currentStep === 5 && (
                <motion.div
                  key="step5"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">더 자세한 분석을 원하시나요?</h2>
                    <p className="text-gray-600 text-sm">추가 정보로 더 정확한 분석을 받아보세요</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <motion.div
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card
                        className={`p-8 cursor-pointer transition-all ${
                          formData.advancedEnabled
                            ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                            : 'bg-white hover:shadow-md border-gray-200'
                        }`}
                        onClick={() => setFormData({ ...formData, advancedEnabled: true })}
                      >
                        <div className="text-4xl mb-4">✨</div>
                        <h3 className={formData.advancedEnabled ? 'text-white mb-2' : 'text-gray-900 mb-2'}>
                          네, 자세히 분석할게요
                        </h3>
                        <p className={`text-sm ${formData.advancedEnabled ? 'text-blue-100' : 'text-gray-600'}`}>
                          고객층, 유동인구, 경쟁업체 등 추가 정보 입력
                        </p>
                      </Card>
                    </motion.div>

                    <motion.div
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card
                        className={`p-8 cursor-pointer transition-all ${
                          !formData.advancedEnabled
                            ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                            : 'bg-white hover:shadow-md border-gray-200'
                        }`}
                        onClick={() => setFormData({ ...formData, advancedEnabled: false })}
                      >
                        <div className="text-4xl mb-4">⚡</div>
                        <h3 className={!formData.advancedEnabled ? 'text-white mb-2' : 'text-gray-900 mb-2'}>
                          아니요, 빠르게 분석할게요
                        </h3>
                        <p className={`text-sm ${!formData.advancedEnabled ? 'text-blue-100' : 'text-gray-600'}`}>
                          기본 정보만으로 빠른 분석
                        </p>
                      </Card>
                    </motion.div>
                  </div>
                </motion.div>
              )}

              {/* Step 6: Target Age (Advanced) */}
              {currentStep === 6 && formData.advancedEnabled && (
                <motion.div
                  key="step6"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">주요 고객층은 누구인가요?</h2>
                    <p className="text-gray-600 text-sm">타겟 연령대를 선택해주세요</p>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {ageGroups.map((age) => (
                      <motion.div
                        key={age.value}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Card
                          className={`p-6 cursor-pointer transition-all text-center ${
                            formData.targetAge === age.value
                              ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                              : 'bg-white hover:shadow-md border-gray-200'
                          }`}
                          onClick={() => setFormData({ ...formData, targetAge: age.value })}
                        >
                          <div className="text-3xl mb-2">{age.emoji}</div>
                          <p className={formData.targetAge === age.value ? 'text-white' : 'text-gray-900'}>
                            {age.label}
                          </p>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Step 7: Foot Traffic and Competitors (Advanced) */}
              {currentStep === 7 && formData.advancedEnabled && (
                <motion.div
                  key="step7"
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.3 }}
                  className="flex-1"
                >
                  <div className="mb-6">
                    <h2 className="text-gray-900 mb-2">원하는 유동인구와 경쟁업체 수준은?</h2>
                    <p className="text-gray-600 text-sm">선호하는 상권 환경을 선택해주세요</p>
                  </div>
                  
                  <div className="space-y-6">
                    <div>
                      <Label className="mb-3 block">유동인구 수준</Label>
                      <div className="grid grid-cols-1 gap-3">
                        {footTrafficLevels.map((level) => (
                          <Card
                            key={level.value}
                            className={`p-4 cursor-pointer transition-all ${
                              formData.footTraffic === level.value
                                ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                                : 'bg-white hover:shadow-md border-gray-200'
                            }`}
                            onClick={() => setFormData({ ...formData, footTraffic: level.value })}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className={formData.footTraffic === level.value ? 'text-white' : 'text-gray-900'}>
                                  {level.label}
                                </p>
                                <p className={`text-sm ${formData.footTraffic === level.value ? 'text-blue-100' : 'text-gray-500'}`}>
                                  {level.description}
                                </p>
                              </div>
                              {formData.footTraffic === level.value && (
                                <Check className="w-5 h-5 text-white" />
                              )}
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>

                    <div>
                      <Label className="mb-3 block">경쟁업체 수</Label>
                      <div className="grid grid-cols-1 gap-3">
                        {competitorLevels.map((level) => (
                          <Card
                            key={level.value}
                            className={`p-4 cursor-pointer transition-all ${
                              formData.competitors === level.value
                                ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-400'
                                : 'bg-white hover:shadow-md border-gray-200'
                            }`}
                            onClick={() => setFormData({ ...formData, competitors: level.value })}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className={formData.competitors === level.value ? 'text-white' : 'text-gray-900'}>
                                  {level.label}
                                </p>
                                <p className={`text-sm ${formData.competitors === level.value ? 'text-blue-100' : 'text-gray-500'}`}>
                                  {level.description}
                                </p>
                              </div>
                              {formData.competitors === level.value && (
                                <Check className="w-5 h-5 text-white" />
                              )}
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 1}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                이전
              </Button>

              {currentStep === totalSteps ? (
                <Button
                  onClick={handleSubmit}
                  disabled={!canProceed()}
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
                  size="lg"
                >
                  분석 시작하기
                  <Sparkles className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
                >
                  다음
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
