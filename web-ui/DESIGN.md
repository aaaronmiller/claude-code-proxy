# Claude Code Proxy Web Dashboard - Design Plan

## Project Overview

**Project**: Claude Code Proxy Web Dashboard Upgrade  
**Type**: AI/ML Platform Dashboard (Aurora UI, Motion-Driven)  
**Goal**: Comprehensive upgrade with feature parity to TUI, enhanced metrics, 3 dark mode themes, and generative imagery

---

## 1. Product Classification

| Dimension | Selection | Rationale |
|-----------|-----------|-----------|
| **Product Type** | AI/ML Platform | Proxy for LLM routing |
| **Style Intent** | Aurora UI, Motion-Driven | Gradient primaries, dark surfaces, animated elements |
| **Audience** | Developer/DevOps | Technical users who appreciate data density |
| **Primary Mode** | Dark (with light option) | Technical dashboard convention |

---

## 2. Color Palettes

### Theme 1: "Midnight Aurora" (Default Dark)

**Primary Hue**: 230 (Indigo-Blue)  
**Accent Hue**: 170 (Teal) - Split-complementary for sophisticated contrast

| Token | Lightness | Usage |
|-------|-----------|-------|
| `--base-100` | 6% | Page background |
| `--base-200` | 11% | Card/surface |
| `--base-300` | 17% | Elevated surfaces |
| `--primary-muted` | S:20%, L:35% | Primary backgrounds |
| `--primary-default` | S:70%, L:55% | Primary actions |
| `--primary-vivid` | S:85%, L:60% | Hover/focus |
| `--accent-subtle` | S:40%, L:45% | Badges |
| `--accent-default` | S:75%, L:55% | Accent elements |
| `--accent-bold` | S:90%, L:60% | Emphasis, charts |
| `--text-primary` | 90% | Main text |
| `--text-secondary` | 60% | Secondary text |
| `--glow-color` | H:170, S:80% | Neon glow effects |

### Theme 2: "Ember Console"

**Primary Hue**: 25 (Warm Orange)  
**Accent Hue**: 200 (Cool Blue) - Complementary for high contrast

| Token | Lightness | Usage |
|-------|-----------|-------|
| `--base-100` | 8% | Page background |
| `--base-200` | 13% | Card/surface |
| `--base-300` | 18% | Elevated surfaces |
| `--primary-muted` | S:25%, L:38% | Primary backgrounds |
| `--primary-default` | S:75%, L:52% | Primary actions |
| `--primary-vivid` | S:90%, L:58% | Hover/focus |
| `--accent-subtle` | S:35%, L:42% | Badges |
| `--accent-default` | S:70%, L:50% | Accent elements |
| `--accent-bold` | S:85%, L:55% | Emphasis, charts |
| `--glow-color` | H:25, S:90% | Warm glow effects |

### Theme 3: "Synthwave Minimal"

**Primary Hue**: 280 (Violet-Purple, shifted)  
**Accent Hue**: 320 (Magenta-Pink) - Triadic relationship

| Token | Lightness | Usage |
|-------|-----------|-------|
| `--base-100` | 5% | Page background |
| `--base-200` | 10% | Card/surface |
| `--base-300` | 15% | Elevated surfaces |
| `--primary-muted` | S:30%, L:32% | Primary backgrounds |
| `--primary-default` | S:65%, L:50% | Primary actions |
| `--primary-vivid` | S:80%, L:55% | Hover/focus |
| `--accent-subtle` | S:50%, L:45% | Badges |
| `--accent-default` | S:75%, L:52% | Accent elements |
| `--accent-bold` | S:90%, L:58% | Emphasis, charts |
| `--glow-color` | H:320, S:85% | Neon magenta glow |

---

## 3. Typography

**Display Font**: "Outfit" (Google Fonts) - Geometric sans, modern tech feel  
**Body Font**: "IBM Plex Sans" (Google Fonts) - Technical, readable  
**Mono Font**: "IBM Plex Mono" - For code/stats

### Type Scale
- Display: 48px/56px, weight 700
- H1: 36px/44px, weight 600
- H2: 28px/36px, weight 600
- H3: 22px/28px, weight 500
- Body: 15px/24px, weight 400
- Small: 13px/20px, weight 400
- Mono: 14px/22px, weight 400

---

## 4. Layout System

### Bento Grid Dashboard

```
+------------------+------------------+------------------+
|                  |                  |                  |
|   Stats Card 1   |   Stats Card 2   |   Stats Card 3   |
|   (1 col)       |   (1 col)        |   (1 col)        |
+------------------+------------------+------------------+
|                                               |      |
|           Main Chart Area (2 col)            | Side |
|                                               | bar  |
+------------------+------------------+--------+------+
|                  |                  |                  |
|   Table/Data     |   Activity       |   Alerts         |
|   (1 col)       |   Feed (1 col)   |   (1 col)        |
+------------------+------------------+------------------+
```

