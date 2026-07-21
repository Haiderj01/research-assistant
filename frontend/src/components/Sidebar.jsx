import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Upload", icon: "↑" },
  { to: "/chat", label: "Chat", icon: "💬" },
  { to: "/compare", label: "Compare", icon: "⇄" },
  { to: "/history", label: "History", icon: "📋" },
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen shrink-0">
      <div className="p-5 border-b border-gray-700">
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
                isActive ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-gray-800"
              }`
            }
          >
            <span>{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
