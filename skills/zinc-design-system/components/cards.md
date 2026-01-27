# Cards & Containers

Card components, panels, and container patterns.

## Basic Card

### Tailwind/React

```tsx
<div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4 hover:border-zinc-600 transition-colors">
  {/* content */}
</div>
```

### Vanilla CSS

```html
<div class="card">
  <!-- content -->
</div>
```

```css
.card {
  background: var(--zinc-900);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  padding: 16px;
  transition: border-color var(--transition-fast);
}
.card:hover {
  border-color: var(--zinc-600);
}
```

---

## Glass Card

For modals, popovers, elevated content.

### Tailwind/React

```tsx
<div className="bg-zinc-900/50 border border-zinc-800 rounded-sm p-6 shadow-2xl backdrop-blur-sm">
  {/* content */}
</div>
```

### Vanilla CSS

```css
.card-glass {
  background: rgba(24, 24, 27, 0.5);
  backdrop-filter: blur(8px);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}
```

---

## Template/Gallery Card

Card with preview image, gradient overlay, category, and hover actions.

### Tailwind/React

```tsx
<div 
  onClick={() => handleClick(item)}
  className="group relative aspect-[3/4] bg-zinc-900 border border-zinc-800 rounded-sm overflow-hidden cursor-pointer hover:border-zinc-600 transition-all"
>
  {/* Preview Image */}
  {item.previewImage ? (
    <img 
      src={item.previewImage} 
      alt="Preview" 
      className="w-full h-full object-cover opacity-60 group-hover:opacity-40 group-hover:scale-105 transition-all duration-500"
    />
  ) : (
    <div className="w-full h-full bg-zinc-950 flex items-center justify-center opacity-50">
      <LayoutTemplate size={48} className="text-zinc-800" />
    </div>
  )}
  
  {/* Gradient Overlay */}
  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent opacity-90" />
  
  {/* Hover CTA */}
  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 z-20 pointer-events-none">
    <span className="bg-white text-black px-4 py-2 text-[10px] font-bold uppercase tracking-widest rounded-sm shadow-xl transform translate-y-2 group-hover:translate-y-0 transition-transform">
      Use Template
    </span>
  </div>

  {/* Hover Actions */}
  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 z-30">
    <button 
      onClick={(e) => { e.stopPropagation(); handleEdit(item); }} 
      className="p-2 bg-black/50 backdrop-blur-md hover:bg-zinc-800 text-zinc-300 hover:text-white rounded-sm border border-white/10 transition-colors"
    >
      <Pencil size={14} />
    </button>
    <button 
      onClick={(e) => { e.stopPropagation(); handleDelete(item); }}
      className="p-2 bg-black/50 backdrop-blur-md hover:bg-red-900/30 text-zinc-300 hover:text-red-500 rounded-sm border border-white/10 transition-colors"
    >
      <Trash2 size={14} />
    </button>
  </div>
  
  {/* Content */}
  <div className="absolute bottom-0 left-0 right-0 p-4 flex flex-col z-20">
    <span className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1 font-bold">{item.category}</span>
    <h3 className="text-sm font-bold text-white mb-2 group-hover:text-zinc-200 transition-colors line-clamp-1">{item.name}</h3>
    <div className="flex items-center justify-between border-t border-white/10 pt-2 text-[10px] font-mono text-zinc-500">
      <span>{Object.keys(item.fields).length} VARS</span>
      <span>V{item.version}</span>
    </div>
  </div>
</div>
```

### Vanilla CSS

```html
<div class="gallery-card">
  <div class="gallery-card-image">
    <img src="preview.jpg" alt="Preview">
  </div>
  <div class="gallery-card-overlay"></div>
  <div class="gallery-card-actions">
    <button class="btn-icon">Edit</button>
    <button class="btn-icon btn-icon-danger">Delete</button>
  </div>
  <div class="gallery-card-content">
    <span class="gallery-card-category">Category</span>
    <h3 class="gallery-card-title">Card Title</h3>
    <div class="gallery-card-meta">
      <span>3 VARS</span>
      <span>V1</span>
    </div>
  </div>
</div>
```

```css
.gallery-card {
  position: relative;
  aspect-ratio: 3/4;
  background: var(--zinc-900);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.gallery-card:hover {
  border-color: var(--zinc-600);
}

.gallery-card-image {
  position: absolute;
  inset: 0;
}
.gallery-card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.6;
  transition: all 500ms ease;
}
.gallery-card:hover .gallery-card-image img {
  opacity: 0.4;
  transform: scale(1.05);
}

.gallery-card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, var(--zinc-950), transparent);
  opacity: 0.9;
}

.gallery-card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.gallery-card:hover .gallery-card-actions {
  opacity: 1;
}

.gallery-card-content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
}

.gallery-card-category {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--zinc-500);
  margin-bottom: 4px;
}

.gallery-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--zinc-white);
  margin-bottom: 8px;
}

.gallery-card-meta {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--zinc-500);
}
```

---

## Empty State

### Tailwind/React