### Responsive Breakpoints
- Mobile: < 640px (single column)
- Tablet: 640-1024px (2 columns)
- Desktop: > 1024px (full bento grid)

---

## 5. Component Specifications

### 5-State Button System

Every button follows this pattern:
1. **Default**: Base style with subtle shadow
2. **Hover**: Lift (translateY -2px), glow expansion, color shift
3. **Active**: Press down (translateY 1px, scale 0.98), shadow reduction
4. **Focus**: 2px accent outline, 3px offset
5. **Disabled**: 50% opacity, no transforms

```css
/* Primary Button */
.btn-primary {
  transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.15s ease,
              background-color 0.15s ease;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--glow-color);
}
.btn-primary:active {
  transform: translateY(1px) scale(0.98);
}
```

### Card Components

- Border: `1px solid rgba(255,255,255,0.06)`
- Background: `linear-gradient(135deg, var(--base-200), var(--base-100))`
- Padding: 24px
- Border-radius: 16px
- Hover: Subtle glow + lift

### Status Indicators

- **Active**: Green dot with glow `shadow-[0_0_8px_theme(colors.emerald.500)]`
- **Pending**: Amber dot with pulse animation
- **Error**: Red dot, no glow
- **Inactive**: Gray dot, no glow

---

## 6. Data Visualization

### Chart Aesthetic: "Neon" (Default)

- Line stroke: 2.5px, accent color
- Glow filter applied to lines
- Area: gradient fill (accent 50% → transparent)
- Grid: dashed, 8% opacity
- Labels: Mono font, muted color
- Tooltip: Glassmorphic with blur

### Table Styling

- No vertical borders
- Horizontal separators: `border-b border-white/10`
- Sticky header with backdrop blur
- Row hover: `bg-accent/8`
- Status column: Geometric indicators (not text)

---

## 7. Animations

### Micro-interactions

| Element | Animation | Duration | Easing |
|---------|----------|----------|--------|
| Button hover | Lift + glow | 150ms | Bouncy |
| Card hover | Lift + shadow | 200ms | Smooth out |
| Tab switch | Slide indicator | 250ms | Smooth out |
| Modal open | Fade + scale | 200ms | Decelerate |
| Toast appear | Slide + fade | 150ms | Bouncy |

### Scroll Animations

- Staggered reveal: 80ms delay between items
- Counter animation: 1500ms, ease-out cubic
- Progress bar: 100ms, linear

---

## 8. Nano Banana Integration

### Image Roles

1. **Hero Background**: Atmospheric generative texture (dithered)
2. **Section Dividers**: Geometric patterns
3. **Card Accents**: Subtle texture overlays
4. **Loading States**: Animated generative placeholders

### Three-Layer Composition

```
Layer 1: Solid color base (var(--base-100))
Layer 2: Nano Banana dithered, 0.1 opacity, blend: luminosity
Layer 3: Nano Banana fine noise, 0.05 opacity, blend: overlay
Layer 4: Content
```

---

## 9. Feature Parity: TUI → Web

| TUI Module | Web Equivalent | Priority |
|------------|----------------|----------|
| Activity Feed | Real-time feed panel | High |
| Performance Monitor | Live metrics + charts | High |
| Analytics Panel | Cost/usage analytics | High |
| Request Waterfall | Request timeline view | Medium |
| Routing Visualizer | Model routing diagram | Medium |

---

## 10. Implementation Priority

### Phase 1: Foundation
1. CSS custom properties setup (3 themes)
2. Theme selector component
3. Base layout with bento grid

### Phase 2: Components
4. Button 5-state system
5. Card components with animations
6. Status indicators
7. Table styling

### Phase 3: Visualization
8. LayerChart integration
9. Real-time data updates
10. Sparklines for metrics

### Phase 4: Polish
11. Nano Banana imagery
12. Page transitions
13. Micro-animations throughout

---

## 11. Acceptance Criteria

- [ ] 3 dark mode themes selectable via UI
- [ ] Theme persists in localStorage
- [ ] All buttons have visible 5-state feedback
- [ ] Cards have hover lift + glow
- [ ] Charts use gradient fills + glow effects
- [ ] Tables have geometric status indicators
- [ ] Real-time data updates smoothly
- [ ] Responsive on mobile/tablet/desktop
- [ ] prefers-reduced-motion respected
- [ ] All interactive elements have cursor-pointer
