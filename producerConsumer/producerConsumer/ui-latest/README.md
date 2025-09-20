# Next.js Production Application with NextAuth

A production-ready Next.js application with NextAuth v5 authentication, protected routes, and a well-organized folder structure.

## Features

- ✅ **NextAuth v5** - Complete authentication system
- ✅ **Protected Routes** - Middleware-based route protection
- ✅ **User Registration** - Custom registration with password hashing
- ✅ **Prisma Database** - SQLite database with proper schema
- ✅ **TypeScript** - Full type safety
- ✅ **Tailwind CSS** - Utility-first styling
- ✅ **Production Structure** - Organized folder structure

## Folder Structure

```
src/
├── app/                          # Next.js 13+ App Router
│   ├── (auth)/                   # Authentication routes group
│   │   ├── login/                # Login page
│   │   ├── register/             # Registration page
│   │   └── layout.tsx            # Auth layout (redirects if authenticated)
│   ├── (protected)/              # Protected routes group
│   │   ├── history/              # History page (default landing page)
│   │   ├── profile/              # Profile page
│   │   └── layout.tsx            # Protected layout (requires auth)
│   ├── api/                      # API routes
│   │   └── auth/                 # Authentication API
│   │       ├── [...nextauth]/    # NextAuth handler
│   │       └── register/         # Registration API
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout with providers
│   └── page.tsx                  # Home page
├── components/                   # Reusable components
│   ├── auth/                     # Authentication components
│   │   ├── AuthProvider.tsx      # NextAuth session provider
│   │   ├── LoginForm.tsx         # Login form
│   │   └── RegisterForm.tsx      # Registration form
│   ├── layout/                   # Layout components
│   │   └── Navbar.tsx            # Navigation bar
│   └── ui/                       # UI components
│       ├── Button.tsx            # Reusable button
│       └── Loading.tsx           # Loading component
├── hooks/                        # Custom React hooks
│   └── useAuth.ts                # Authentication hook
├── lib/                          # Library configurations
│   ├── auth.ts                   # NextAuth configuration
│   └── prisma.ts                 # Prisma client
├── types/                        # TypeScript type definitions
│   └── next-auth.d.ts            # NextAuth type extensions
└── utils/                        # Utility functions
    └── index.ts                  # Common utilities
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   Create a `.env.local` file in the root directory:
   ```env
   DATABASE_URL="file:./dev.db"
   NEXTAUTH_URL="http://localhost:3000"
   NEXTAUTH_SECRET="your-secret-key-here-change-this-in-production"
   ```

3. **Set up the database:**
   ```bash
   npx prisma generate
   npx prisma db push
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Authentication Flow

### Routes

- **Public Routes:** `/`, `/login`, `/register`
- **Protected Routes:** `/history`, `/profile`
- **API Routes:** `/api/auth/*`, `/api/auth/register`

### User Registration

1. Users can register at `/register`
2. Passwords are hashed using bcrypt
3. User data is stored in the database
4. Automatic redirect to login page

### User Login

1. Users can login at `/login`
2. Credentials are validated against the database
3. JWT tokens are issued for session management
4. Automatic redirect to history

### Route Protection

- **Middleware:** Automatically redirects unauthenticated users
- **Layout Protection:** Server-side authentication checks
- **Client Protection:** React hooks for conditional rendering

## Database Schema

The application uses Prisma with SQLite for simplicity. The schema includes:

- **Users:** Store user information with roles
- **Accounts:** OAuth account linking
- **Sessions:** User session management
- **Verification Tokens:** Email verification support

## Customization

### Adding New Protected Routes

1. Create route under `src/app/(protected)/`
2. The layout will automatically protect it
3. Access user session via `auth()` function

### Adding New Authentication Providers

1. Install the provider package
2. Add configuration to `src/lib/auth.ts`
3. Add environment variables

### Styling

- Uses Tailwind CSS for styling
- Custom components in `src/components/ui/`
- Utility functions in `src/utils/`

## Production Deployment

### Environment Variables

Update `.env.local` for production:
```env
DATABASE_URL="your-production-database-url"
NEXTAUTH_URL="https://yourdomain.com"
NEXTAUTH_SECRET="a-secure-random-string"
```

### Database

For production, consider switching to:
- PostgreSQL
- MySQL  
- MongoDB

Update `prisma/schema.prisma` accordingly.

### Build and Deploy

```bash
npm run build
npm start
```

## File Conventions

- **Pages:** Use `page.tsx` for route pages
- **Layouts:** Use `layout.tsx` for shared layouts
- **Components:** PascalCase, one component per file
- **Hooks:** `use` prefix, camelCase
- **Utils:** camelCase functions
- **Types:** PascalCase interfaces/types

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based sessions
- ✅ CSRF protection
- ✅ Environment variable security
- ✅ Route-level protection
- ✅ Input validation with Zod

## Contributing

1. Follow the established folder structure
2. Use TypeScript for all new files
3. Follow the naming conventions
4. Add proper error handling
5. Include type definitions

## License

This project is open source and available under the [MIT License](LICENSE).