```tsx
<div className="col-span-full py-20 text-center border border-dashed border-zinc-800 rounded-sm">
  <LayoutTemplate size={48} className="mx-auto text-zinc-700 mb-4" />
  <p className="text-zinc-500 text-sm">No items found.</p>
  <button className="mt-4 text-white underline text-sm hover:text-zinc-300">
    Create your first item
  </button>
</div>
```

### Vanilla CSS

```html
<div class="empty-state">
  <svg class="empty-state-icon" width="48" height="48">...</svg>
  <p class="empty-state-text">No items found.</p>
  <button class="btn btn-ghost">Create your first item</button>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  border: 1px dashed var(--zinc-800);
  border-radius: var(--radius-sm);
}

.empty-state-icon {
  color: var(--zinc-700);
  margin-bottom: 16px;
}

.empty-state-text {
  color: var(--zinc-500);
  margin-bottom: 16px;
}
```

---

## Drop Zone / Welcome State

Interactive drop zone for file uploads or initial states.

### Tailwind/React

```tsx
<div className="flex items-center justify-center h-full p-8 group">
  <div className="p-16 border border-dashed border-zinc-800 rounded-sm text-center transition-all group-hover:border-zinc-600 group-hover:bg-zinc-950">
    <span className="text-7xl block mb-8 opacity-50 transition-all group-hover:scale-110 group-hover:opacity-100">📁</span>
    <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-br from-white to-zinc-400 bg-clip-text text-transparent">
      Drop Files Here
    </h1>
    <p className="text-lg text-zinc-400 mt-2 mb-8">or click to browse</p>
    <button className="btn btn-primary">Browse Files</button>
  </div>
</div>
```

---

## Image Tile with Actions

Preview tile with overlay action buttons.

### Tailwind/React

```tsx
<div className="relative cursor-move select-none">
  <img src="preview.jpg" className="w-full h-auto pointer-events-none" />
  <button className="absolute top-1 right-1 px-2 bg-black/60 backdrop-blur text-zinc-200 rounded-sm hover:bg-red-600/30 hover:text-red-500 transition-colors">
    ×
  </button>
</div>
<p className="p-3 bg-zinc-900 text-xs font-mono text-zinc-400 truncate">filename.jpg</p>
```

---

## Collapsible/Expandable Card

### Tailwind/React

```tsx
<div className={`rounded-sm border transition-all group ${
  isExpanded ? 'bg-zinc-900 border-zinc-700' : 'bg-black border-zinc-800 hover:border-zinc-600'
}`}>
  {/* Header */}
  <div className="flex items-center justify-between p-3 cursor-pointer" onClick={toggle}>
    <div className="flex items-center gap-2">
      {isExpanded ? <ChevronDown size={12} className="text-zinc-500" /> : <ChevronRight size={12} className="text-zinc-500" />}
      <span className="text-xs font-bold text-zinc-200">{title}</span>
    </div>
    {!isExpanded && (
      <button className="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 p-1">
        <Trash2 size={12} />
      </button>
    )}
  </div>
  
  {/* Expandable Content */}
  {isExpanded && (
    <div className="px-3 pb-3 pt-0 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
      <div className="h-[1px] bg-zinc-800 w-full"></div>
      {/* content */}
    </div>
  )}
</div>
```

---

## Anchor Point Grid

3x3 grid for selecting anchor/focal points.

### Vanilla CSS

```html
<div class="anchor-points">
  <div class="anchor-point" data-position="top-left"></div>
  <div class="anchor-point" data-position="top-center"></div>
  <div class="anchor-point" data-position="top-right"></div>
  <div class="anchor-point" data-position="middle-left"></div>
  <div class="anchor-point active" data-position="middle-center"></div>
  <div class="anchor-point" data-position="middle-right"></div>
  <div class="anchor-point" data-position="bottom-left"></div>
  <div class="anchor-point" data-position="bottom-center"></div>
  <div class="anchor-point" data-position="bottom-right"></div>
</div>
```

```css
.anchor-points {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  width: 80px;
  height: 80px;
  position: relative;
  border: 1px dashed var(--zinc-700);
}

.anchor-point {
  width: 16px;
  height: 16px;
  border: 2px solid var(--zinc-600);
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  position: absolute;
  transition: all var(--transition-fast);
}

.anchor-point:hover {
  border-color: var(--zinc-white);
}

.anchor-point.active {
  background: var(--zinc-white);
  border-color: var(--zinc-white);
}

/* Position each point */
.anchor-point[data-position="top-left"] { top: -8px; left: -8px; }
.anchor-point[data-position="top-center"] { top: -8px; left: 50%; transform: translateX(-50%); }
.anchor-point[data-position="top-right"] { top: -8px; right: -8px; }
.anchor-point[data-position="middle-left"] { top: 50%; left: -8px; transform: translateY(-50%); }
.anchor-point[data-position="middle-center"] { top: 50%; left: 50%; transform: translate(-50%, -50%); }
.anchor-point[data-position="middle-right"] { top: 50%; right: -8px; transform: translateY(-50%); }
.anchor-point[data-position="bottom-left"] { bottom: -8px; left: -8px; }
.anchor-point[data-position="bottom-center"] { bottom: -8px; left: 50%; transform: translateX(-50%); }
.anchor-point[data-position="bottom-right"] { bottom: -8px; right: -8px; }
```
