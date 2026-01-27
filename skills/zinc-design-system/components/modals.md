# Modals & Overlays

Modal dialogs, lightboxes, side drawers, and overlay patterns.

## Confirmation Modal

### Tailwind/React

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center p-4">
  {/* Backdrop */}
  <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
  
  {/* Modal */}
  <div className="relative bg-zinc-950 border border-zinc-800 rounded-sm w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
    {/* Header */}
    <div className="flex items-center justify-between p-4 border-b border-zinc-800">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-red-500/10 rounded-sm flex items-center justify-center">
          <AlertTriangle size={20} className="text-red-500" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">Confirm Action</h3>
          <p className="text-xs text-zinc-500">This cannot be undone</p>
        </div>
      </div>
      <button onClick={onClose} className="text-zinc-500 hover:text-white p-1 transition-colors">
        <X size={18} />
      </button>
    </div>
    
    {/* Content */}
    <div className="p-4">
      <p className="text-sm text-zinc-400">
        Are you sure you want to proceed?
      </p>
    </div>
    
    {/* Actions */}
    <div className="flex gap-3 p-4 border-t border-zinc-800 bg-zinc-900/30">
      <button onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-bold uppercase tracking-wide rounded-sm transition-colors">
        Cancel
      </button>
      <button onClick={onConfirm} className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-bold uppercase tracking-wide rounded-sm transition-colors flex items-center justify-center gap-2">
        <Trash2 size={14} />
        Delete
      </button>
    </div>
  </div>
</div>
```

### Vanilla CSS

```html
<div class="modal-backdrop active" id="modal">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title">Modal Title</h3>
      <button class="btn-icon modal-close">×</button>
    </div>
    <div class="modal-body">
      <p>Modal content goes here.</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Confirm</button>
    </div>
  </div>
</div>
```

```css
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  opacity: 0;
  visibility: hidden;
  transition: opacity var(--transition-normal), visibility var(--transition-normal);
}
.modal-backdrop.active {
  opacity: 1;
  visibility: visible;
}

.modal {
  width: 100%;
  max-width: 400px;
  background: var(--zinc-950);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transform: scale(0.95);
  transition: transform var(--transition-normal);
}
.modal-backdrop.active .modal {
  transform: scale(1);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--zinc-800);
}

.modal-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--zinc-white);
}

.modal-body {
  padding: 16px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--zinc-800);
  background: rgba(24, 24, 27, 0.3);
}
.modal-footer .btn {
  flex: 1;
}
```

---

## Lightbox with Pan/Zoom

Full-screen image viewer with mouse wheel zoom and drag-to-pan.

### Tailwind/React

```tsx
const [zoom, setZoom] = useState(1);
const [pan, setPan] = useState({ x: 0, y: 0 });
const [isPanning, setIsPanning] = useState(false);

<div 
  className="fixed inset-0 z-50 bg-black flex items-center justify-center overflow-hidden"
  onClick={onClose}
  onWheel={handleWheel}
  onMouseDown={handleMouseDown}
  onMouseMove={handleMouseMove}
  onMouseUp={handleMouseUp}
  onMouseLeave={handleMouseUp}
  style={{ cursor: isPanning ? 'grabbing' : 'grab' }}
