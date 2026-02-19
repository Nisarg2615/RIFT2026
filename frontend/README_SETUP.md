# PharmaGuard AI - Premium Frontend Setup

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
```

## 📦 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Animation library
- **Lucide React** - Icon library
- **clsx & tailwind-merge** - Utility functions

## 🎨 Design Features

### Visual Effects
- ✅ Animated DNA Helix background (SVG + Framer Motion)
- ✅ Floating nucleotide particles (A, T, C, G)
- ✅ Genome scanning animation during file upload
- ✅ AI glow pulse analyze button
- ✅ Data decoding animations on results load
- ✅ Glassmorphism cards with backdrop blur
- ✅ Biotech grid background patterns

### Components
- **HeroSection** - Animated landing with DNA helix
- **UploadSection** - Drag-drop VCF upload with genome scan
- **SummaryDashboard** - Risk overview cards
- **DrugTable** - Interactive risk assessment table
- **GenePanel** - Gene analysis cards
- **DetailedReports** - Expandable detailed reports
- **DownloadSection** - JSON export functionality

## 🎯 Key Features

1. **Premium UI/UX**
   - Clinical-grade trust aesthetics
   - Biotech laboratory feel
   - AI intelligence visual language
   - Futuristic but minimal design

2. **Animations**
   - Smooth page transitions
   - Component entrance animations
   - Hover effects and micro-interactions
   - Loading states with DNA animations

3. **Responsive Design**
   - Mobile-first approach
   - Adaptive layouts
   - Touch-friendly interactions

## 🔧 Configuration

### Tailwind Config
Custom colors and animations are defined in `tailwind.config.js`:
- DNA theme colors (cyan, purple, pink, teal)
- Custom animations (dna-rotate, pulse-glow, float, scan)
- Glassmorphism utilities

### Vite Config
- React plugin configured
- Path aliases (@/ for src/)
- Dev server on port 3000

## 📝 Notes

- All backend API calls use `/api/analyze` endpoint
- FormData format: `vcf_file` (File) and `drugs` (comma-separated string)
- Results are expected as an array of drug analysis objects
- All existing backend fields are preserved in the UI

## 🎨 Color Palette

- **DNA Cyan**: `#00D4FF` - Primary accent
- **DNA Purple**: `#8B5CF6` - Secondary accent
- **DNA Pink**: `#EC4899` - Tertiary accent
- **DNA Teal**: `#14B8A6` - Success states
- **DNA Green**: `#10B981` - Safe states

## 🚀 Production Build

The production build optimizes:
- Code splitting
- Asset optimization
- Tree shaking
- Minification

Build output is in `frontend/dist/`
