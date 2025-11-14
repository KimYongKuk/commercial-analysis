type HeatmapData = {
  district: string;
  lat: number;
  lng: number;
  count: number;
  density: number;
  avgRent: number;
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

/**
 * HeatmapData를 Location 형식으로 변환
 * Chatbot에서 사용할 수 있도록 분석 결과 형태로 변환
 */
export function transformHeatmapToLocations(
  data: HeatmapData[],
  industry: string
): Location[] {
  const industryLabels: Record<string, string> = {
    cafe: '카페',
    restaurant: '음식점',
    beauty: '미용실',
    convenience: '편의점',
    retail: '소매점',
    fitness: '헬스장',
  };

  const industryName = industryLabels[industry] || industry;

  return data.map((item, index) => {
    // 밀집도 기반 점수 계산 (density를 기반으로 100점 만점)
    const score = Math.min(100, Math.round(item.density + (item.count / 50)));

    // 임대료 역산 점수 (임대료가 낮을수록 높은 점수)
    const rentScore = Math.max(40, 100 - Math.round(item.avgRent / 5));

    // 밀집도 기반 경쟁 점수 (밀집도가 높으면 경쟁도 높음)
    const competitionScore = item.density;

    // 매장 수 기반 유동인구 추정
    const footTrafficScore = Math.min(100, Math.round(item.count / 15 + 20));

    // 입지 점수 (밀집도와 매장 수 종합)
    const locationScore = Math.min(100, Math.round((item.density + item.count / 20) / 2 + 30));

    return {
      id: index + 1,
      name: item.district,
      score,
      lat: item.lat,
      lng: item.lng,
      metrics: {
        location: locationScore,
        footTraffic: footTrafficScore,
        rent: rentScore,
        competition: competitionScore,
      },
      descriptions: {
        location: `${item.district}는 ${industryName} 업종이 ${item.count}개 밀집된 상권으로 입지 조건이 ${locationScore >= 80 ? '매우 우수' : locationScore >= 60 ? '우수' : '양호'}합니다.`,
        footTraffic: `현재 ${item.count}개의 ${industryName}가 운영 중이며, ${item.density >= 80 ? '매우 높은' : item.density >= 60 ? '높은' : '적정한'} 유동인구를 보유하고 있습니다.`,
        rent: `평균 임대료는 ${item.avgRent}만원으로 ${rentScore >= 80 ? '매우 합리적인' : rentScore >= 60 ? '적정한' : '다소 높은'} 수준입니다.`,
        competition: `밀집도 ${item.density}점으로 경쟁 강도가 ${competitionScore >= 80 ? '높은 편' : competitionScore >= 60 ? '중간 정도' : '낮은 편'}입니다. ${competitionScore >= 80 ? '차별화 전략이 필요합니다.' : competitionScore >= 60 ? '적정한 경쟁 환경입니다.' : '진입 장벽이 낮습니다.'}`,
      },
    };
  });
}
