# 🚀 JobFlex - 빠른 시작 가이드

## 새로운 PC에서 5분 안에 실행하기

### 전제조건
- ✅ Node.js 18+ 설치됨 (`node --version`으로 확인)
- ✅ npm 9+ 설치됨 (`npm --version`으로 확인)

### 3단계로 실행하기

```bash
# 1️⃣ 프로젝트 폴더로 이동
cd project

# 2️⃣ 의존성 설치 (3-5분 소요)
npm install

# 3️⃣ 개발 서버 실행
npm run dev
```

브라우저에서 자동으로 `http://localhost:5173` 열림!

---

## ⚠️ 에러 발생 시

### "Failed to resolve import @radix-ui" 에러
```bash
# 이미 해결되어 있어야 함
# 만약 발생하면 UI 컴포넌트 import에서 @버전 제거
```

### "tailwindcss PostCSS" 에러
```bash
# @tailwindcss/postcss 설치 확인
npm install --save-dev @tailwindcss/postcss
```

### 스타일이 안 보임
`styles/globals.css` 첫 줄에 `@import "tailwindcss";` 있는지 확인

### 기타 모든 에러
```bash
# 클린 설치
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 상세 문서

- **README.md**: 프로젝트 개요 및 라이브러리 정보
- **.claude/SETUP_GUIDE.md**: 완벽한 설치 가이드 (모든 에러 해결법)
- **.claude/ARCHITECTURE.md**: 프로젝트 구조 상세 설명

---

## 🎯 이관 체크리스트

다른 PC로 복사할 때 포함해야 할 파일:

✅ **필수:**
- `package.json` ⭐
- `package-lock.json` ⭐
- `tsconfig.json`
- `vite.config.ts`
- `tailwind.config.js`
- `postcss.config.js`
- `index.html`
- `src/`, `components/`, `styles/` 폴더
- `App.tsx`

❌ **제외:**
- `node_modules/` (재설치)
- `dist/` (재생성)
- `.vscode/` (개인 설정)

---

**한 줄 명령어:**
```bash
npm install && npm run dev
```

성공! 🎉
