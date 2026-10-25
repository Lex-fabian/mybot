import { initializeApp, getApps, getApp } from 'firebase/app'
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  type User
} from 'firebase/auth'

export const firebaseConfig = {
  projectId: 'mybot-79861',
  appId: '1:929325369614:web:552848363e69f7a2c1af5f',
  storageBucket: 'mybot-79861.firebasestorage.app',
  apiKey: 'AIzaSyBr_TIXjNmtV_sKBFVT_eWki-slPQ5NC14',
  authDomain: 'mybot-79861.firebaseapp.com',
  messagingSenderId: '929325369614'
}

export const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()
googleProvider.setCustomParameters({ prompt: 'select_account' })

export async function loginWithGoogle(): Promise<User> {
  const result = await signInWithPopup(auth, googleProvider)
  return result.user
}

export async function logoutFirebase(): Promise<void> {
  await signOut(auth)
}

export { onAuthStateChanged, type User }
