# Tech Stack, Style Guide

## TypeScript

Type-driven development, using the following stack:

- **TypeScript** (strict mode)
- **Next.js** & **React**
- **Tailwind CSS**
- **tRPC & Valibot**
- **Zustand**
- **Headless UI**
- **Centralized Logging** (e.g., Pino)
- **pnpm** & **ESLint**
- **Mermaid Entity Diagrams** (for subsystem documentation)

### 1. **Naming Conventions**

#### 1.1 General Philosophy

- **Clarity Over Brevity** – Names should reflect purpose or domain context.
- **No Vague Placeholders** – Avoid “foo”, “stuff”, “util”.
- **Domain-Aligned** – E.g., `billingCycle`, `checkoutFlow`.

#### 1.2 Variables & Functions

- **Camel Case** – e.g., `isLoading`, `handleOrderSubmit`.
- **Boolean Prefixes** – `is`, `has`, `can`.
- **Event Handlers** – `handleClick`, `onUserSelect`.
- **Async** – Optionally append `Async` (e.g., `fetchUserDataAsync`).

#### 1.3 Files & Directories

- **All Lowercase, Dashes** – `components/user-profile`, `lib/validate-user`.
- **Component Files** – match PascalCase if the component is the sole export (`UserProfile.tsx`).
- **Shared Hooks** – e.g. `useOrderStatus.ts`, `useUserData.ts`.

#### 1.4 Types

- **Interfaces** – for object shapes.
- **Discriminated Unions** – for complex states/results.
- **Result Types** – `OkResult<T>` or `ErrResult<E>` for safe success/failure flows.

### 2. **Type-Driven Code**

- **`strict`** in `tsconfig.json`.
- **Minimize `any`** using robust type definitions.
- **Discriminated Unions** for multi-step flows (onboarding, checkout, etc.).
- **Valibot** for runtime validation of external data and requests.

### 3. **Client and Server Boundaries**

1. **Server-Side Secrets & Logic**

   - Keep ENV variables, tokens, DB connections strictly on the server.
   - Never expose them in `"use client"` modules.

2. **Server Components First**

   - In Next.js, default to server components.
   - Use `"use client"` only when direct interactivity or browser APIs are required.

3. **Sensitive Functions**
   - Database queries, secret access, or privileged operations must reside in server modules/route handlers.
   - Use **tRPC** for typed, secure server calls—never leak secrets to the client.

### 4. **Centralized Logging & Error Handling**

1. **Single Logging Interface**
   - One logger (e.g., Pino) with consistent levels/formats.
2. **Structured Logging**
   - Include relevant metadata, omit sensitive data.
3. **Error Handling**
   - Use typed `ErrResult<E>` instead of throwing unhandled exceptions.
4. **Client vs. Server Logs**
   - **Server**: Main logs (debugging, security, analytics).
   - **Client**: Minimal logs, no confidential info.

### 5. **Centralized Environment Variable Validation**

- **Single File** (e.g., `env.ts`) validating required vars at startup.
- **Fail Fast** on missing or invalid variables.
- **Export Sanitized Values** for use across the codebase.

```ts
// env.ts
import { object, string, minLength } from "valibot";

const envSchema = object({
  DATABASE_URL: string([minLength(1, "DATABASE_URL must not be empty")]),
  LOG_LEVEL: string(),
  // ...
});

const parsed = envSchema.parse(process.env);

export const ENV = {
  DATABASE_URL: parsed.DATABASE_URL,
  LOG_LEVEL: parsed.LOG_LEVEL,
};
```

### 6. **Minimal Bloat**

- Evaluate dependencies carefully.
- Favor smaller, focused libraries (e.g., tRPC, Valibot).
- Keep client bundles lean (Next.js code splitting, SSR).

---

### 7. **UI Guidelines & State Management**

#### 7.1 Headless & Composable UI

- **Headless UI** or custom logic-based components with **Tailwind** for styling.
- Maintain semantic, accessible markup (ARIA labels, roles, keyboard navigation).

#### 7.2 Zustand for State (When Needed)

- Keep small, domain-scoped Zustand stores.
- Rely on server components & tRPC for most data operations.

## Python

### 1. **Code Formatting & Structure**

- **Black** for consistent code formatting.
- **PyScaffold** for project structure and setup.
- **Pipenv** for dependency management and virtual environments.

### 2. **Command Line Interfaces**

- **Click** for building intuitive, well-documented CLIs.
- Consistent command structure with proper help documentation.

### 3. **Logging**

- Centralized logging system using **Rich**.
- Colorful, structured console output for better debugging.
- Consistent log levels and formatting across the application.

### 4. **API Development**

- **FastAPI** for high-performance API endpoints.
- Automatic OpenAPI documentation generation.
- Async support for efficient request handling.

### 5. **Data Validation**

- **Pydantic** for data validation, especially for sensitive information.
- Schema-based validation for request and response models.
