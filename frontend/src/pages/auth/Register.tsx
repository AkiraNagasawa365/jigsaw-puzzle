/**
 * Register Page
 * 新規登録画面
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function Register() {
  const { register, confirmRegistration } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // パスワード確認
    if (password !== confirmPassword) {
      setError('パスワードが一致しません');
      return;
    }

    // パスワード要件チェック
    if (password.length < 8) {
      setError('パスワードは8文字以上である必要があります');
      return;
    }
    if (!/[A-Z]/.test(password)) {
      setError('パスワードには大文字を含める必要があります');
      return;
    }
    if (!/[a-z]/.test(password)) {
      setError('パスワードには小文字を含める必要があります');
      return;
    }
    if (!/[0-9]/.test(password)) {
      setError('パスワードには数字を含める必要があります');
      return;
    }

    setLoading(true);

    try {
      await register(email, password);
      setSuccess('確認コードをメールアドレスに送信しました');
      setNeedsConfirmation(true);
    } catch (err: any) {
      setError(err.message || 'アカウント登録に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await confirmRegistration(email, verificationCode);
      setSuccess('アカウント登録が完了しました。ログインしてください。');
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err: any) {
      setError(err.message || '確認コードの検証に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px' }}>
      <h1>新規登録</h1>

      {error && (
        <div style={{
          padding: '10px',
          marginBottom: '20px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c00'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '10px',
          marginBottom: '20px',
          backgroundColor: '#efe',
          border: '1px solid #cfc',
          borderRadius: '4px',
          color: '#060'
        }}>
          {success}
        </div>
      )}

      {!needsConfirmation ? (
        <form onSubmit={handleRegister}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>
              メールアドレス
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>
              パスワード
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
            <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
              8文字以上、大文字・小文字・数字を含む
            </small>
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>
              パスワード（確認）
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: loading ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            {loading ? '登録中...' : '登録'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleConfirm}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>
              確認コード
            </label>
            <input
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              required
              placeholder="メールに送信された6桁のコード"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: loading ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            {loading ? '確認中...' : '確認'}
          </button>
        </form>
      )}

      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <p>
          すでにアカウントをお持ちの方は
          <Link to="/login" style={{ color: '#007bff', marginLeft: '5px' }}>
            ログイン
          </Link>
        </p>
      </div>
    </div>
  );
}
