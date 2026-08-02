import { NavLink } from "react-router-dom";
import { useAppDispatch, useAppState } from "../context/AppContext";

const links = [
  { to: "/", label: "Upload", icon: "↑" },
  { to: "/chat", label: "Chat", icon: "💬" },
  { to: "/compare", label: "Compare", icon: "⇄" },
  { to: "/history", label: "History", icon: "📋" },
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
];

export default function Sidebar() {
  const { theme } = useAppState();
  const dispatch = useAppDispatch();
  const isDark = theme === "dark";

  return (
    <aside className="w-64 bg-sidebar-bg text-sidebar-text-hover flex flex-col h-screen shrink-0">
      <div className="p-5 border-b border-sidebar-border">
        <h1 className="text-lg font-bold tracking-tight">Research Assistant</h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-accent text-sidebar-text-hover"
                  : "text-sidebar-text hover:bg-sidebar-item-hover"
              }`
            }
          >
            <span>{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-sidebar-border">
        <button
          type="button"
          onClick={() => dispatch({ type: "TOGGLE_THEME" })}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-sidebar-text hover:bg-sidebar-item-hover transition-colors"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <span>{isDark ? "☀️" : "🌙"}</span>
          {isDark ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </aside>
  );
}
