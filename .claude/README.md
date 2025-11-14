# 상권분석 앱 프로젝트

## 프로젝트 개요
React와 TypeScript를 사용한 상권 분석 애플리케이션입니다.

## 기술 스택
- **프레임워크**: React + TypeScript
- **빌드 도구**: Vite
- **스타일링**: Tailwind CSS
- **애니메이션**: Framer Motion
- **상태 관리**: React Hooks (useState)

## 설치된 라이브러리 버전

### 주요 의존성 (dependencies)
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| react | ^19.2.0 | React 프레임워크 |
| react-dom | ^19.2.0 | React DOM 렌더링 |
| motion | ^12.23.24 | Framer Motion 애니메이션 라이브러리 |
| lucide-react | ^0.553.0 | 아이콘 라이브러리 |
| @radix-ui/react-slot | ^1.2.4 | Radix UI Slot 컴포넌트 |
| @radix-ui/react-progress | ^1.1.8 | Radix UI Progress 컴포넌트 |
| @radix-ui/react-label | ^2.1.8 | Radix UI Label 컴포넌트 |
| class-variance-authority | ^0.7.1 | CSS 클래스 관리 유틸리티 |
| clsx | ^2.1.1 | 조건부 클래스명 처리 |
| tailwind-merge | ^3.4.0 | Tailwind 클래스 병합 |

### 개발 의존성 (devDependencies)
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| typescript | ^5.9.3 | TypeScript 컴파일러 |
| @types/react | ^19.2.4 | React TypeScript 타입 정의 |
| @types/react-dom | ^19.2.3 | React DOM TypeScript 타입 정의 |
| vite | ^7.2.2 | 차세대 빌드 도구 |
| @vitejs/plugin-react | ^5.1.1 | Vite React 플러그인 |
| tailwindcss | ^4.1.17 | 유틸리티 우선 CSS 프레임워크 (v4) |
| @tailwindcss/postcss | ^4.1.17 | Tailwind CSS PostCSS 플러그인 |
| postcss | ^8.5.6 | CSS 변환 도구 |
| autoprefixer | ^10.4.22 | CSS 벤더 프리픽스 자동 추가 |

## 🚀 실행 방법

### 1. 개발 서버 실행
```bash
npm run dev
```
개발 서버가 `http://localhost:5173`에서 실행됩니다.

### 2. 프로덕션 빌드
```bash
npm run build
```
빌드된 파일은 `dist/` 폴더에 생성됩니다.

### 3. 프로덕션 미리보기
```bash
npm run preview
```
빌드된 파일을 로컬에서 미리 확인할 수 있습니다.

## 📦 새로운 PC에서 프로젝트 설정하기

### ⚠️ 중요: 설치 전 확인사항
- **Node.js 버전**: 18.x 이상 필요
- **npm 버전**: 9.x 이상 권장

### 단계별 설치 가이드

#### 1단계: 프로젝트 클론 또는 복사
```bash
# Git을 사용하는 경우
git clone <repository-url>
cd project

# 또는 프로젝트 폴더를 복사한 경우
cd project
```

#### 2단계: 의존성 설치
```bash
npm install
```

**설치될 주요 패키지:**
- React 19.2.0 및 React DOM
- TypeScript 5.9.3
- Vite 7.2.2 (빌드 도구)
- Tailwind CSS 4.1.17 (+ PostCSS 플러그인)
- Motion (Framer Motion) 12.23.24
- Radix UI 컴포넌트들 (Slot, Progress, Label)
- Lucide React 아이콘
- 유틸리티 라이브러리 (clsx, class-variance-authority, tailwind-merge)

#### 3단계: 개발 서버 실행
```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

### 🐛 문제 해결 (Troubleshooting)

#### 문제 1: Radix UI 의존성 에러
```
Error: Failed to resolve import "@radix-ui/react-slot@1.1.2"
```

**해결 방법:**
UI 컴포넌트의 import 구문에서 버전 번호 제거
```typescript
// ❌ 잘못된 예
import { Slot } from "@radix-ui/react-slot@1.1.2";

