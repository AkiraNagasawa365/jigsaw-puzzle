/**
 * Authentication Context
 * ユーザーの認証状態を管理
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import {
  signIn,
  signUp,
  signOut,
  confirmSignUp,
  getCurrentUser,
  fetchAuthSession
} from 'aws-amplify/auth';

interface User {
  userId: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  confirmRegistration: (email: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | undefined>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 初回マウント時に認証状態を確認
  useEffect(() => {
    console.log('🔄 AuthContext: Checking auth state...');
    checkAuthState();
  }, []);

  const checkAuthState = async () => {
    try {
      console.log('🔍 AuthContext: Getting current user...');
      const currentUser = await getCurrentUser();
      console.log('✅ AuthContext: User found:', currentUser);
      setUser({
        userId: currentUser.userId,
        email: currentUser.signInDetails?.loginId || '',
      });
    } catch {
      // 未認証の場合（errorは使用しないため省略）
      console.log('ℹ️ AuthContext: No user authenticated (expected for first visit)');
      setUser(null);
    } finally {
      console.log('✅ AuthContext: Auth check complete, loading = false');
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      await signIn({
        username: email,
        password,
      });
      await checkAuthState();
    } catch (error: any) {
      console.error('Login error:', error);
      throw new Error(error.message || 'ログインに失敗しました');
    }
  };

  const register = async (email: string, password: string) => {
    try {
      await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
          },
        },
      });
    } catch (error: any) {
      console.error('Register error:', error);
      throw new Error(error.message || 'アカウント登録に失敗しました');
    }
  };

  const confirmRegistration = async (email: string, code: string) => {
    try {
      await confirmSignUp({
        username: email,
        confirmationCode: code,
      });
    } catch (error: any) {
      console.error('Confirm registration error:', error);
      throw new Error(error.message || '確認コードの検証に失敗しました');
    }
  };

  const logout = async () => {
    try {
      await signOut();
      setUser(null);
    } catch (error: any) {
      console.error('Logout error:', error);
      throw new Error(error.message || 'ログアウトに失敗しました');
    }
  };

  const getIdToken = async (): Promise<string | undefined> => {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString();
    } catch (error) {
      console.error('Get ID token error:', error);
      return undefined;
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    confirmRegistration,
    logout,
    getIdToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// カスタムフックのエクスポートはFast Refreshの対象外
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
