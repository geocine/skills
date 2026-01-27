# Buttons

All button variants for the Zinc Design System.

## Primary Button (White)

The main call-to-action. Use sparingly - one per section.

### Tailwind/React

```tsx
<button className="flex items-center gap-2 bg-white hover:bg-zinc-200 text-black px-4 py-2 rounded-sm text-xs font-bold uppercase tracking-wide transition-colors active:scale-[0.99]">
  <Sparkles size={16} />
  Generate
</button>
```

### Vanilla CSS

```html
<button class="btn btn-primary">Generate</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:active {
  transform: scale(0.99);
}

.btn-primary {
  background: var(--zinc-white);
  color: var(--zinc-black);
}
.btn-primary:hover {
  background: var(--zinc-200);
}
```

---

## Secondary Button (Bordered)

For secondary actions, cancel buttons, alternative options.

### Tailwind/React

```tsx
<button className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 px-3 py-2 rounded-sm text-xs font-bold uppercase tracking-wide transition-all">
  <LayoutTemplate size={16} />
  New Template
</button>
```

### Vanilla CSS

```html
<button class="btn btn-secondary">Cancel</button>
```

```css
.btn-secondary {
  background: var(--zinc-900);
  color: var(--zinc-400);
  border: 1px solid var(--zinc-800);
}
.btn-secondary:hover {
  color: var(--zinc-white);
  border-color: var(--zinc-700);
}
```

---

## Danger Button

For destructive actions. Always requires confirmation.

### Tailwind/React

```tsx
<button className="flex items-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-bold uppercase tracking-wide rounded-sm transition-colors">
  <Trash2 size={14} />
  Delete
</button>
```

### Vanilla CSS

```html
<button class="btn btn-danger">Delete</button>
```

```css
.btn-danger {
  background: var(--color-danger-bg);
  color: var(--zinc-white);
}
.btn-danger:hover {
  background: var(--color-danger);
}
```

---

## Icon Button

For toolbar actions, close buttons, compact UI.

### Tailwind/React

```tsx
<button className="p-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-sm border border-zinc-800 transition-colors">
  <Settings size={16} />
</button>

// Danger variant (for delete actions on images/overlays)
<button className="p-2 bg-black/50 backdrop-blur-md hover:bg-red-900/30 text-zinc-300 hover:text-red-500 rounded-sm border border-white/10 transition-colors">
  <Trash2 size={14} />
</button>
```

### Vanilla CSS

```html
<button class="btn-icon">
  <svg width="16" height="16">...</svg>
</button>
```

```css
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: var(--zinc-900);
  color: var(--zinc-400);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-icon:hover {
  background: var(--zinc-800);
  color: var(--zinc-white);
}
```

---

## Ghost Button

For tertiary actions, inline links.

### Tailwind/React

```tsx
<button className="text-zinc-400 hover:text-white text-xs font-bold uppercase tracking-wide flex items-center gap-2 py-2 px-4 hover:bg-zinc-900 rounded-sm transition-colors border border-transparent hover:border-zinc-800">
  <Plus size={14} /> Add Item
</button>
```

### Vanilla CSS

```html
<button class="btn btn-ghost">+ Add Item</button>
```

```css
.btn-ghost {
  background: transparent;
  color: var(--zinc-400);
  border: 1px solid transparent;
}
.btn-ghost:hover {
  color: var(--zinc-white);
  background: var(--zinc-900);
  border-color: var(--zinc-800);
}
```

---

## Full-Width Action Button

For form submissions, modal confirmations.

### Tailwind/React

```tsx
<button 
  disabled={isLoading}
  className="w-full h-12 bg-white text-black rounded-sm font-bold tracking-wide flex items-center justify-center gap-2 hover:bg-zinc-200 disabled:opacity-50 transition-all active:scale-[0.99]"
>
  {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
  GENERATE
</button>
```

---

## Type Button Grid

Grid of selectable type buttons (for field type selection, mode toggles).

### Tailwind/React

```tsx
<div className="grid grid-cols-4 gap-1">
  {(['text', 'textarea', 'select', 'boolean'] as const).map(t => (
    <button
      key={t}
      onClick={() => setType(t)}
      className={`text-[10px] py-1.5 rounded-sm border uppercase font-bold flex justify-center ${
        type === t 
          ? 'bg-zinc-800 text-white border-zinc-600' 
          : 'bg-black text-zinc-600 border-zinc-800 hover:border-zinc-700'
      }`}
    >
      {t === 'select' ? 'List' : t}
    </button>
  ))}
</div>
```
