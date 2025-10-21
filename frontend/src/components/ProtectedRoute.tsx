/**
 * Protected Route Component
 * ログインが必要なページを保護
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  console.log('🔒 ProtectedRoute: loading =', loading, ', user =', user);

  // ローディング中は空画面
  if (loading) {
    console.log('⏳ ProtectedRoute: Showing loading screen');
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <p>読み込み中...</p>
      </div>
    );
  }

  // 未ログインの場合はログイン画面にリダイレクト
  if (!user) {
    console.log('🚫 ProtectedRoute: No user, redirecting to /login');
    return <Navigate to="/login" replace />;
  }

  // ログイン済みの場合は子要素を表示
  console.log('✅ ProtectedRoute: User authenticated, showing content');
  return <>{children}</>;
}