>
  <div 
    style={{
      transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
      transition: isPanning ? 'none' : 'transform 0.1s ease-out',
    }}
    onClick={(e) => e.stopPropagation()}
  >
    <img 
      src={imageUrl} 
      className="max-w-[95vw] max-h-[95vh] object-contain select-none"
      draggable={false}
    />
  </div>

  {/* Zoom Controls */}
  <div className="absolute top-4 left-4 flex items-center gap-1 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700 rounded-sm p-1">
    <button onClick={handleZoomOut} className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors">
      <ZoomOut size={16} />
    </button>
    <span className="px-2 text-xs font-mono text-zinc-300 min-w-[50px] text-center">{Math.round(zoom * 100)}%</span>
    <button onClick={handleZoomIn} className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors">
      <ZoomIn size={16} />
    </button>
    <div className="w-px h-4 bg-zinc-700 mx-1"></div>
    <button onClick={handleReset} className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-sm transition-colors">
      <RotateCcw size={16} />
    </button>
  </div>

  {/* Pan hint */}
  {zoom > 1 && (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-sm px-2 py-1 flex items-center gap-1.5">
      <Move size={12} className="text-zinc-500" />
      <span className="text-[10px] text-zinc-500">Drag to pan</span>
    </div>
  )}

  {/* Close */}
  <button onClick={onClose} className="absolute top-4 right-4 p-2 bg-zinc-900/90 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-full border border-zinc-700 transition-colors">
    <X size={24} />
  </button>
</div>
```

---

## Side Drawer

Slide-in panel from the right side.

### Tailwind/React

```tsx
<div className="absolute inset-y-0 right-0 w-80 bg-zinc-950 border-l border-zinc-800 z-50 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
  {/* Header */}
  <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900">
    <h3 className="font-bold text-white text-sm uppercase flex items-center gap-2">
      <History size={14} /> History
    </h3>
    <button onClick={onClose} className="text-zinc-500 hover:text-white">
      <X size={16} />
    </button>
  </div>
  
  {/* Scrollable Content */}
  <div className="flex-1 overflow-y-auto p-4 space-y-4">
    {/* items */}
  </div>
</div>
```

---

## Preset/Variant Menu

Dropdown menu for saving and loading presets/variants.

### Tailwind/React

```tsx
<div className="relative" ref={menuRef}>
  <button 
    onClick={() => setShowMenu(!showMenu)} 
    className={`flex items-center gap-2 px-3 py-1.5 rounded-sm text-xs font-bold uppercase tracking-wide border transition-all ${
      showMenu ? 'bg-white text-black border-white' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700'
    }`}
  >
    <Save size={14} />
    <span>Presets</span>
    <span className={`px-1.5 py-0.5 rounded text-[10px] min-w-[20px] text-center ${
      showMenu ? 'bg-zinc-200 text-black' : 'bg-zinc-800 text-zinc-400'
    }`}>{presets.length}</span>
  </button>
  
  {showMenu && (
    <div className="absolute right-0 top-full mt-2 w-72 bg-zinc-950 border border-zinc-800 rounded-sm shadow-2xl z-50 overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
      {/* Save New */}
      <div className="p-3 border-b border-zinc-900 bg-zinc-900/30">
        <label className="text-[10px] font-bold text-zinc-500 uppercase mb-2 block tracking-wider">Save Current State</label>
        <div className="flex gap-2">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="Variant Name..."
            className="flex-1 bg-black border border-zinc-800 text-xs p-2 rounded-sm outline-none focus:border-white text-white placeholder-zinc-700"
          />
          <button onClick={handleSave} disabled={!newName} className="bg-white text-black p-2 rounded-sm hover:bg-zinc-200 disabled:opacity-50">
            <Plus size={14} />
          </button>
        </div>
      </div>

      {/* List */}
      <div className="max-h-60 overflow-y-auto">
        {presets.map(p => (
          <div key={p.id} onClick={() => handleLoad(p)} className="flex items-center gap-3 p-3 hover:bg-zinc-900 cursor-pointer border-b border-zinc-900/50 last:border-0 group transition-colors">
            <div className="w-8 h-8 bg-zinc-800 rounded-sm overflow-hidden border border-zinc-700/50">
              {p.previewImage ? (
                <img src={p.previewImage} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-600"><Sparkles size={12}/></div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-zinc-300 group-hover:text-white truncate">{p.name}</div>
              <div className="text-[10px] text-zinc-600 font-mono">{new Date(p.createdAt).toLocaleDateString()}</div>
            </div>
            <button onClick={(e) => handleDelete(p.id, e)} className="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-zinc-800 rounded-sm">
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )}
</div>
```
