# Advanced Components

Complex interactive components with specialized behaviors.

## Smart Input with AI Action

Input with inline AI sparkle button for suggestions.

### Tailwind/React

```tsx
<div className="relative group">
  <textarea
    value={value || ''}
    onChange={e => onChange(e.target.value)}
    className="w-full p-3 bg-black border border-zinc-800 rounded-sm focus:border-white outline-none transition text-sm text-zinc-200 placeholder-zinc-700 min-h-[80px] resize-y pr-10"
    placeholder="Enter text..."
  />
  <button 
    onClick={handleAiSuggest}
    disabled={loading}
    className="absolute bottom-3 right-3 text-zinc-600 hover:text-white disabled:animate-spin transition-colors"
    title="AI Autocomplete"
  >
    {loading ? <Loader2 size={16} /> : <Sparkles size={16} />}
  </button>
</div>
```

### Vanilla CSS

```html
<div class="smart-input">
  <textarea class="form-textarea" placeholder="Enter text..."></textarea>
  <button class="smart-input-action" title="AI Suggest">
    <svg width="16" height="16"><!-- Sparkles icon --></svg>
  </button>
</div>
```

```css
.smart-input {
  position: relative;
}

.smart-input .form-textarea {
  padding-right: 40px;
}

.smart-input-action {
  position: absolute;
  bottom: 12px;
  right: 12px;
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--zinc-600);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.smart-input-action:hover {
  color: var(--zinc-white);
}

.smart-input-action.loading svg {
  animation: spin 1s linear infinite;
}
```

---

## Combobox / Autocomplete

Input with dropdown list and optional AI suggestions.

### Tailwind/React

```tsx
<div className="relative" ref={containerRef}>
  <div className="relative">
    <input
      type="text"
      value={query}
      onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
      onFocus={() => setIsOpen(true)}
      className="w-full p-3 bg-black border border-zinc-800 rounded-sm focus:border-white outline-none transition text-sm text-zinc-200 placeholder-zinc-700 pr-16"
      placeholder="Select or type..."
    />
    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
      <button 
        onClick={handleAiSuggest}
        disabled={loading}
        className="text-zinc-600 hover:text-white disabled:animate-spin transition-colors"
      >
        {loading ? <Loader2 size={14} /> : <Sparkles size={14} />}
      </button>
      <ChevronDown size={14} className={`text-zinc-600 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
    </div>
  </div>

  {isOpen && (
    <div className="absolute z-50 w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-sm shadow-2xl max-h-60 overflow-y-auto">
      {filteredOptions.map((opt, idx) => (
        <button
          key={idx}
          onClick={() => handleSelect(opt)}
          className="w-full text-left px-4 py-3 hover:bg-zinc-900 text-sm border-b border-zinc-900 last:border-0 flex flex-col"
        >
          <span className="text-zinc-200 font-medium">{opt.label}</span>
          {opt.description && <span className="text-zinc-500 text-xs">{opt.description}</span>}
        </button>
      ))}
      {filteredOptions.length === 0 && (
        <div className="px-4 py-3 text-zinc-600 text-xs italic">No options found.</div>
      )}
    </div>
  )}
</div>
```

---

## Accordion / Collapsible Section

### Tailwind/React

```tsx
const [expandedId, setExpandedId] = useState<string | null>(null);

<div className={`rounded-sm border transition-all group ${
  isExpanded ? 'bg-zinc-900 border-zinc-700' : 'bg-black border-zinc-800 hover:border-zinc-600'
}`}>
  {/* Header */}
  <div 
    className="flex items-center justify-between p-3 cursor-pointer"
    onClick={() => setExpandedId(isExpanded ? null : item.id)}
  >
    <div className="flex items-center gap-2 min-w-0">
      {isExpanded ? <ChevronDown size={12} className="text-zinc-500" /> : <ChevronRight size={12} className="text-zinc-500" />}
      <div className="flex flex-col min-w-0">
        <span className="text-xs font-bold text-zinc-200 truncate">{item.label}</span>
        <span className="text-[10px] text-zinc-500 font-mono">{item.type}</span>
      </div>
    </div>
    {!isExpanded && (
      <button 
        onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
        className="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 p-1"
      >
        <Trash2 size={12} />
      </button>
    )}
  </div>

  {/* Expanded Content */}
  {isExpanded && (
    <div className="px-3 pb-3 pt-0 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
      <div className="h-[1px] bg-zinc-800 w-full"></div>
      {/* Content here */}
    </div>
  )}
