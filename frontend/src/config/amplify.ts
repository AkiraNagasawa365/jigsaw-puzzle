/**
 * AWS Amplify Configuration
 * Cognito認証の設定
 */

import { Amplify } from 'aws-amplify';

// 環境変数の確認
const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;

console.log('🔧 Amplify Configuration:');
console.log('User Pool ID:', userPoolId);
console.log('Client ID:', clientId);

if (!userPoolId || !clientId) {
  console.error('❌ Cognito環境変数が設定されていません');
  console.error('VITE_COGNITO_USER_POOL_ID:', userPoolId);
  console.error('VITE_COGNITO_CLIENT_ID:', clientId);
}

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: userPoolId,
      userPoolClientId: clientId,
      loginWith: {
        email: true,
      },
      signUpVerificationMethod: 'code' as const,
      userAttributes: {
        email: {
          required: true,
        },
      },
      passwordFormat: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: false,
      },
    },
  },
};

try {
  Amplify.configure(amplifyConfig);
  console.log('✅ Amplify configured successfully');
} catch (error) {
  console.error('❌ Amplify configuration error:', error);
}

export default amplifyConfig;
