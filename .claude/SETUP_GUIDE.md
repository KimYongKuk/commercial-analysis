# 🛠️ JobFlex 프로젝트 설치 완벽 가이드

## 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [새로운 PC에서 설치하기](#새로운-pc에서-설치하기)
3. [발생 가능한 모든 에러와 해결 방법](#발생-가능한-모든-에러와-해결-방법)
4. [프로젝트 이관 방법](#프로젝트-이관-방법)
5. [의존성 상세 설명](#의존성-상세-설명)

---

## 시스템 요구사항

### 필수 소프트웨어

| 소프트웨어 | 최소 버전 | 권장 버전 | 다운로드 링크 |
|-----------|----------|----------|-------------|
| Node.js | 18.0.0 | 20.x LTS | https://nodejs.org |
| npm | 9.0.0 | 10.x | Node.js와 함께 설치됨 |
| Git | 2.30.0 | 최신 버전 | https://git-scm.com |

### 시스템 사양
- **RAM**: 최소 4GB (8GB 권장)
- **디스크 공간**: 최소 500MB (node_modules 포함 시 ~200MB)
- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)

### 버전 확인 방법

```bash
# Node.js 버전 확인
node --version
# 출력 예: v20.11.0

# npm 버전 확인
npm --version
# 출력 예: 10.2.4

# Git 버전 확인 (선택사항)
git --version
# 출력 예: git version 2.43.0
```

버전이 요구사항을 만족하지 않으면 최신 버전으로 업데이트하세요.

---

## 새로운 PC에서 설치하기

### 방법 1: Git Clone (권장)

#### Windows (PowerShell/CMD)
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd project

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev
```

#### macOS/Linux (Terminal)
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd project

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev
```

### 방법 2: 압축 파일로 이관

#### 1단계: 원본 PC에서 압축 파일 만들기

**포함할 파일/폴더:**
```
project/
├── .claude/              ✅ (문서)
├── components/           ✅ (컴포넌트)
├── src/                  ✅ (소스)
├── styles/               ✅ (스타일)
├── .gitignore            ✅ (Git 설정)
├── App.tsx               ✅ (메인 앱)
├── index.html            ✅ (HTML)
├── package.json          ✅ (의존성 목록) ⭐ 필수
├── package-lock.json     ✅ (잠금 파일) ⭐ 필수
├── postcss.config.js     ✅ (PostCSS 설정)
├── tailwind.config.js    ✅ (Tailwind 설정)
├── tsconfig.json         ✅ (TypeScript 설정)
├── tsconfig.node.json    ✅ (Node TypeScript 설정)
├── vite.config.ts        ✅ (Vite 설정)
└── Attributions.md       ✅ (라이선스)

제외할 폴더:
├── node_modules/         ❌ (너무 큼, 재설치 가능)
├── dist/                 ❌ (빌드 결과물, 재생성 가능)
└── .vscode/              ❌ (에디터 설정, 개인별 다름)
```

**압축 명령어:**

Windows:
```powershell
# 탐색기에서 프로젝트 폴더 우클릭 → "압축"
# 또는 PowerShell에서:
Compress-Archive -Path project -DestinationPath jobflex-project.zip
```

macOS/Linux:
```bash
# node_modules 제외하고 압축
zip -r jobflex-project.zip project -x "project/node_modules/*" "project/dist/*"
```

#### 2단계: 새로운 PC에서 압축 해제 및 설치

```bash
# 1. 압축 해제
unzip jobflex-project.zip
cd project

# 2. 의존성 설치
npm install

# 3. 설치 확인
npm list --depth=0

# 4. 개발 서버 실행
npm run dev
```

### 설치 성공 확인

브라우저에서 `http://localhost:5173`을 열었을 때:
- ✅ 배경이 파란색-흰색-주황색 그라데이션으로 표시됨
- ✅ "JobFlex" 로고가 좌측 상단에 표시됨
- ✅ "내 입맛에 맞는 창업, AI가 도와드립니다" 제목이 표시됨
- ✅ "상권 분석하기" 버튼이 표시됨
- ✅ 3개의 기능 카드가 표시됨
- ✅ 아이콘이 정상적으로 표시됨

---

## 발생 가능한 모든 에러와 해결 방법

### 🔴 에러 1: "Failed to resolve import @radix-ui/react-slot@1.1.2"

#### 증상
```
[plugin:vite:import-analysis] Failed to resolve import "@radix-ui/react-slot@1.1.2"
from "components/ui/badge.tsx". Does the file exist?
```

#### 원인
UI 컴포넌트의 import 구문에 버전 번호가 포함되어 있음

#### 해결 방법 1: 자동 수정 (권장)
```bash
# Windows (PowerShell)
cd components/ui
Get-ChildItem -Filter *.tsx | ForEach-Object {
    (Get-Content $_.FullName) -replace '@radix-ui/react-([a-z-]+)@[0-9.]+', '@radix-ui/react-$1' |
    Set-Content $_.FullName
}

# macOS/Linux
cd components/ui
find . -name "*.tsx" -exec sed -i 's/@radix-ui\/react-\([a-z-]*\)@[0-9.]*/@radix-ui\/react-\1/g' {} \;
```

#### 해결 방법 2: 수동 수정
각 UI 컴포넌트 파일을 열어서 다음과 같이 수정:

**수정 전:**
```typescript
import { Slot } from "@radix-ui/react-slot@1.1.2";
```

**수정 후:**
```typescript
import { Slot } from "@radix-ui/react-slot";
```

영향받는 파일들:
- `components/ui/badge.tsx`
- `components/ui/button.tsx`
- `components/ui/progress.tsx`
- `components/ui/label.tsx`
- 기타 UI 컴포넌트 파일들

---

### 🔴 에러 2: Tailwind CSS PostCSS 플러그인 에러

#### 증상
```
[postcss] It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin.
The PostCSS plugin has moved to a separate package.
```

#### 원인
Tailwind CSS v4는 별도의 PostCSS 플러그인 패키지가 필요함

#### 해결 방법

**1단계: 패키지 설치**
```bash
npm install --save-dev @tailwindcss/postcss
```

**2단계: postcss.config.js 수정**

파일 위치: `postcss.config.js`

```javascript
// ❌ 잘못된 설정
export default {
  plugins: {
    tailwindcss: {},    // 이렇게 하면 안됨
    autoprefixer: {},
  },
}

// ✅ 올바른 설정
export default {
  plugins: {
    '@tailwindcss/postcss': {},  // @tailwindcss/postcss 사용
    autoprefixer: {},
  },
}
```

**3단계: globals.css 확인**

파일 위치: `styles/globals.css`

파일 맨 위에 다음 줄이 있는지 확인:
```css
@import "tailwindcss";
```

없다면 추가:
```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  /* ... */
}
```

---

### 🔴 에러 3: "Cannot find module 'react'"

#### 증상
```
Error: Cannot find module 'react'
Require stack: ...
```

#### 원인
- `node_modules`가 손상되었거나
- 의존성 설치가 제대로 안됨
- `package-lock.json`이 없음

#### 해결 방법

**옵션 A: 클린 설치 (권장)**
```bash
# 1. 기존 node_modules와 lock 파일 삭제
# Windows
rmdir /s /q node_modules
del package-lock.json

# macOS/Linux
rm -rf node_modules package-lock.json

# 2. 캐시 클리어
npm cache clean --force

# 3. 재설치
npm install
```

**옵션 B: React만 재설치**
```bash
npm install react react-dom
```

---

### 🔴 에러 4: "Module not found: Error: Can't resolve './utils'"

#### 증상
```
Module not found: Error: Can't resolve './utils'
```

#### 원인
`components/ui/utils.ts` 파일이 없음

#### 해결 방법

`components/ui/utils.ts` 파일 생성:

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

### 🔴 에러 5: TypeScript 컴파일 에러

#### 증상
```
error TS2307: Cannot find module '@/components/...' or its corresponding type declarations
```

#### 원인
TypeScript 경로 매핑이 잘못 설정됨

#### 해결 방법

**tsconfig.json 확인 및 수정:**

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    },
    // ... 기타 설정
  },
  "include": ["src", "components", "App.tsx", "styles"]
}
```

**vite.config.ts 확인:**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
```

