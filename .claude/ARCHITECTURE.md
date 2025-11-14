# 🏗️ 프로젝트 아키텍처 가이드

## 📝 프로젝트 개요

**JobFlex**는 AI 기반 상권 분석 웹 애플리케이션입니다. 사용자가 업종, 예산, 지역 정보를 입력하면 최적의 창업 입지를 추천해주는 서비스입니다.

---

## 🎯 핵심 개념

### 페이지 구조
애플리케이션은 3개의 주요 페이지로 구성됩니다:

1. **메인 페이지** (`MainPage.tsx`)
   - 서비스 소개 및 시작 버튼
   - 주요 기능 카드 표시
   - 애니메이션 효과로 사용자 경험 향상

2. **입력 페이지** (`InputPage.tsx`)
   - 사용자 정보 입력 폼
   - 업종, 예산, 지역 선택
   - 고급 옵션 (타겟 연령대, 유동인구, 경쟁업체)

3. **결과 페이지** (`ResultPage.tsx`)
   - 분석 결과 표시
   - 입력한 데이터 기반 추천

### 상태 관리
- `App.tsx`에서 전역 상태 관리
- `useState`를 사용한 간단한 상태 관리
- `currentPage`: 현재 페이지 추적 ('main' | 'input' | 'result')
- `formData`: 사용자 입력 데이터 저장

### 데이터 흐름
```
MainPage → InputPage → ResultPage
   ↓           ↓            ↓
시작 버튼  → 폼 작성  →  결과 확인
              ↓
         formData 저장
```

---

## 🗂️ 파일 구조 상세 설명

### 진입점 파일들

#### `index.html`
```html
<!-- HTML 진입점 -->
- React 앱이 마운트될 <div id="root"> 제공
- main.tsx 스크립트 로드
```

#### `src/main.tsx`
```typescript
// React 애플리케이션 진입점
- ReactDOM을 통해 App 컴포넌트를 #root에 렌더링
- 전역 CSS (globals.css) 임포트
- StrictMode로 개발 시 경고 활성화
```

#### `App.tsx`
```typescript
// 메인 애플리케이션 컴포넌트
- 페이지 라우팅 로직
- 상태 관리 (currentPage, formData)
- Framer Motion을 사용한 페이지 전환 애니메이션
```

---

## 🎨 UI 컴포넌트 구조

### shadcn/ui 컴포넌트
`components/ui/` 폴더에는 50개 이상의 재사용 가능한 UI 컴포넌트가 있습니다:

- **Button, Input, Select**: 기본 폼 요소
- **Card, Dialog, Sheet**: 레이아웃 컴포넌트
- **Table, Chart**: 데이터 표시 컴포넌트
- **Accordion, Tabs**: 인터랙티브 컴포넌트

이들은 모두 Tailwind CSS 기반으로 스타일링되어 있으며, `class-variance-authority`를 통해 variant 관리가 가능합니다.

### 커스텀 컴포넌트

#### `components/MainPage.tsx`
- 랜딩 페이지 UI
- 특징 카드 (FeatureCard) 표시
- Lucide React 아이콘 사용
- Framer Motion 애니메이션

#### `components/InputPage.tsx`
- 사용자 입력 폼
- shadcn/ui 폼 컴포넌트 활용
- 조건부 렌더링 (고급 옵션)

#### `components/ResultPage.tsx`
- 분석 결과 표시
- FormData를 props로 받아서 처리

#### `components/Chatbot.tsx`
- AI 챗봇 기능 (추후 확장 가능)

---

## ⚙️ 설정 파일 설명

### `vite.config.ts`
```typescript
// Vite 빌드 도구 설정
- React 플러그인 활성화
- 경로 alias 설정 (@/ → 루트 디렉토리)
- 개발 서버 및 빌드 최적화
```

### `tsconfig.json`
```json
// TypeScript 컴파일러 설정
- ES2020 타겟
- React JSX 지원
- strict 모드 활성화
- 경로 매핑 (@/* 별칭)
```

### `tailwind.config.js`
```javascript
// Tailwind CSS 설정
- content: 스캔할 파일 경로 지정
- theme: 커스텀 테마 확장
- plugins: 플러그인 추가
```

