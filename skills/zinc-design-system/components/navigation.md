# Navigation

Headers, tab switchers, and navigation patterns.

## Header

### Tailwind/React

```tsx
<header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950 sticky top-0 z-40">
  <div className="flex items-center gap-4">
    <button onClick={onBack} className="text-zinc-500 hover:text-white transition-colors flex items-center gap-2 text-sm font-medium">
      <ArrowLeft size={16} /> Back
    </button>
    <div className="h-4 w-[1px] bg-zinc-800"></div>
    <h2 className="text-sm font-bold text-white flex items-center gap-2">
      <Sparkles size={16} className="text-zinc-400" />
      Page Title
    </h2>
  </div>
  
  <div className="flex items-center gap-3">
    {/* actions */}
  </div>
</header>
```

### Vanilla CSS

```html
<header class="header">
  <div class="header-left">
    <button class="btn btn-ghost">← Back</button>
    <div class="header-divider"></div>
    <h1 class="header-title">Page Title</h1>
  </div>
  <div class="header-right">
    <!-- actions -->
  </div>
</header>
```

```css
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  background: var(--zinc-950);
  border-bottom: 1px solid var(--zinc-800);
  position: sticky;
  top: 0;
  z-index: 40;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-divider {
  width: 1px;
  height: 16px;
  background: var(--zinc-800);
}

.header-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--zinc-white);
}
```

---

## Pill Tab Switcher

### Tailwind/React

```tsx
<div className="inline-flex bg-zinc-900 border border-zinc-800 rounded-sm p-0.5">
  {tabs.map(tab => (
    <button 
      key={tab.id}
      onClick={() => setActive(tab.id)}
      className={`px-4 py-1.5 text-xs font-bold uppercase tracking-wide transition-all rounded-sm ${
        active === tab.id 
          ? 'bg-white text-black' 
          : 'text-zinc-500 hover:text-white'
      }`}
    >
      {tab.label}
    </button>
  ))}
</div>
```

### Vanilla CSS

```html
<div class="tabs-pill">
  <button class="tab-pill active">Tab One</button>
  <button class="tab-pill">Tab Two</button>
</div>
```

```css
.tabs-pill {
  display: inline-flex;
  padding: 2px;
  background: var(--zinc-900);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
}

.tab-pill {
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--zinc-500);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.tab-pill:hover {
  color: var(--zinc-white);
}
.tab-pill.active {
  background: var(--zinc-white);
  color: var(--zinc-black);
}
```

---

## Underline Tabs

### Tailwind/React

```tsx
<div className="h-10 px-4 border-b border-zinc-800 flex items-center gap-1 bg-zinc-950">
  {tabs.map(tab => (
    <button 
      key={tab.id}
      onClick={() => setActive(tab.id)}
      className={`h-full px-4 text-xs font-bold uppercase tracking-wide flex items-center gap-2 border-b-2 transition-colors ${
        active === tab.id 
          ? 'text-white border-white' 
          : 'text-zinc-500 border-transparent hover:text-zinc-300'
      }`}
    >
      <tab.icon size={14} />
      {tab.label}
    </button>
  ))}
</div>
```

---

## Cover Position Selector

Segmented control for image position.

### Tailwind/React

```tsx
<div className="flex bg-black/70 backdrop-blur-md rounded-sm border border-white/10 overflow-hidden">
  {['top', 'center', 'bottom'].map(pos => (
    <button 
      key={pos}
      onClick={() => setPosition(pos)}
      className={`px-3 py-1.5 text-[10px] font-bold uppercase transition-colors ${
        position === pos ? 'bg-white text-black' : 'text-white/70 hover:text-white'
      }`}
    >
      {pos.charAt(0).toUpperCase() + pos.slice(1)}
    </button>
  ))}
</div>
```

### Vanilla CSS

```html
<div class="position-selector">
  <button class="position-btn active">Top</button>
  <button class="position-btn">Center</button>
  <button class="position-btn">Bottom</button>
</div>
```

```css
.position-selector {
  display: flex;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.position-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.position-btn:hover {
  color: var(--zinc-white);
}

.position-btn.active {
  background: var(--zinc-white);
  color: var(--zinc-black);
}
```
