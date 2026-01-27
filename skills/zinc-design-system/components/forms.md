# Form Controls

Input components, selects, checkboxes, and other form elements.

## Text Input

### Tailwind/React

```tsx
<div>
  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1.5 block">
    Field Label
  </label>
  <input 
    type="text"
    className="w-full bg-black border border-zinc-800 rounded-sm focus:border-white outline-none text-white text-sm px-3 py-2 placeholder-zinc-700 transition-colors"
    placeholder="Enter value..."
  />
</div>
```

### Vanilla CSS

```html
<div class="form-group">
  <label class="form-label">Field Label</label>
  <input type="text" class="form-input" placeholder="Enter value...">
</div>
```

```css
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--zinc-500);
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--zinc-white);
  background: var(--zinc-black);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}
.form-input::placeholder {
  color: var(--zinc-700);
}
.form-input:focus {
  border-color: var(--zinc-white);
}
```

---

## Textarea

### Tailwind/React

```tsx
<textarea
  className="w-full bg-zinc-950 border border-zinc-800 p-4 rounded-sm outline-none text-sm font-mono leading-relaxed resize-none focus:border-zinc-600 transition-colors text-zinc-300 placeholder-zinc-700 min-h-[120px]"
  placeholder="Enter description..."
/>
```

### Vanilla CSS

```html
<textarea class="form-textarea" rows="4" placeholder="Enter description..."></textarea>
```

```css
.form-textarea {
  width: 100%;
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.6;
  color: var(--zinc-300);
  background: var(--zinc-950);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  outline: none;
  resize: vertical;
  transition: border-color var(--transition-fast);
}
.form-textarea::placeholder {
  color: var(--zinc-700);
}
.form-textarea:focus {
  border-color: var(--zinc-600);
}
```

---

## Number Input

Hide default spinners (invisible on dark backgrounds).

### Vanilla CSS

```css
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
  width: 80px;
  padding: 8px 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  text-align: center;
  color: var(--zinc-white);
  background: var(--zinc-black);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}
```

---

## Select Dropdown

### Tailwind/React

```tsx
<div className="relative">
  <select 
    className="w-full h-10 bg-zinc-900 border border-zinc-800 text-zinc-300 pl-3 pr-8 rounded-sm outline-none text-xs font-bold uppercase appearance-none cursor-pointer hover:border-zinc-600 focus:border-white transition-colors"
  >
    <option value="opt1">Option One</option>
    <option value="opt2">Option Two</option>
  </select>
  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" size={14} />
</div>
```

### Vanilla CSS

```html
<div class="form-select-wrapper">
  <select class="form-select">
    <option>Option One</option>
    <option>Option Two</option>
  </select>
  <svg class="form-select-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M6 9l6 6 6-6"/>
  </svg>
</div>
```

```css
.form-select-wrapper {
  position: relative;
  display: inline-block;
}

.form-select {
  appearance: none;
  padding: 8px 32px 8px 12px;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--zinc-300);
  background: var(--zinc-900);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  cursor: pointer;
  outline: none;
  transition: border-color var(--transition-fast);
}
.form-select:hover {
  border-color: var(--zinc-600);
}
.form-select:focus {
  border-color: var(--zinc-white);
}

.form-select-icon {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--zinc-500);
  pointer-events: none;
}
```

---

## Checkbox

### Tailwind/React

```tsx
<label className="inline-flex items-center gap-2 cursor-pointer text-zinc-400 hover:text-zinc-200 text-sm">
  <input type="checkbox" className="appearance-none w-3.5 h-3.5 bg-black border border-zinc-700 rounded-sm checked:bg-white checked:border-white relative cursor-pointer
    after:content-[''] after:absolute after:hidden checked:after:block after:left-1 after:top-px after:w-1 after:h-2 after:border-black after:border-r-2 after:border-b-2 after:rotate-45" />
  <span>Enable feature</span>
</label>
```

### Vanilla CSS

```html
<label class="checkbox">
  <input type="checkbox" class="checkbox-input">
  <span class="checkbox-box"></span>
  <span class="checkbox-label">Enable feature</span>
</label>
```

```css
.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--zinc-400);
  font-size: 14px;
  transition: color var(--transition-fast);
}
.checkbox:hover {
  color: var(--zinc-200);
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkbox-box {
  position: relative;
  width: 16px;
  height: 16px;
  background: var(--zinc-black);
  border: 1px solid var(--zinc-700);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.checkbox-input:checked + .checkbox-box {
  background: var(--zinc-white);
  border-color: var(--zinc-white);
}
.checkbox-input:checked + .checkbox-box::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 5px;
  width: 4px;
  height: 8px;
  border: solid var(--zinc-black);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
```

