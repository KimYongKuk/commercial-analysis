import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { MessageCircle, X, Send, Sparkles } from 'lucide-react';
import type { FormData } from '../App';

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

type ChatbotProps = {
  isOpen: boolean;
  onToggle: () => void;
  formData?: FormData;
  locations: Location[];
  title?: string;
  welcomeMessage?: string;
};

type Message = {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
};

export default function Chatbot({ isOpen, onToggle, formData, locations, title, welcomeMessage }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: welcomeMessage || '안녕하세요! JobFlex AI입니다. 분석 결과에 대해 궁금하신 점이 있으시면 언제든 물어보세요. 😊',
      sender: 'ai',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const currentInput = inputValue;  // 입력값 저장
    setInputValue('');

    // 최근 10개 대화만 선택 (첫 번째 환영 메시지 제외)
    const MAX_HISTORY = 10;
    const recentMessages = [...messages, userMessage]
      .filter(msg => !(msg.id === 1 && msg.sender === 'ai'))  // 환영 메시지 제외
      .slice(-MAX_HISTORY);  // 최근 10개만

    // OpenAI 형식으로 변환
    const conversationHistory = recentMessages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text
    }));

    // 🔍 로깅: 전송할 데이터 확인
    console.log('📤 [Chatbot] 전송할 메시지:', currentInput);
    console.log('📤 [Chatbot] 대화 히스토리 개수:', conversationHistory.length);
    console.log('📤 [Chatbot] 대화 히스토리:', conversationHistory);

    // 실제 FastAPI 백엔드 호출
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          analysis_results: locations,  // 분석 결과 포함
          conversation_history: conversationHistory,  // 대화 히스토리 포함
        }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data = await response.json();

      // 🔍 로깅: 받은 응답 확인
      console.log('📥 [Chatbot] AI 응답:', data.reply);

      const aiResponse: Message = {
        id: messages.length + 2,
        text: data.reply,  // OpenAI API 응답 사용
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      // 에러 발생 시 사용자에게 알림
      const errorMessage: Message = {
        id: messages.length + 2,
        text: '죄송합니다. 서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요. 😔',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('챗봇 API 호출 오류:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Chat Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="fixed bottom-8 right-8 z-50"
          >
            <Button
              onClick={onToggle}
              size="lg"
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-full w-16 h-16 shadow-lg hover:shadow-xl transition-all"
            >
              <MessageCircle className="w-6 h-6" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-8 right-8 w-96 z-50"
          >
            <Card className="shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="bg-white/20 p-2 rounded-lg">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3>{title || 'JobFlex AI'}</h3>
                    <p className="text-xs text-orange-100">무엇이든 물어보세요</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggle}
                  className="text-white hover:bg-white/20"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Messages */}
              <div className="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.sender === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-900 shadow-sm'
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Input */}
              <div className="p-4 bg-white border-t border-gray-200">
                <div className="flex gap-2">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="메시지를 입력하세요..."
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!inputValue.trim()}
                    className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