</div>
```

### Vanilla CSS

```html
<div class="accordion" data-expanded="false">
  <div class="accordion-header">
    <div class="accordion-title">
      <svg class="accordion-chevron" width="12" height="12">...</svg>
      <span>Section Title</span>
    </div>
    <button class="accordion-delete">×</button>
  </div>
  <div class="accordion-content">
    <div class="accordion-divider"></div>
    <!-- Content -->
  </div>
</div>
```

```css
.accordion {
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  background: var(--zinc-black);
  transition: all var(--transition-fast);
}

.accordion:hover {
  border-color: var(--zinc-600);
}

.accordion[data-expanded="true"] {
  background: var(--zinc-900);
  border-color: var(--zinc-700);
}

.accordion-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  cursor: pointer;
}

.accordion-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--zinc-200);
}

.accordion-chevron {
  color: var(--zinc-500);
  transition: transform var(--transition-fast);
}

.accordion[data-expanded="true"] .accordion-chevron {
  transform: rotate(90deg);
}

.accordion-content {
  display: none;
  padding: 0 12px 12px;
}

.accordion[data-expanded="true"] .accordion-content {
  display: block;
  animation: fadeSlideIn 200ms ease;
}

.accordion-divider {
  height: 1px;
  background: var(--zinc-800);
  margin-bottom: 12px;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

```javascript
document.querySelectorAll('.accordion').forEach(accordion => {
  const header = accordion.querySelector('.accordion-header');
  header.addEventListener('click', () => {
    const expanded = accordion.dataset.expanded === 'true';
    accordion.dataset.expanded = (!expanded).toString();
  });
});
```

---

## File Upload Drop Zone

### Tailwind/React

```tsx
<div className="relative border border-dashed border-zinc-700 rounded-sm h-32 flex flex-col items-center justify-center hover:bg-zinc-900/50 transition-colors group overflow-hidden">
  <input type="file" accept="image/*" onChange={handleUpload} className="absolute inset-0 opacity-0 cursor-pointer z-10" />
  {selectedFile ? (
    <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
      <img src={previewUrl} alt="Preview" className="max-w-full max-h-full object-contain" />
      <div className="absolute top-1 right-1 bg-green-500/90 rounded-full p-0.5">
        <Check size={12} className="text-white" />
      </div>
    </div>
  ) : (
    <div className="text-center text-zinc-500 group-hover:text-zinc-400">
      <Upload size={24} className="mx-auto mb-2" />
      <span className="text-xs">Drop image or click to upload</span>
    </div>
  )}
</div>
```

---

## Zoom Control Bar

### Tailwind/React

```tsx
<div className="flex items-center gap-1 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700 rounded-sm p-1">
  <button 
    onClick={handleZoomOut}
    className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors"
    title="Zoom Out"
  >
    <ZoomOut size={16} />
  </button>
  <span className="px-2 text-xs font-mono text-zinc-300 min-w-[50px] text-center">
    {Math.round(zoom * 100)}%
  </span>
  <button 
    onClick={handleZoomIn}
    className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors"
    title="Zoom In"
  >
    <ZoomIn size={16} />
  </button>
  <div className="w-px h-4 bg-zinc-700 mx-1"></div>
  <button 
    onClick={handleReset}
    className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors"
    title="Reset View"
  >
    <RotateCcw size={16} />
  </button>
</div>
```

---

## Parameter Grid

Display generation parameters in a compact grid.

### Tailwind/React

```tsx
<div className="grid grid-cols-2 gap-3">
  <div className="bg-zinc-900/30 border border-zinc-800 p-2 rounded-sm">
    <span className="block text-[10px] text-zinc-500 uppercase mb-1">Seed</span>
    <span className="block text-xs font-mono text-white">{seed}</span>
  </div>
  <div className="bg-zinc-900/30 border border-zinc-800 p-2 rounded-sm">
    <span className="block text-[10px] text-zinc-500 uppercase mb-1">Size</span>
    <span className="block text-xs font-mono text-white">{size}</span>
  </div>
</div>
```

---

## Code/Prompt Block

### Tailwind/React

```tsx
<div className="bg-black border border-zinc-800 rounded-sm p-4 text-sm text-zinc-300 font-mono leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
  {content}
</div>
```