---

### 🔴 에러 6: "EACCES: permission denied"

#### 증상
```
Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules/...'
```

#### 원인
npm 전역 패키지 설치 권한 문제

#### 해결 방법

**Windows:**
PowerShell을 관리자 권한으로 실행

**macOS/Linux:**
```bash
# 옵션 1: sudo 사용 (비권장)
sudo npm install

# 옵션 2: npm 디렉토리 권한 변경 (권장)
sudo chown -R $USER /usr/local/lib/node_modules
```

---

### 🔴 에러 7: "Port 5173 is already in use"

#### 증상
```
Port 5173 is already in use
```

#### 원인
다른 프로세스가 이미 5173 포트를 사용 중

#### 해결 방법

**옵션 A: 다른 포트 사용**
```bash
npm run dev -- --port 5174
```

**옵션 B: 기존 프로세스 종료**

Windows:
```powershell
# 5173 포트 사용 중인 프로세스 찾기
netstat -ano | findstr :5173

# 프로세스 종료 (PID는 위 명령어 결과에서 확인)
taskkill /PID <PID> /F
```

macOS/Linux:
```bash
# 5173 포트 사용 중인 프로세스 찾기
lsof -i :5173

# 프로세스 종료
kill -9 <PID>
```

---

### 🔴 에러 8: "npm ERR! code ERESOLVE"