// ✅ 올바른 예
import { Slot } from "@radix-ui/react-slot";
```

이미 수정되어 있으므로 이 에러는 발생하지 않아야 합니다.

#### 문제 2: Tailwind CSS PostCSS 에러
```
Error: It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin
```

**해결 방법:**
`@tailwindcss/postcss` 패키지가 설치되어 있는지 확인
```bash
npm install --save-dev @tailwindcss/postcss
```

`postcss.config.js` 확인:
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},  // tailwindcss가 아닌 @tailwindcss/postcss 사용
    autoprefixer: {},
  },
}
```

#### 문제 3: Tailwind 스타일 미적용
**해결 방법:**
`styles/globals.css` 파일 첫 줄에 다음이 있는지 확인:
```css
@import "tailwindcss";
```

#### 문제 4: 모듈을 찾을 수 없음 (Module not found)
**해결 방법:**
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install

# Windows의 경우
rmdir /s /q node_modules
del package-lock.json
npm install
```

#### 문제 5: TypeScript 에러
**해결 방법:**
```bash
# TypeScript 컴파일 확인
npm run build
```

`tsconfig.json`의 경로 매핑이 올바른지 확인:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### 📋 설치 완료 체크리스트

프로젝트가 정상적으로 설정되었는지 확인:

- [ ] `npm install` 완료 (에러 없이)
- [ ] `npm run dev` 실행 시 서버 시작
- [ ] `http://localhost:5173` 접속 가능
- [ ] 메인 페이지가 올바르게 표시됨
- [ ] Tailwind CSS 스타일 적용됨 (그라데이션 배경, 버튼 스타일)
- [ ] 아이콘이 정상적으로 표시됨 (Lucide React)
- [ ] 페이지 전환 애니메이션 작동 (Framer Motion)

### 🔧 필요한 파일 확인

다음 파일들이 모두 존재하는지 확인:

**설정 파일:**
- ✅ `package.json` - 의존성 및 스크립트
- ✅ `tsconfig.json` - TypeScript 설정
- ✅ `vite.config.ts` - Vite 설정
- ✅ `tailwind.config.js` - Tailwind CSS 설정
- ✅ `postcss.config.js` - PostCSS 설정
- ✅ `index.html` - HTML 진입점

**소스 파일:**
- ✅ `src/main.tsx` - React 엔트리 포인트
- ✅ `App.tsx` - 메인 앱 컴포넌트
- ✅ `styles/globals.css` - 전역 CSS
- ✅ `components/` - 컴포넌트 디렉토리

### 🚀 빠른 시작 (한 줄 명령어)

```bash
npm install && npm run dev
```

이 명령어로 의존성 설치부터 개발 서버 실행까지 한번에 가능합니다.

## 주요 기능
1. 메인 페이지: 분석 시작
2. 입력 페이지: 업종, 예산, 지역 등 정보 입력
3. 결과 페이지: 분석 결과 표시

## 프로젝트 구조
```
project/
├── index.html               # HTML 진입점
├── vite.config.ts          # Vite 설정
├── tsconfig.json           # TypeScript 설정
├── tailwind.config.js      # Tailwind CSS 설정
├── postcss.config.js       # PostCSS 설정
├── package.json            # 프로젝트 메타데이터 및 의존성
├── src/
│   └── main.tsx           # React 엔트리 포인트
├── App.tsx                # 메인 앱 컴포넌트 (페이지 라우팅)
├── components/            # React 컴포넌트들
│   ├── MainPage.tsx      # 메인 랜딩 페이지
│   ├── InputPage.tsx     # 입력 폼 페이지
│   ├── ResultPage.tsx    # 결과 표시 페이지
│   ├── Chatbot.tsx       # 챗봇 컴포넌트
│   ├── ui/               # shadcn/ui 컴포넌트 라이브러리
│   └── figma/            # Figma 관련 컴포넌트
└── styles/
    └── globals.css        # 전역 CSS (Tailwind 설정)
```

