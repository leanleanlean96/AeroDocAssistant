import React, { useCallback, useRef, useState } from 'react';
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

function App() {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

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
      }
    },
    []
  );

  const handleInput = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, window.innerHeight * 0.5)}px`;
  }, []);

  return (
    <div className="app">
      <div className="hero">
        <span className="plane-icon" aria-hidden="true">
          ✈︎
        </span>
        <div className="hero-text">
          <p className="title">Отправьте AeroDoc Assistant</p>
          <p className="subtitle">технические файлы для анализа</p>
        </div>
      </div>

      <div className="input-wrapper">
        <div className="input-bar">
          <button className="icon-button" type="button" aria-label="Прикрепить файл">
            <PaperclipIcon />
          </button>
          <textarea
            className="text-input"
            placeholder="Задайте ваш вопрос и прикрепите файлы для анализа"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            rows={1}
            ref={textareaRef}
          />
          <button className="icon-button send" type="button" aria-label="Отправить">
            <span className="send-glyph" aria-hidden="true">
              ✈︎
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