#### 증상
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

#### 원인
의존성 버전 충돌

#### 해결 방법

**옵션 A: 강제 설치 (권장)**
```bash
npm install --legacy-peer-deps
```

**옵션 B: package-lock.json 사용**
```bash
# package-lock.json이 있다면
npm ci
```

---

### 🔴 에러 9: Tailwind 스타일이 적용되지 않음

#### 증상
- 페이지가 표시되지만 스타일이 없음
- 배경이 흰색, 버튼이 기본 스타일

#### 원인
- Tailwind CSS가 제대로 설정되지 않음
- `globals.css` import가 누락됨

#### 해결 방법

**1단계: globals.css import 확인**

`src/main.tsx` 파일:
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from '../App.tsx'
import '../styles/globals.css'  // ⭐ 이 줄이 있는지 확인

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**2단계: globals.css 첫 줄 확인**
```css
@import "tailwindcss";  /* ⭐ 이 줄이 반드시 필요 */
```

**3단계: tailwind.config.js 확인**
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./App.tsx",
  ],
  // ...
}
```

**4단계: 개발 서버 재시작**
```bash
# Ctrl+C로 서버 종료 후
npm run dev
```

---

## 프로젝트 이관 방법

### 체크리스트

프로젝트를 다른 PC로 이관하기 전에 확인:

- [ ] `package.json` 파일 존재
- [ ] `package-lock.json` 파일 존재 (⭐ 매우 중요!)
- [ ] 모든 설정 파일 존재 (tsconfig, vite.config, etc.)
- [ ] `node_modules`와 `dist` 폴더 제외
- [ ] `.gitignore` 파일 포함 (Git 사용 시)
- [ ] 소스 코드 파일 모두 포함

### Git을 사용한 이관 (권장)

**원본 PC:**
```bash
# 1. Git 저장소 초기화 (처음 한번만)
git init

# 2. .gitignore 확인
# (이미 생성되어 있음)

# 3. 파일 추가 및 커밋
git add .
git commit -m "Initial commit: JobFlex 프로젝트"

# 4. 원격 저장소 추가
git remote add origin <your-github-repo-url>

# 5. 푸시
git push -u origin main
```

**새로운 PC:**
```bash
# 1. 클론
git clone <your-github-repo-url>
cd project

# 2. 의존성 설치
npm install

# 3. 실행
npm run dev
```

### USB/클라우드를 사용한 이관

**원본 PC에서 압축:**
```bash
# 1. 불필요한 폴더 삭제
rm -rf node_modules dist

