import { useState, useRef, useEffect } from "react";

export default function ExitModal({ isOpen, onClose }) {
  const [exitCode, setExitCode] = useState("");
  const [error, setError] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleExitConfirm = () => {
    if (exitCode === "12345") {
      window.electron.confirmExit();
    } else {
      setError(true);
      setExitCode("");

      // 🔥 мгновенно возвращаем фокус
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);

      // убираем ошибку через время
      setTimeout(() => setError(false), 800);
    }
  };

  const handleExitCancel = () => {
    onClose();
    setExitCode("");
    setError(false);
  };

  return (
    <div className="exit-modal-overlay">
      <div className={`exit-modal ${error ? "shake" : ""}`}>
        <span className="exit-modal-icon">🔒</span>
        <h2>Security Verification</h2>
        <p>Please enter 12345 to exit the application.</p>

        <div className="exit-code-container">
          <input
            ref={inputRef}
            type="password"
            className={`exit-code-input ${error ? "input-error" : ""}`}
            placeholder="•••••"
            value={exitCode}
            onChange={(e) => setExitCode(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleExitConfirm()}
          />
        </div>

        {error && <p className="error-text">Incorrect code</p>}

        <div className="exit-modal-actions">
          <button
            className="exit-btn exit-btn-cancel"
            onClick={handleExitCancel}
          >
            Cancel
          </button>
          <button
            className="exit-btn exit-btn-confirm"
            onClick={handleExitConfirm}
            disabled={!exitCode}
          >
            Confirm Exit
          </button>
        </div>
      </div>
    </div>
  );
}
