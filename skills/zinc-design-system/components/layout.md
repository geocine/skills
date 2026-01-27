# Layout

Page layouts, grid patterns, and structural components.

## Full Page Layout

### Tailwind/React

```tsx
<div className="min-h-screen bg-black text-zinc-200 flex flex-col font-sans selection:bg-white selection:text-black">
  <header className="h-16 border-b border-zinc-800 flex items-center px-6 bg-zinc-950 sticky top-0 z-40">
    {/* header */}
  </header>
  <main className="flex-1 p-6">
    {/* content */}
  </main>
</div>
```

---

## Split Panel (IDE Style)

### Tailwind/React

```tsx
<div className="flex h-screen bg-black overflow-hidden">
  <aside className="w-[350px] border-r border-zinc-800 bg-zinc-900/30 flex flex-col">
    {/* sidebar */}
  </aside>
  <main className="flex-1 flex flex-col">
    {/* main canvas */}
  </main>
</div>
```

---

## Sidebar Layout

### Tailwind/React

```tsx
<div className="w-full lg:w-[450px] flex flex-col lg:h-screen border-r border-zinc-800 bg-zinc-900/30 backdrop-blur-sm z-10">
  {/* Header */}
  <div className="h-16 flex items-center justify-between px-6 border-b border-zinc-800 bg-zinc-950 flex-shrink-0">
    {/* header content */}
  </div>

  {/* Scrollable Content */}
  <div className="flex-1 overflow-y-auto p-6 space-y-6">
    {/* scrollable content */}
  </div>

  {/* Footer Action Bar */}
  <div className="p-4 border-t border-zinc-800 bg-zinc-950 flex flex-col gap-3 flex-shrink-0">
    {/* actions */}
  </div>
</div>
```

---

## Sidebar Groups & Dividers

### Vanilla CSS

```html
<div class="sidebar-group">
  <!-- settings rows -->
</div>
<div class="sidebar-divider"></div>
<div class="sidebar-group">
  <!-- more settings -->
</div>
```

```css
.sidebar-group {
  padding: 20px;
}

.sidebar-divider {
  height: 1px;
  background: var(--zinc-800);
  margin: 0 20px;
}
```

---

## Inline Form Row

Horizontal row with label + controls (common in settings panels).

### Tailwind/React

```tsx
<div className="flex items-center justify-between mb-3">
  <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 min-w-[55px]">Width</label>
  <div className="flex items-center gap-2">
    <input type="number" className="w-20 h-8 px-3 text-center text-xs bg-black border border-zinc-800 rounded-sm text-white" />
    <span className="text-xs font-mono text-zinc-600">px</span>
  </div>
</div>
```

### Vanilla CSS

```html
<div class="sidebar-row">
  <label class="sidebar-label">Width</label>
  <div class="sidebar-controls">
    <input type="number" class="form-input form-input-sm" value="1200">
    <span class="sidebar-unit">px</span>
  </div>
</div>
```

```css
.sidebar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.sidebar-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--zinc-500);
  flex-shrink: 0;
  min-width: 55px;
}

.sidebar-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-unit {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--zinc-600);
}
```

---

## Grid Background

Subtle grid pattern for canvas/workspace areas.

### Tailwind/React

```tsx
<div 
  className="absolute inset-0 opacity-[0.03] pointer-events-none" 
  style={{ 
    backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', 
    backgroundSize: '40px 40px'
  }}
/>
```

### Vanilla CSS

```css
.bg-grid {
  background-image: 
    linear-gradient(#333 1px, transparent 1px),
    linear-gradient(90deg, #333 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.03;
}
```

---

## Divider with Text

### Tailwind/React

```tsx
<div className="relative flex items-center justify-center">
  <div className="absolute inset-0 flex items-center">
    <div className="w-full border-t border-zinc-800"></div>
  </div>
  <span className="relative bg-black px-4 text-[10px] text-zinc-600 uppercase font-bold tracking-widest">OR</span>
</div>
```

### Vanilla CSS

```html
<div class="divider-text">
  <span>OR</span>
</div>
```

```css
.divider-text {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider-text::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: var(--zinc-800);
}

.divider-text span {
  position: relative;
  background: var(--zinc-black);
  padding: 0 16px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--zinc-600);
}
```

---

## Footer Action Bar

Bottom-anchored controls with action buttons.

### Tailwind/React

```tsx
<div className="p-4 border-t border-zinc-800 bg-zinc-950 flex flex-col gap-3 flex-shrink-0">
  {/* Controls row */}
  <div className="flex items-center gap-3 h-10">
    {/* seed, size selectors */}
  </div>
  
  {/* Action buttons */}
  <div className="flex gap-2">
    <button className="px-3 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-sm font-bold text-xs border border-zinc-800 transition-colors h-10">
      <Terminal size={16} />
    </button>
    <button className="flex-1 h-10 bg-white hover:bg-zinc-200 text-black rounded-sm font-bold text-xs tracking-wide flex items-center justify-center gap-2 transition-all">
      <ImageIcon size={16} />
      GENERATE
    </button>
  </div>
</div>
```

### Vanilla CSS

```css
.sidebar-footer {
  margin-top: auto;
  padding: 20px;
  display: flex;
  gap: 10px;
  border-top: 1px solid var(--zinc-800);
  background: var(--zinc-950);
}

.sidebar-footer .btn {
  flex: 1;
}
```