# 2. 압축
zip -r jobflex-backup.zip .
```

**새로운 PC에서 복원:**
```bash
# 1. 압축 해제
unzip jobflex-backup.zip

# 2. 의존성 설치
npm install

# 3. 실행
npm run dev
```

---

## 의존성 상세 설명

### 주요 의존성 (dependencies)

#### React 생태계
```json
{
  "react": "^19.2.0",
  "react-dom": "^19.2.0"
}
```
- **용도**: 핵심 React 라이브러리
- **필수 여부**: ✅ 필수
- **재설치 필요**: 삭제 시 반드시 재설치

#### 애니메이션
```json
{
  "motion": "^12.23.24"
}
```
- **용도**: Framer Motion - 페이지 전환 애니메이션
- **필수 여부**: ✅ 필수 (페이지 전환에 사용)
- **대체 가능**: react-spring, gsap

#### UI 컴포넌트
```json
{
  "@radix-ui/react-slot": "^1.2.4",
  "@radix-ui/react-progress": "^1.1.8",
  "@radix-ui/react-label": "^2.1.8"
}
```
- **용도**: shadcn/ui의 기반 컴포넌트
- **필수 여부**: ✅ 필수 (UI 컴포넌트에서 사용)
- **주의**: 버전 번호 없이 import 해야 함

#### 아이콘
```json
{
  "lucide-react": "^0.553.0"
}
```
- **용도**: 아이콘 라이브러리
- **필수 여부**: ✅ 필수 (MainPage에서 사용)
- **대체 가능**: react-icons, heroicons

#### CSS 유틸리티
```json
{
  "class-variance-authority": "^0.7.1",
  "clsx": "^2.1.1",
  "tailwind-merge": "^3.4.0"
}
```
- **용도**: 조건부 CSS 클래스 처리
- **필수 여부**: ✅ 필수 (UI 컴포넌트에서 사용)
- **주의**: 세 가지 모두 필요

### 개발 의존성 (devDependencies)

#### TypeScript
```json
{
  "typescript": "^5.9.3",
  "@types/react": "^19.2.4",
  "@types/react-dom": "^19.2.3"
}
```
- **용도**: TypeScript 컴파일러 및 타입 정의
- **필수 여부**: ✅ 필수
- **주의**: 버전 호환성 중요

#### 빌드 도구
```json
{
  "vite": "^7.2.2",
  "@vitejs/plugin-react": "^5.1.1"
}
```
- **용도**: 번들러 및 개발 서버
- **필수 여부**: ✅ 필수
- **대체 불가**: 프로젝트가 Vite 기반

#### Tailwind CSS
```json
{
  "tailwindcss": "^4.1.17",
  "@tailwindcss/postcss": "^4.1.17",
  "postcss": "^8.5.6",
  "autoprefixer": "^10.4.22"
}
```
- **용도**: CSS 프레임워크 및 PostCSS 처리
- **필수 여부**: ✅ 필수
- **주의**: `@tailwindcss/postcss` 플러그인 필수

---

## 빠른 참조

### 일반적인 명령어

```bash
# 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview

# 타입 체크
tsc --noEmit

# 의존성 목록
npm list --depth=0

# 패키지 업데이트 확인
npm outdated

# 보안 취약점 확인
npm audit
```

### 트러블슈팅 명령어

```bash
# 클린 설치
rm -rf node_modules package-lock.json && npm install

# 캐시 클리어
npm cache clean --force

# 특정 패키지 재설치
npm uninstall <package-name>
npm install <package-name>

# 강제 설치
npm install --force

# 레거시 peer deps
npm install --legacy-peer-deps
```

---

## 연락처 및 지원

문제가 해결되지 않는 경우:

1. ✅ 이 문서를 다시 확인
2. ✅ ARCHITECTURE.md 참고
3. ✅ 에러 메시지 전체를 구글에 검색
4. ✅ 공식 문서 확인 (React, Vite, Tailwind)
5. ✅ GitHub Issues 등록

---

**마지막 업데이트**: 2024-11-14
**문서 버전**: 1.0.0
