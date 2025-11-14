# 한국어 코딩 스타일 가이드

## 기본 원칙
- 코드는 영어로, 주석과 문서는 한국어로 작성
- 변수명과 함수명은 명확하고 의미 있는 영어 단어 사용
- 한국어 주석은 필요한 경우에만 사용하여 코드의 의도를 명확히 설명

## TypeScript 규칙
- 모든 함수와 변수에 명시적인 타입 지정
- `any` 타입 사용 최소화
- 인터페이스와 타입 별칭을 적절히 활용

## React 컴포넌트
- 함수형 컴포넌트 우선 사용
- Props는 인터페이스로 정의
- Custom hooks는 `use` 접두사 사용
- 컴포넌트명은 PascalCase

## 네이밍 컨벤션
- 컴포넌트: PascalCase (예: `MainPage`, `InputForm`)
- 함수/변수: camelCase (예: `handleSubmit`, `formData`)
- 상수: UPPER_SNAKE_CASE (예: `API_URL`, `MAX_LENGTH`)
- 파일명: PascalCase (컴포넌트), camelCase (유틸리티)

## 스타일링
- Tailwind CSS 유틸리티 클래스 우선 사용
- 반복되는 스타일은 컴포넌트로 추출
- 반응형 디자인 고려 (모바일 우선)

## 주석 작성
```typescript
// ✅ 좋은 예: 복잡한 로직 설명
// 사용자가 고급 옵션을 활성화한 경우에만 추가 필드 표시
if (advancedEnabled) {
  // ...
}

// ❌ 나쁜 예: 불필요한 주석
// 버튼 클릭 핸들러
const handleClick = () => {
  // ...
}
```
