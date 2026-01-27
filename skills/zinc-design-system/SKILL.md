---
name: zinc-design-system
description: Dark, technical design system built on pure black with zinc accents. Use when building web components, pages, modals, dashboards, or any dark-themed web application. Works with Tailwind CSS or plain CSS/HTML/JS. Provides color tokens, typography, component patterns, layout conventions, and animation standards for a cohesive, professional UI.
---

# Zinc Design System

A dark, technical aesthetic inspired by professional tools like Figma, Linear, and code editors - minimal, high-contrast, and sophisticated.

**Keywords**: dark theme, zinc colors, Tailwind CSS, vanilla CSS, HTML, JavaScript, dark mode, IDE aesthetic, modals, forms, cards, buttons, dashboard

## Component Reference

Individual component documentation:

| Component | File |
|-----------|------|
| Buttons | [components/buttons.md](components/buttons.md) |
| Form Controls | [components/forms.md](components/forms.md) |
| Cards & Containers | [components/cards.md](components/cards.md) |
| Modals & Overlays | [components/modals.md](components/modals.md) |
| Navigation | [components/navigation.md](components/navigation.md) |
| Feedback & Status | [components/feedback.md](components/feedback.md) |
| Layout | [components/layout.md](components/layout.md) |
| Advanced Components | [components/advanced.md](components/advanced.md) |

## Design Philosophy

The Zinc system embodies **technical precision** with **creative purpose**:

- **Pure Black Foundation**: `#000000` base creates depth and makes content pop
- **High Contrast**: White primary actions create clear visual hierarchy
- **Technical Aesthetic**: Monospace for data, uppercase labels, subtle grid patterns
- **Restrained Motion**: Smooth transitions that feel responsive, not decorative

**Intentionality over intensity** - every element serves a purpose. No decorative flourishes, no soft shadows, no rounded corners beyond 2px.

## Color Tokens

### CSS Custom Properties

```css
:root {
  /* Core palette */
  --zinc-black: #000000;
  --zinc-950: #09090b;
  --zinc-900: #18181b;
  --zinc-800: #27272a;
  --zinc-700: #3f3f46;
  --zinc-600: #52525b;
  --zinc-500: #71717a;
  --zinc-400: #a1a1aa;
  --zinc-300: #d4d4d8;
  --zinc-200: #e4e4e7;
  --zinc-100: #f4f4f5;
  --zinc-white: #ffffff;
  
  /* Semantic tokens */
  --color-bg: var(--zinc-black);
  --color-surface: var(--zinc-900);
  --color-surface-elevated: var(--zinc-950);
  --color-border: var(--zinc-800);
  --color-border-hover: var(--zinc-600);
  --color-text-primary: var(--zinc-200);
  --color-text-secondary: var(--zinc-500);
  --color-text-muted: var(--zinc-600);
  
  /* Accent colors */
  --color-danger: #ef4444;
  --color-danger-bg: #dc2626;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  
  /* Spacing & Transitions */
  --radius-sm: 2px;
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
}
```

### Color Reference Table

| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| Black | `#000000` | `black` | Page backgrounds, inputs |
| Zinc 950 | `#09090b` | `zinc-950` | Headers, footers, elevated surfaces |
| Zinc 900 | `#18181b` | `zinc-900` | Cards, panels, secondary surfaces |
| Zinc 800 | `#27272a` | `zinc-800` | Borders, dividers |
| Zinc 700 | `#3f3f46` | `zinc-700` | Scrollbar thumbs, active borders |
| Zinc 600 | `#52525b` | `zinc-600` | Hover borders |
| Zinc 500 | `#71717a` | `zinc-500` | Secondary text, labels |
| Zinc 400 | `#a1a1aa` | `zinc-400` | Inactive icons, muted UI |
| Zinc 200 | `#e4e4e7` | `zinc-200` | Primary text |
| White | `#ffffff` | `white` | Primary buttons, focus states |

### Semantic Colors

