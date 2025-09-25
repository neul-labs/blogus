# Blogus UI

Vue.js frontend for the Blogus AI prompt engineering platform.

## Features

- **Modern Vue.js 3** with Composition API and TypeScript
- **SkeletonUI + TailwindCSS** for beautiful, responsive design
- **Pinia** for state management
- **Vue Router** for client-side routing
- **Axios** for API communication
- **Vite** for fast development and building

## Development Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Commands

```bash
# Type checking
npm run type-check

# Linting
npm run lint
```

## Project Structure

```
src/
├── components/        # Reusable Vue components
│   ├── layout/       # Layout components (Header, Sidebar, etc.)
│   └── ui/           # UI components (NavItem, etc.)
├── views/            # Page components
├── stores/           # Pinia stores for state management
├── services/         # API service layer
├── types/            # TypeScript type definitions
├── router/           # Vue Router configuration
└── assets/           # Static assets and global styles
```

## API Integration

The frontend communicates with the Blogus FastAPI backend through the `/api/v1` endpoint. The development server automatically proxies API calls to `http://localhost:8000`.

## State Management

- **Prompt Store** (`stores/prompts.ts`) - Manages prompt analysis, execution, and test generation
- **Template Store** (`stores/templates.ts`) - Handles template CRUD operations and rendering

## Styling

The application uses:
- **TailwindCSS** for utility-first styling
- **SkeletonUI** component library for consistent design
- **Dark mode** support with automatic theme switching
- **Responsive design** for mobile and desktop

## Contributing

1. Follow Vue.js and TypeScript best practices
2. Use the established component structure
3. Maintain type safety throughout
4. Follow the existing naming conventions
5. Update this README when adding new features