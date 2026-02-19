# PharmaGuard AI - Component Architecture

## 🏗️ Component Structure

### Core Layout
- **App.jsx** - Main application component with state management
- **main.jsx** - React entry point
- **index.css** - Global styles with Tailwind directives

### Background Components (`components/backgrounds/`)
- **DNAHelix.jsx** - Animated SVG DNA double helix
- **NucleotideParticles.jsx** - Floating A, T, C, G particles
- **GenomeScanAnimation.jsx** - Scanning line animation for file upload

### UI Components (`components/ui/`)
- **GlassCard.jsx** - Reusable glassmorphism card wrapper
- **AIGlowButton.jsx** - Animated AI-powered button with glow effects

### Main Components
- **Header.jsx** - Navigation header with logo and menu
- **HeroSection.jsx** - Landing page with DNA animations
- **UploadSection.jsx** - VCF file upload with drag-drop and drug selection
- **LoadingState.jsx** - Animated loading indicator
- **ErrorMessage.jsx** - Error display component
- **SummaryDashboard.jsx** - Risk overview dashboard
- **DrugTable.jsx** - Drug risk assessment table
- **GenePanel.jsx** - Gene analysis cards
- **DetailedReports.jsx** - Expandable detailed drug reports
- **DownloadSection.jsx** - JSON export functionality

### Utilities (`lib/`)
- **utils.js** - Helper functions (cn for className merging)

## 🎨 Design System

### Color Palette
- Primary: DNA Cyan (`#00D4FF`)
- Secondary: DNA Purple (`#8B5CF6`)
- Accent: DNA Pink (`#EC4899`)
- Success: DNA Green (`#10B981`)
- Background: Slate 950/900

### Typography
- Font: Inter (sans-serif)
- Code: JetBrains Mono (monospace)
- Hierarchy: Clear size and weight system

### Animations
- Entrance: Fade + slide up
- Hover: Scale + lift
- Loading: Rotate + pulse
- DNA: Continuous rotation

## 🔄 Data Flow

1. **Upload** → User selects VCF file and drugs
2. **Submit** → FormData sent to `/api/analyze`
3. **Loading** → Animated loading state
4. **Results** → Display dashboard, table, panels, reports
5. **Export** → Download or copy JSON

## 📦 Props & State

### App State
- `selectedFile` - Uploaded VCF file
- `selectedDrugs` - Array of selected drug names
- `results` - Analysis results array
- `loading` - Loading state
- `error` - Error message

### Component Props
All components receive only necessary props, maintaining clean separation of concerns.

## 🎯 Key Features Implemented

✅ Animated DNA Helix background
✅ Floating nucleotide particles
✅ Genome scanning animation
✅ AI glow pulse button
✅ Glassmorphism effects
✅ Smooth page transitions
✅ Responsive design
✅ All backend fields preserved
✅ Premium clinical aesthetics
