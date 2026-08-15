import { NavLink } from "react-router-dom";
import { useAppDispatch, useAppState, useAuthActions } from "../context/AppContext";

const links = [
  { to: "/upload", label: "Upload", icon: "↑" },
  { to: "/chat", label: "Chat", icon: "💬" },
  { to: "/compare", label: "Compare", icon: "⇄" },
  { to: "/history", label: "History", icon: "📋" },
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
];

export default function Sidebar() {
  const { theme, user, token } = useAppState();
  const dispatch = useAppDispatch();
  const { logout } = useAuthActions();
  const isDark = theme === "dark";

  return (
    <aside className="w-16 lg:w-64 bg-sidebar-bg text-sidebar-text-hover flex flex-col h-screen shrink-0 transition-[width] duration-200">
      <div className="px-3 lg:px-5 py-5 border-b border-sidebar-border flex items-center justify-center lg:justify-start">
        <h1 className="text-lg font-bold tracking-tight hidden lg:block">Research Assistant</h1>
        <span className="lg:hidden text-lg font-bold" title="Research Assistant">RA</span>
      </div>
      <nav className="flex-1 p-2 lg:p-3 space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset ${
                isActive
                  ? "bg-accent text-sidebar-text-hover"
                  : "text-sidebar-text hover:bg-sidebar-item-hover active:bg-sidebar-item-hover"
              }`
            }
          >
            <span className="w-5 text-center shrink-0">{l.icon}</span>
            <span className="hidden lg:inline">{l.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-2 lg:p-3 border-t border-sidebar-border space-y-1">
        {user && (
          <div
            className="px-3 py-2 text-xs text-sidebar-text truncate text-center hidden lg:block"
            title={user.name || user.email}
          >
            {user.name || user.email}
          </div>
        )}
        <button
          type="button"
          onClick={() => dispatch({ type: "TOGGLE_THEME" })}
          className="w-full flex items-center justify-center lg:justify-start gap-3 px-3 py-2 rounded-lg text-sm text-sidebar-text hover:bg-sidebar-item-hover active:bg-sidebar-item-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <span className="w-5 text-center shrink-0">{isDark ? "☀️" : "🌙"}</span>
          <span className="hidden lg:inline">{isDark ? "Light mode" : "Dark mode"}</span>
        </button>
        {token && (
          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center justify-center lg:justify-start gap-3 px-3 py-2 rounded-lg text-sm text-sidebar-text hover:bg-sidebar-item-hover active:bg-sidebar-item-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
            title="Log out"
          >
            <span className="w-5 text-center shrink-0">⏻</span>
            <span className="hidden lg:inline">Log out</span>
          </button>
        )}
      </div>
    </aside>
  );
}