### `postcss.config.js`
```javascript
// PostCSS 설정
- Tailwind CSS 플러그인
- Autoprefixer (벤더 프리픽스 자동 추가)
```

---

## 🎭 스타일링 시스템

### Tailwind CSS
- **유틸리티 우선** 접근 방식
- `globals.css`에 기본 설정 및 커스텀 변수 정의
- CSS 변수를 통한 테마 관리 (라이트/다크 모드)

### CSS 변수 구조
```css
:root {
  --background: #ffffff;
  --foreground: oklch(...);
  --primary: #030213;
  /* ... 더 많은 변수 */
}

.dark {
  --background: oklch(...);
  /* 다크 모드 오버라이드 */
}
```

### 타이포그래피
`globals.css`에서 기본 타이포그래피 스타일 정의:
- h1, h2, h3, h4: 헤딩 스타일
- p: 본문 텍스트
- label, button, input: 폼 요소

---

## 🔄 애니메이션 시스템

### Framer Motion
- `motion` 라이브러리 사용
- 페이지 전환 애니메이션
- `AnimatePresence`로 컴포넌트 언마운트 애니메이션

#### 애니메이션 패턴
```typescript
<motion.div
  initial={{ opacity: 0, y: 30 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, x: -50 }}
  transition={{ duration: 0.3 }}
>
```

---

## 🛠️ 개발 워크플로우

### 1. 개발 시작
```bash
npm run dev
```
- Vite 개발 서버 실행
- Hot Module Replacement (HMR) 활성화
- `http://localhost:5173` 접속

### 2. 코드 수정
- TypeScript 파일 수정 시 자동 타입 체크
- CSS 수정 시 즉시 반영
- 컴포넌트 수정 시 HMR로 즉시 업데이트

### 3. 빌드
```bash
npm run build
```
- TypeScript 컴파일 (`tsc`)
- Vite 번들링
- `dist/` 폴더에 최적화된 파일 생성

### 4. 미리보기
```bash
npm run preview
```
- 프로덕션 빌드 로컬 서버에서 테스트

---

## 📊 데이터 타입 시스템

### FormData 타입
```typescript
export type FormData = {
  industry: string;        // 업종
  budget: string;          // 예산
  city: string;            // 시/도
  district: string;        // 구/군
  advancedEnabled: boolean; // 고급 옵션 활성화
  targetAge?: string;      // 타겟 연령대 (선택)
  footTraffic?: string;    // 유동인구 (선택)
  competitors?: string;    // 경쟁업체 (선택)
};
```

---

## 🎯 확장 가능성

### 추가 가능한 기능
1. **라우터 추가**: React Router로 URL 기반 라우팅
2. **상태 관리 강화**: Zustand, Redux Toolkit
3. **API 연동**: 실제 상권 데이터 API 연동
4. **인증**: 사용자 로그인/회원가입
5. **데이터 시각화**: Chart.js, Recharts로 그래프 표시
6. **지도 통합**: Kakao Maps API, Google Maps API

### 성능 최적화
1. **코드 스플리팅**: React.lazy, Suspense
2. **이미지 최적화**: WebP, lazy loading
3. **번들 최적화**: Vite의 tree-shaking 활용
4. **메모이제이션**: React.memo, useMemo, useCallback

---

## 🔍 디버깅 가이드

### TypeScript 에러
```bash
# 타입 체크
npm run build
```

### 개발자 도구
- React DevTools 확장 프로그램 사용
- Vite의 상세한 에러 메시지 확인
- 브라우저 콘솔에서 경고/에러 확인

### 일반적인 문제 해결
1. **모듈을 찾을 수 없음**: `npm install` 재실행
2. **타입 에러**: `tsconfig.json` 설정 확인
3. **스타일 미적용**: Tailwind content 경로 확인
4. **HMR 작동 안함**: 개발 서버 재시작

---

## 📚 추가 학습 자료

- [React 공식 문서](https://react.dev)
- [Vite 가이드](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Framer Motion](https://www.framer.com/motion/)
- [TypeScript 핸드북](https://www.typescriptlang.org/docs/)
