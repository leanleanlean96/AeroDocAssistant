import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const PaperclipIcon: React.FC = () => (
  <svg
    className="icon"
    viewBox="0 0 24 24"
    aria-hidden="true"
    focusable="false"
  >
    <path
      d="M7.5 13.75 14.8 6.5a3.02 3.02 0 0 1 4.26 0c1.18 1.18 1.18 3.08 0 4.26l-8.09 8.1a5 5 0 0 1-7.08-7.07l8.6-8.61"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  attachments?: { id: string; name: string; size: number }[];
};

function App() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
   const [files, setFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const inputBarRef = useRef<HTMLDivElement | null>(null);
  const chatAreaRef = useRef<HTMLDivElement | null>(null);
  const [inputBarHeight, setInputBarHeight] = useState(140);
  const docsFileInputRef = useRef<HTMLInputElement | null>(null);

  const demoReply = useMemo(
    () =>
      'Это демонстрационный ответ ассистента на сто слов. Он создан, чтобы заполнить область чата и показать, как будет выглядеть длинный текст в интерфейсе. Здесь можно упомянуть загрузку документов, анализ файлов, поиск совпадений, построение графа знаний, генерацию сводок, проверку соответствий и любые другие шаги, которые мог бы выполнять AeroDoc Assistant. Также в примере текст специально удлиняется за счет дополнительных фраз, описывающих процесс обработки: чтение, токенизация, векторизация, сравнение, агрегация, вывод результатов. В обычной работе это место займут реальные ответы. Пока что это просто макет для визуального тестирования поведения интерфейса при выводе длинного сообщения.',
    []
  );

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, window.innerHeight * 0.5)}px`;
  }, []);

  const handleSend = useCallback(() => {
    const hasFiles = files.length > 0;
    const userText = message.trim();
    if (!userText && !hasFiles) return;

    const attachments = hasFiles
      ? files.map((file, index) => ({
          id: `file-${Date.now()}-${index}`,
          name: file.name,
          size: file.size,
        }))
      : undefined;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userText,
      attachments,
    };

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: demoReply,
    };

    // Очищаем поле ввода и файлы сразу, но после добавления сообщений
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setFiles([]);

    // Добавляем сообщения сразу
    setMessages((prev) => [...prev, userMessage, assistantMessage]);

    // Принудительно обновляем высоту после очистки в следующем кадре
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        resizeTextarea();
      }
    });
  }, [demoReply, message, files]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && (event.ctrlKey || event.shiftKey)) {
        event.preventDefault();
        const target = event.currentTarget;
        const { selectionStart, selectionEnd, value } = target;
        const nextValue =
          value.slice(0, selectionStart) + '\n' + value.slice(selectionEnd);
        setMessage(nextValue);
        // Move caret to just after inserted newline for natural typing flow.
        requestAnimationFrame(() => {
          target.selectionStart = target.selectionEnd = selectionStart + 1;
        });
        return;
      }

      if (event.key === 'Enter') {
        event.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleAttachClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFilesSelected = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const list = event.target.files;
    if (!list) return;

    const pdfs = Array.from(list).filter(
      (file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    );

    if (pdfs.length === 0) return;

    setFiles((prev) => {
      const existingKeys = new Set(prev.map((f) => `${f.name}-${f.size}`));
      const merged = [...prev];
      pdfs.forEach((file) => {
        const key = `${file.name}-${file.size}`;
        if (!existingKeys.has(key)) {
          merged.push(file);
          existingKeys.add(key);
        }
      });
      return merged;
    });
  }, []);

  const handleRemoveFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleDocsUploadClick = useCallback(() => {
    docsFileInputRef.current?.click();
  }, []);

  const handleDocsFilesSelected = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    // Пока только загружаем файлы для будущей обработки; можно добавить логику позже.
    const list = event.target.files;
    if (!list) return;
    console.log('Документация загружена, файлов:', list.length);
  }, []);

  useEffect(() => {
    resizeTextarea();
  }, [message, resizeTextarea]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, inputBarHeight]);

  useEffect(() => {
    const el = inputBarRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const next = entry.contentRect.height;
        setInputBarHeight(Math.ceil(next + 24)); // 24px зазор над панелью
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);


  return (
    <div className="app">
      <div className="content">
        <div className="hero">
          <span className="plane-icon" aria-hidden="true">
            ✈︎
          </span>
          <div className="hero-text">
            <p className="title">Отправьте AeroDoc Assistant</p>
            <p className="subtitle">технические файлы для анализа</p>
          </div>
        </div>

        <div className="chat-area" ref={chatAreaRef} style={{ paddingBottom: inputBarHeight }}>
            {messages.length === 0 ? (
              <div className="chat-empty">Пока нет сообщений. Отправьте текст, чтобы увидеть чат.</div>
            ) : (
              <>
                {messages.map((msg) => {
                  const hasAttachments = msg.role === 'user' && msg.attachments && msg.attachments.length > 0;

                  return (
                    <div key={msg.id} className={`bubble ${msg.role}`}>
                      {hasAttachments && (
                        <div className="attachments attachments-inline">
                          {msg.attachments!.map((file) => (
                            <div className="attachment-chip" key={file.id}>
                              <span className="attachment-name">{file.name}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {msg.content && <p className="bubble-text">{msg.content}</p>}
                    </div>
                  );
                })}
                <div style={{ height: inputBarHeight }} />
                <div ref={chatEndRef} />
              </>
            )}
        </div>
      </div>

      <div className="docs-upload">
        <input
          ref={docsFileInputRef}
          type="file"
          accept="application/pdf"
          multiple
          hidden
          onChange={handleDocsFilesSelected}
        />
        <button
          className="docs-upload-button"
          type="button"
          onClick={handleDocsUploadClick}
          aria-label="Загрузка документации"
        >
          <span className="docs-upload-icon">PDF</span>
          <div className="docs-upload-tooltip">Загрузка документации</div>
        </button>
      </div>

      <div className="input-wrapper">
        <div className="input-bar" ref={inputBarRef}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            multiple
            hidden
            onChange={handleFilesSelected}
          />

          <div className="input-row">
            <div className="control-group">
              <button
                className="icon-button"
                type="button"
                aria-label="Прикрепить файл"
                onClick={handleAttachClick}
              >
                <PaperclipIcon />
              </button>
              <span className="control-label">Добавить файлы</span>
            </div>

            <div className="text-area-wrapper">
              {files.length > 0 && (
                <div className="attachments">
                  {files.map((file, index) => (
                    <div className="attachment-chip" key={`${file.name}-${index}`}>
                      <span className="attachment-name">{file.name}</span>
                      <button
                        className="attachment-remove"
                        type="button"
                        aria-label="Удалить файл"
                        onClick={() => handleRemoveFile(index)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <textarea
                className="text-input"
                placeholder="Задайте ваш вопрос и прикрепите файлы для анализа"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                ref={textareaRef}
              />
            </div>

            <div className="control-group">
              <button 
                className="icon-button send" 
                type="button" 
                aria-label="Отправить" 
                onClick={handleSend}
              >
                <span className="send-glyph" aria-hidden="true">
                  ✈︎
                </span>
              </button>
              <span className="control-label">Отправить</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
