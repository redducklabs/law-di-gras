// React 19 hoists <link precedence> into <head>, so pages can load Inter without touching index.html.
export function Fonts() {
  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link rel="stylesheet" precedence="default"
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" />
    </>
  )
}