## 데이터 구조
### FormData
- `industry`: 업종
- `budget`: 예산
- `city`: 시/도
- `district`: 구/군
- `advancedEnabled`: 고급 옵션 활성화 여부
- `targetAge?`: 타겟 연령대 (선택)
- `footTraffic?`: 유동인구 (선택)
- `competitors?`: 경쟁업체 (선택)

## 개발 가이드라인
- TypeScript를 사용하여 타입 안정성 확보
- 컴포넌트 기반 아키텍처 유지
- Framer Motion을 활용한 부드러운 페이지 전환
- 반응형 디자인 적용 (Tailwind CSS)

---

## 🔄 프로젝트 이관 시 주의사항

### Git 저장소 설정 (권장)
프로젝트를 다른 PC로 이관하기 전에 Git 저장소에 업로드하는 것을 권장합니다.

#### .gitignore 파일 확인
다음 항목들이 `.gitignore`에 포함되어 있어야 합니다:
```
node_modules/
dist/
.env
.DS_Store
*.log
.vscode/
```

#### 커밋 및 푸시
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repository-url>
git push -u origin main
```

### 압축 파일로 이관하는 경우

**포함해야 할 파일/폴더:**
```
✅ src/
✅ components/
✅ styles/
✅ .claude/
✅ package.json
✅ package-lock.json  (중요!)
✅ tsconfig.json
✅ tsconfig.node.json
✅ vite.config.ts
✅ tailwind.config.js
✅ postcss.config.js
✅ index.html
✅ App.tsx
✅ Attributions.md
```

**제외해도 되는 폴더:** (새로운 PC에서 `npm install`로 재생성)
```
❌ node_modules/
❌ dist/
❌ .vscode/
```

### 환경별 설정

#### Windows
```bash
# PowerShell 또는 CMD에서
npm install
npm run dev
```

#### macOS / Linux
```bash
npm install
npm run dev
```

---

## 🎓 추가 학습 자료

### 공식 문서
- [React 공식 문서](https://react.dev) - React 19 최신 기능
- [TypeScript 핸드북](https://www.typescriptlang.org/docs/) - TypeScript 기본
- [Vite 가이드](https://vitejs.dev) - Vite 빌드 도구
- [Tailwind CSS v4](https://tailwindcss.com) - 최신 Tailwind CSS
- [Framer Motion](https://www.framer.com/motion/) - 애니메이션 라이브러리
- [shadcn/ui](https://ui.shadcn.com/) - UI 컴포넌트 시스템

### 유용한 명령어

```bash
# 의존성 버전 확인
npm list

# 특정 패키지 버전 확인
npm list react

# 보안 취약점 확인
npm audit

# 보안 취약점 자동 수정
npm audit fix

# 패키지 업데이트 확인
npm outdated

# 캐시 클리어
npm cache clean --force
```

---

## 📞 지원 및 문의

문제가 발생하거나 질문이 있는 경우:

1. **문서 확인**: 이 README 및 ARCHITECTURE.md 문서 참고
2. **에러 메시지 검색**: 에러 메시지를 구글에 검색
3. **공식 문서 확인**: 관련 라이브러리 공식 문서 참고
4. **이슈 리포트**: GitHub Issues에 이슈 등록 (해당하는 경우)

---

## 📝 변경 이력

### v1.0.0 (2024-11-14)
- 초기 프로젝트 설정
- React 19 + TypeScript 5.9 + Vite 7 구성
- Tailwind CSS v4 적용
- shadcn/ui 컴포넌트 통합
- Radix UI 의존성 설치 및 import 구문 수정
- Tailwind PostCSS 플러그인 설정
- 3페이지 워크플로우 구현 (Main → Input → Result)
- Framer Motion 페이지 전환 애니메이션 추가
