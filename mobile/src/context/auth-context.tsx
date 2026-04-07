import React, { createContext, useContext, useEffect, useState } from "react";
import type { User } from "../types/api";
import * as authApi from "../services/auth-api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount check for an existing token
  useEffect(() => {
    (async () => {
      try {
        const token = await authApi.getAccessToken();
        if (token) {
          const profile = await authApi.getProfile();
          setUser(profile.user);
        }
      } catch {
        await authApi.clearTokens();
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const signIn = async (username: string, password: string) => {
    const data = await authApi.login(username, password);
    setUser(data.user);
  };

  const signOut = async () => {
    await authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
