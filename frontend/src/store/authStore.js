import { create } from "zustand";

const useAuthStore = create((set) => ({
  user:  JSON.parse(localStorage.getItem("user") || "null"),
  token: localStorage.getItem("access_token") || null,

  login: (userData, token) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    set({ user: userData, token });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    set({ user: null, token: null });
  },
}));

export default useAuthStore;