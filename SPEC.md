# Music Connect - Specification

## Concept & Vision
A sleek, vibrant hub where musicians discover, connect, and collaborate. The platform feels energetic yet professional—like walking into a well-curated music studio where creative connections happen naturally.

## Design Language

**Aesthetic Direction:** Dark, immersive UI with neon accent highlights—reminiscent of a late-night studio session or live music venue.

**Color Palette:**
- Primary: `#1a1a2e` (deep midnight)
- Secondary: `#16213e` (dark navy)
- Accent: `#e94560` (electric pink/red)
- Highlight: `#0f3460` (muted blue)
- Text: `#eaeaea` (soft white)
- Muted: `#a0a0a0` (gray)

**Typography:**
- Headings: Poppins (bold, modern)
- Body: Inter (clean, readable)

**Motion:** Subtle fade-ins on load, hover scale transforms on cards (1.02), smooth color transitions (0.3s).

## Layout & Structure

1. **Hero Section** - Full-width gradient background, bold tagline, search bar for musicians
2. **Featured Musicians** - Grid of musician cards with profile photos, instruments, and genre tags
3. **Browse by Genre** - Horizontal scrollable pills for filtering (Rock, Jazz, Electronic, etc.)
4. **Connect CTA** - Prominent section encouraging sign-up
5. **Footer** - Minimal with links

## Features & Interactions

- Musician cards with hover lift effect
- Genre filter pills (visual feedback on selection)
- Search bar with placeholder text
- "Connect" button on each musician card
- Responsive grid (3 cols desktop, 2 tablet, 1 mobile)

## Component Inventory

**Musician Card:**
- Profile image (circular, 80px)
- Name, instrument, location
- Genre tags (colored pills)
- Connect button (accent color)
- Hover: slight scale, shadow increase

**Genre Pill:**
- Default: outlined
- Active: filled accent

**Search Bar:**
- Large, rounded, dark input with icon

## Technical Approach
- Single HTML file with Bootstrap 5 CDN
- Custom CSS overrides for dark theme
- Vanilla JS for interactions
