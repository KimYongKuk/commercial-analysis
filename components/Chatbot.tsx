import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { MessageCircle, X, Send, Sparkles, Maximize2, Minimize2 } from 'lucide-react';
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
  isExpanded?: boolean;
  onExpandToggle?: () => void;
};

type Message = {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isStreaming?: boolean;  // 스트리밍 중 여부
};

export default function Chatbot({ isOpen, onToggle, formData, locations, title, welcomeMessage, isExpanded: externalExpanded, onExpandToggle }: ChatbotProps) {
  const [internalExpanded, setInternalExpanded] = useState(false);
  const isExpanded = externalExpanded !== undefined ? externalExpanded : internalExpanded;

  const handleExpandToggle = () => {
    if (onExpandToggle) {
      onExpandToggle();
    } else {
      setInternalExpanded(!internalExpanded);
    }
  };

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: welcomeMessage || '안녕하세요! JobFlex AI입니다. 분석 결과에 대해 궁금하신 점이 있으시면 언제든 물어보세요. 😊',
      sender: 'ai',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [conversationId, setConversationId] = useState('');  // MISO 대화 ID
  const [isLoading, setIsLoading] = useState(false);  // 로딩 상태

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    // 🔍 로깅: 전송할 데이터 확인
    console.log('📤 [Chatbot] MISO API 전송:', currentInput);
    console.log('📤 [Chatbot] conversation_id:', conversationId);

    // MISO API 스트리밍 호출
    try {
      const response = await fetch('http://localhost:8000/api/miso-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentInput,
          conversation_id: conversationId,
          user: 'user-001',
          inputs: {},
        }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      // 스트리밍 응답을 위한 AI 메시지 생성
      const aiMessageId = messages.length + 2;
      const aiMessage: Message = {
        id: aiMessageId,
        text: '',
        sender: 'ai',
        timestamp: new Date(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, aiMessage]);

      // SSE 스트리밍 처리
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let currentContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data:')) {
              try {
                const jsonStr = line.slice(5).trim();
                if (!jsonStr || jsonStr === '[DONE]') continue;

                const data = JSON.parse(jsonStr);

                // 에러 이벤트 처리
                if (data.event === 'error') {
                  currentContent = data.message || '오류가 발생했습니다.';
                  setMessages((prev: Message[]) =>
                    prev.map((msg: Message) =>
                      msg.id === aiMessageId
                        ? { ...msg, text: currentContent, isStreaming: false }
                        : msg
                    )
                  );
                  break;
                }

                // conversation_id 저장
                if (data.conversation_id) {
                  setConversationId(data.conversation_id);
                }

                // 이벤트 타입에 따른 처리
                if (data.event === 'agent_message' || data.event === 'message') {
                  // 메시지 내용 추가
                  if (data.answer) {
                    currentContent += data.answer;
                  }
                } else if (data.event === 'message_replace') {
                  // 전체 메시지 대체
                  currentContent = data.answer || '';
                }

                // UI 업데이트
                setMessages((prev: Message[]) =>
                  prev.map((msg: Message) =>
                    msg.id === aiMessageId
                      ? { ...msg, text: currentContent }
                      : msg
                  )
                );
              } catch (e) {
                console.error('JSON 파싱 오류:', e, line);
              }
            }
          }
        }
      }

      // 스트리밍 완료
      setMessages((prev: Message[]) =>
        prev.map((msg: Message) =>
          msg.id === aiMessageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );

      console.log('📥 [Chatbot] MISO 응답 완료:', currentContent.slice(0, 100));

    } catch (error) {
      const errorMessage: Message = {
        id: messages.length + 2,
        text: '죄송합니다. 서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('챗봇 API 호출 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /* ============================================
   * 기존 OpenAI API 호출 로직 (주석 처리)
   * ============================================
  const handleSendLegacy = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const currentInput = inputValue;
    setInputValue('');

    // 최근 10개 대화만 선택 (첫 번째 환영 메시지 제외)
    const MAX_HISTORY = 10;
    const recentMessages = [...messages, userMessage]
      .filter(msg => !(msg.id === 1 && msg.sender === 'ai'))
      .slice(-MAX_HISTORY);

    // OpenAI 형식으로 변환
    const conversationHistory = recentMessages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text
    }));

    console.log('📤 [Chatbot] 전송할 메시지:', currentInput);
    console.log('📤 [Chatbot] 대화 히스토리 개수:', conversationHistory.length);
    console.log('📤 [Chatbot] 대화 히스토리:', conversationHistory);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          analysis_results: locations,
          conversation_history: conversationHistory,
        }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data = await response.json();
      console.log('📥 [Chatbot] AI 응답:', data.reply);

      const aiResponse: Message = {
        id: messages.length + 2,
        text: data.reply,
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
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
  */

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Chat Button - 플로팅 모드에서만 표시 */}
      <AnimatePresence>
        {!isOpen && !isExpanded && (
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
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div
            key={isExpanded ? 'expanded' : 'floating'}
            initial={isExpanded
              ? { opacity: 0, x: 100 }
              : { opacity: 0, y: 20, scale: 0.95 }
            }
            animate={isExpanded
              ? { opacity: 1, x: 0 }
              : { opacity: 1, y: 0, scale: 1 }
            }
            exit={isExpanded
              ? { opacity: 0, x: 100 }
              : { opacity: 0, y: 20, scale: 0.95 }
            }
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className={
              isExpanded
                ? "fixed inset-0 h-screen w-screen z-50"
                : "fixed bottom-8 right-8 w-96 z-50"
            }
          >
            <Card className={`shadow-2xl overflow-hidden ${isExpanded ? 'h-full flex flex-col rounded-none' : ''}`}>
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
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleExpandToggle}
                    className="text-white hover:bg-white/20"
                    title={isExpanded ? '축소' : '확장'}
                  >
                    {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onToggle}
                    className="text-white hover:bg-white/20"
                  >
                    <X className="w-5 h-5" />
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <div className={`overflow-y-auto p-4 space-y-4 bg-gray-50 ${isExpanded ? 'flex-1' : 'h-96'}`}>
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
                      <p className="text-sm whitespace-pre-wrap">{message.text}</p>
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

