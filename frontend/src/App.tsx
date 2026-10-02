// Integration owns routing. Streams own the page components.
import { Route, Routes } from 'react-router-dom'

function Placeholder({ name }: { name: string }) {
  return <div className="p-8 text-slate-500">{name} not built yet</div>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Placeholder name="Firm Case Brief (S3)" />} />
      <Route path="/p/:token" element={<Placeholder name="Provider view (S4)" />} />
    </Routes>
  )
}