---

## Radio Buttons (Pill Style)

### Tailwind/React

```tsx
<div className="flex gap-1">
  <label className="flex items-center justify-center h-8 px-4 bg-zinc-900 border border-zinc-800 rounded-sm text-xs text-zinc-500 cursor-pointer hover:bg-zinc-800 hover:text-zinc-300 has-[:checked]:bg-white has-[:checked]:text-black has-[:checked]:border-white transition-all">
    <input type="radio" name="option" className="hidden" />
    Option A
  </label>
  <label className="flex items-center justify-center h-8 px-4 bg-zinc-900 border border-zinc-800 rounded-sm text-xs text-zinc-500 cursor-pointer hover:bg-zinc-800 hover:text-zinc-300 has-[:checked]:bg-white has-[:checked]:text-black has-[:checked]:border-white transition-all">
    <input type="radio" name="option" className="hidden" />
    Option B
  </label>
</div>
```

### Vanilla CSS

```html
<div class="radio-pills">
  <label class="radio-pill">
    <input type="radio" name="format" class="radio-input" checked>
    <span class="radio-label">Auto</span>
  </label>
  <label class="radio-pill">
    <input type="radio" name="format" class="radio-input">
    <span class="radio-label">JPG</span>
  </label>
</div>
```

```css
.radio-pills {
  display: flex;
  gap: 4px;
}

.radio-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 14px;
  background: var(--zinc-900);
  border: 1px solid var(--zinc-800);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.radio-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.radio-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--zinc-500);
  transition: color var(--transition-fast);
}

.radio-pill:has(.radio-input:checked) {
  background: var(--zinc-white);
  border-color: var(--zinc-white);
}
.radio-pill:has(.radio-input:checked) .radio-label {
  color: var(--zinc-black);
}
```

---

## Toggle Switch

### Tailwind/React

```tsx
<div className="flex items-center gap-3">
  <button 
    onClick={() => setValue(!value)}
    className={`w-10 h-5 rounded-full transition-colors relative ${value ? 'bg-white' : 'bg-zinc-800'}`}
  >
    <span className={`absolute top-1 left-1 bg-black w-3 h-3 rounded-full transition-transform ${value ? 'translate-x-5' : ''}`} />
  </button>
  <span className="text-xs text-zinc-500 font-mono uppercase">{value ? 'ON' : 'OFF'}</span>
</div>
```

### Vanilla CSS

```html
<label class="toggle">
  <input type="checkbox" class="toggle-input">
  <span class="toggle-track"></span>
  <span class="toggle-label">OFF</span>
</label>
```

```css
.toggle {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.toggle-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.toggle-track {
  position: relative;
  width: 40px;
  height: 20px;
  background: var(--zinc-800);
  border-radius: 10px;
  transition: background var(--transition-fast);
}
.toggle-track::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  width: 12px;
  height: 12px;
  background: var(--zinc-black);
  border-radius: 50%;
  transition: transform var(--transition-fast);
}

.toggle-input:checked + .toggle-track {
  background: var(--zinc-white);
}
.toggle-input:checked + .toggle-track::after {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 12px;
  font-family: var(--font-mono);
  text-transform: uppercase;
  color: var(--zinc-500);
}
```

---

## Seed Input with Lock

Specialized input for seed values with lock/unlock toggle.

### Tailwind/React

```tsx
<div className="flex items-center h-10 bg-zinc-900 border border-zinc-800 rounded-sm px-3 hover:border-zinc-600 transition-colors">
  <span className="text-[10px] font-bold text-zinc-500 uppercase mr-2 tracking-wide">SEED</span>
  <div className="h-3 w-[1px] bg-zinc-700 mr-2"></div>
  <input 
    type="number" 
    className="bg-transparent text-xs font-mono text-zinc-300 outline-none flex-1 min-w-0 placeholder-zinc-700 h-full"
    placeholder="Random"
    value={seed || ''}
  />
  <button 
    onClick={() => setLocked(!locked)}
    className={`p-1 ml-2 ${locked ? 'text-white' : 'text-zinc-600 hover:text-zinc-400'}`}
  >
    {locked ? <Lock size={14} /> : <Unlock size={14} />}
  </button>
</div>
```
