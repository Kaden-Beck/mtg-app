import { useState } from "react"
import CardSearch from "./components/CardSearch"
import { ConverterPage } from "./components/ConverterPage"
import { ScannerPage } from "./features/scanner/ScannerPage"
import "./App.css"

const TABS = [
  { id: "search", label: "Search", render: () => <CardSearch query="" /> },
  { id: "converter", label: "Converter", render: () => <ConverterPage /> },
  { id: "scanner", label: "Scanner", render: () => <ScannerPage /> },
] as const

type TabId = (typeof TABS)[number]["id"]

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("scanner")
  const active = TABS.find((tab) => tab.id === activeTab) ?? TABS[0]

  return (
    <div className="flex flex-col">
      <nav className="flex gap-2 border-b p-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            aria-current={tab.id === activeTab}
            className="rounded-md px-3 py-1.5 text-sm font-medium aria-[current=true]:bg-muted"
          >
            {tab.label}
          </button>
        ))}
      </nav>
      {active.render()}
    </div>
  )
}

export default App