| Purpose | Light Element | Dark Element |
|---------|--------------|--------------|
| Primary Action | White bg / Black text | Zinc-900 bg / Zinc-800 border |
| Danger | `#ef4444` text | `#dc2626` background |
| Success | `#22c55e` | — |
| Warning | `#f59e0b` | 10% opacity background |

## Typography

### Font Stack

```css
/* Body - Clean, modern sans-serif */
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;

/* Code/Data - Technical monospace */
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale

| Element | Size | Weight | Style |
|---------|------|--------|-------|
| Page Title | 20px (1.25rem) | 700 | — |
| Section Header | 14px (0.875rem) | 700 | uppercase, letter-spacing: 0.05em |
| Field Label | 10px (0.625rem) | 700 | uppercase, letter-spacing: 0.1em |
| Body Text | 14px (0.875rem) | 400 | — |
| Secondary Text | 12px (0.75rem) | 400 | color: zinc-500 |
| Monospace Data | 12px (0.75rem) | 400 | font-family: mono |

### Typography Rules

- Labels are ALWAYS uppercase with letter-spacing
- Seeds, IDs, timestamps use monospace font
- Never use the sans font for numerical/technical data

## Icons

For React projects, use **lucide-react**. For vanilla JS, use **Lucide** or inline SVGs.

| Context | Size |
|---------|------|
| Inline/labels | 12px - 14px |
| Buttons | 16px |
| Headers | 18px |
| Empty states | 24px - 48px |

## Animation Standards

### CSS Transitions

```css
/* Standard transition */
transition: all 150ms ease;
transition: color 150ms ease, background-color 150ms ease;

/* Slower for transforms */
transition: transform 300ms ease;
```

### Keyframe Animations

```css
/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide in from top */
@keyframes slideInFromTop {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Spin (loading) */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Progress bar (indeterminate) */
@keyframes progress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

### Tailwind Animation Classes

```html
class="animate-in fade-in zoom-in-95 duration-200"
class="animate-in fade-in slide-in-from-top-1 duration-200"
class="animate-in slide-in-from-right duration-300"
class="active:scale-[0.99]"
```

## Quick Reference

### Button Classes (Tailwind)

```tsx
// Primary
"bg-white hover:bg-zinc-200 text-black px-4 py-2 rounded-sm text-xs font-bold uppercase tracking-wide transition-colors"

// Secondary
"bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 px-3 py-2 rounded-sm text-xs font-bold uppercase tracking-wide transition-all"

// Danger
"bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-sm text-xs font-bold uppercase tracking-wide transition-colors"

// Icon
"p-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-sm border border-zinc-800 transition-colors"
```

### Input Classes (Tailwind)

```tsx
// Text input
"w-full bg-black border border-zinc-800 rounded-sm focus:border-white outline-none text-white text-sm px-3 py-2 placeholder-zinc-700 transition-colors"

// Textarea
"w-full bg-zinc-950 border border-zinc-800 p-4 rounded-sm text-sm font-mono text-zinc-300 focus:border-zinc-600 outline-none resize-none placeholder-zinc-700"

// Select
"bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-2 rounded-sm text-xs font-bold uppercase appearance-none cursor-pointer hover:border-zinc-600 focus:border-white outline-none transition-colors"
```

### Card Classes (Tailwind)

```tsx
// Basic
"bg-zinc-900 border border-zinc-800 rounded-sm p-4 hover:border-zinc-600 transition-colors"

// Glass
"bg-zinc-900/50 border border-zinc-800 rounded-sm p-6 backdrop-blur-sm shadow-2xl"

// Empty state
"border border-dashed border-zinc-800 rounded-sm py-20 text-center"
```

## Design Rules

### ✅ Always

- Use 2px border-radius (`rounded-sm` / `border-radius: 2px`)
- Add hover states to interactive elements
- Use zinc-800 (`#27272a`) for borders
- Apply transitions to interactive elements
- Use uppercase + letter-spacing for labels
- Use monospace font for seeds, IDs, timestamps

### ❌ Never

- Use large border-radius (except avatars/badges)
- Use colors outside zinc palette (except red for danger)
- Skip hover states on buttons/links
- Use decorative box-shadows (only for elevated modals)
- Mix font families inappropriately
