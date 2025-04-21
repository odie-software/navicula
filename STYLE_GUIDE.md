We follow standard TypeScript best practices (strong typing, interfaces, etc.) combined with Prettier (formatting) and ESLint (linting). For documentation, we use **JSDoc/TSDoc** comment blocks (`/** ... */`).


### JSDoc/TSDoc Comments

JSDoc provides a standardized way to document JavaScript and TypeScript code. TSDoc is a specification built upon JSDoc specifically for TypeScript, enabling richer type information and compatibility with tools like TypeDoc.

**What to Document:**

*   Every exported function, class, type, interface, and constant.
*   Component props, emitted events, and slots (using relevant tags).
*   Complex internal logic or functions.
*   Vuex/Pinia store modules, actions, mutations, and getters.
*   Composable functions (hooks).

**Structure:**

*   Start with `/**` and end with `*/`.
*   A concise summary description.
*   Optional detailed description.
*   Use JSDoc tags (e.g., `@param`, `@returns`, `@throws`, `@deprecated`, `@example`, `@see`).
*   Use TypeScript types directly in your code signatures. JSDoc often infers types from TS, but you can be explicit with ` @param {TypeName} name - Description`.
*   For Vue/Nuxt components, use tags like `@prop`, `@emits`, `@slot`.


**Common Types:** `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`.

**Example:**

```
feat(api): add endpoint for fetching user profiles

Implement GET /api/v1/profiles/:id to retrieve user data.
Includes validation and basic serialization.

Fixes #42
```

## Tooling

We leverage tools to automate style enforcement:

*   **Python:**
    *   `black`: Uncompromising code formatter.
    *   `ruff` or `flake8` (with plugins like `flake8-docstrings`): Linter for style and errors (including basic docstring checks).
    *   `isort`: Sorts imports automatically.
*   **TypeScript:**
    *   `prettier`: Code formatter.
    *   `eslint` (with plugins like `@typescript-eslint/eslint-plugin`, `eslint-plugin-vue`): Linter for style, errors, and best practices.

Configure these tools in your projects (e.g., `pyproject.toml`, `.eslintrc.js`, `.prettierrc.js`) and integrate them with pre-commit hooks and CI pipelines.