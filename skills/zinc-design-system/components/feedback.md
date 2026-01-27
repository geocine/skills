# Feedback & Status

Badges, loading states, progress indicators, and status feedback.

## Status Badges

### Tailwind/React

```tsx
// Modified indicator
<span className="px-1.5 py-0.5 bg-amber-500/10 text-amber-500 rounded-sm text-[9px] font-bold flex items-center gap-1">
  <span className="w-1 h-1 rounded-full bg-amber-500 animate-pulse"></span>
  Modified
</span>

// Mode badge
<span className="px-2 py-0.5 rounded text-[10px] border bg-zinc-800 text-zinc-200 border-zinc-700">
  AI REFINED
</span>

// Count badge
<span className="px-1.5 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-400 min-w-[20px] text-center">
  {count}
</span>
```

---

## Loading States

### Tailwind/React

```tsx
// Spinner
<Loader2 className="animate-spin" size={18} />

// Progress bar (indeterminate)
<div className="w-12 h-1 bg-zinc-800 rounded-full overflow-hidden">
  <div className="h-full bg-white animate-progress"></div>
</div>

// Loading message
<span className="text-xs text-zinc-500 font-mono animate-pulse">Processing...</span>
```

### CSS Animation

```css
@keyframes progress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.animate-progress {
  animation: progress 1.5s ease-in-out infinite;
}
```

### Vanilla CSS

```html
<div class="progress-bar">
  <div class="progress-bar-fill"></div>
</div>
```

```css
.progress-bar {
  width: 48px;
  height: 4px;
  background: var(--zinc-800);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  width: 100%;
  background: var(--zinc-white);
  animation: progress 1.5s ease-in-out infinite;
}
```

---

## Copy Success Feedback

### Tailwind/React

```tsx
<button onClick={handleCopy} className="text-zinc-500 hover:text-white transition-colors">
  {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
</button>
```

---

## Linked Tags (Removable Pills)

Tag cloud with inline add dropdown.

### Tailwind/React

```tsx
<div className="flex flex-wrap gap-2 p-3 bg-black rounded-sm min-h-[50px] border border-zinc-800 border-dashed">
  {linkedItems.map(id => (
    <span key={id} className="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-sm text-xs text-zinc-200 flex items-center gap-2 font-mono group/tag cursor-default">
      {getItemLabel(id)}
      <button 
        onClick={() => handleRemove(id)}
        className="text-zinc-500 hover:text-white"
      >×</button>
    </span>
  ))}
  <select 
    className="bg-transparent text-[10px] text-zinc-500 font-bold uppercase outline-none cursor-pointer min-w-[80px] hover:text-zinc-300 py-1"
    onChange={(e) => {
      if(e.target.value) {
        handleAdd(e.target.value);
        e.target.value = '';
      }
    }}
  >
    <option value="">+ Add Item</option>
    {availableItems.map(item => (
      <option key={item.id} value={item.id}>{item.label}</option>
    ))}
  </select>
</div>
```

### Vanilla CSS

```html
<div class="tag-cloud">
  <span class="tag">
    Tag Label
    <button class="tag-remove">×</button>
  </span>
  <select class="tag-add">
    <option value="">+ Add Tag</option>
  </select>
</div>
```

```css
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: var(--zinc-black);
  border: 1px dashed var(--zinc-800);
  border-radius: var(--radius-sm);
  min-height: 50px;
}

.tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: var(--zinc-800);
  border: 1px solid var(--zinc-700);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--zinc-200);
}

.tag-remove {
  padding: 0;
  background: transparent;
  border: none;
  color: var(--zinc-500);
  font-size: 14px;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.tag-remove:hover {
  color: var(--zinc-white);
}

.tag-add {
  padding: 4px;
  background: transparent;
  border: none;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--zinc-500);
  cursor: pointer;
  outline: none;
}
```
